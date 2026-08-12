from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_models import (
    BookResilienceSliceV1,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    REGIME_METHOD,
    Lot43ValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/schemas/book_resilience_state_v1.schema.json"


def _slice(
    *,
    status: str,
    events: int,
    recovered: int,
    shifted: int,
    expired: int,
    pending: int,
    mean_fraction: Decimal | None,
    mean_time: Decimal | None,
) -> BookResilienceSliceV1:
    return BookResilienceSliceV1(
        "BID",
        10_000,
        "QUIET",
        REGIME_METHOD,
        events,
        recovered,
        shifted,
        expired,
        pending,
        mean_fraction,
        mean_time,
        status,
        ("LOT43_SEMANTIC_CONSISTENCY_TEST",),
        "0" * 64,
    )


@pytest.mark.parametrize(
    (
        "status",
        "events",
        "recovered",
        "shifted",
        "expired",
        "pending",
        "mean_fraction",
        "mean_time",
    ),
    (
        ("NO_EVENTS", 0, 0, 0, 0, 0, None, None),
        ("RESILIENT", 1, 1, 0, 0, 0, Decimal("0.5"), Decimal("10000")),
        ("FRAGILE", 1, 0, 0, 1, 0, Decimal("0"), None),
        ("SHIFTED", 1, 0, 1, 0, 0, Decimal("0"), None),
        ("PENDING", 1, 0, 0, 0, 1, Decimal("0"), None),
        ("PARTIAL", 2, 1, 0, 1, 0, Decimal("0.25"), Decimal("10000")),
    ),
)
def test_resilience_slice_accepts_only_the_status_derived_from_counts(
    status: str,
    events: int,
    recovered: int,
    shifted: int,
    expired: int,
    pending: int,
    mean_fraction: Decimal | None,
    mean_time: Decimal | None,
) -> None:
    result = _slice(
        status=status,
        events=events,
        recovered=recovered,
        shifted=shifted,
        expired=expired,
        pending=pending,
        mean_fraction=mean_fraction,
        mean_time=mean_time,
    )
    assert result.resilience_status == status


@pytest.mark.parametrize(
    (
        "wrong_status",
        "events",
        "recovered",
        "shifted",
        "expired",
        "pending",
        "mean_fraction",
        "mean_time",
    ),
    (
        ("PARTIAL", 0, 0, 0, 0, 0, None, None),
        ("NO_EVENTS", 1, 1, 0, 0, 0, Decimal("0.5"), Decimal("10000")),
        ("NO_EVENTS", 1, 0, 0, 1, 0, Decimal("0"), None),
        ("FRAGILE", 1, 0, 1, 0, 0, Decimal("0"), None),
        ("SHIFTED", 1, 0, 0, 0, 1, Decimal("0"), None),
        ("RESILIENT", 2, 1, 0, 1, 0, Decimal("0.25"), Decimal("10000")),
    ),
)
def test_resilience_slice_rejects_status_count_mismatches(
    wrong_status: str,
    events: int,
    recovered: int,
    shifted: int,
    expired: int,
    pending: int,
    mean_fraction: Decimal | None,
    mean_time: Decimal | None,
) -> None:
    with pytest.raises(Lot43ValidationError, match="resilience status/count mismatch"):
        _slice(
            status=wrong_status,
            events=events,
            recovered=recovered,
            shifted=shifted,
            expired=expired,
            pending=pending,
            mean_fraction=mean_fraction,
            mean_time=mean_time,
        )


def _event_branches() -> tuple[dict[str, object], ...]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    branches = schema["$defs"]["depletionEvent"]["allOf"]
    assert isinstance(branches, list)
    assert len(branches) == 3
    return tuple(branches)


def _branch_for_const(kind: str) -> dict[str, object]:
    for branch in _event_branches():
        condition = branch["if"]["properties"]["replenishment_kind"]
        if condition.get("const") == kind:
            return branch
    raise AssertionError(f"missing schema branch for {kind}")


def test_none_replenishment_schema_branch_matches_runtime_semantics() -> None:
    properties = _branch_for_const("NONE")["then"]["properties"]
    assert properties["replenishment_sequence_id"] == {"type": "null"}
    assert properties["replenishment_time_us"] == {"type": "null"}
    assert properties["replenished_quantity"] == {"const": "0"}
    assert properties["recovered_fraction"] == {"const": "0"}
    assert properties["directional_mid_shift_bps"] == {"const": "0"}
    assert set(properties["max_window_status"]["enum"]) == {
        "EXPIRED_NO_REPLENISHMENT",
        "PENDING_WINDOW",
    }


def test_quantity_replenishment_schema_branch_matches_runtime_semantics() -> None:
    quantity_branch = next(
        branch
        for branch in _event_branches()
        if set(branch["if"]["properties"]["replenishment_kind"].get("enum", []))
        == {"SAME_PRICE", "ADJACENT_PRICE"}
    )
    properties = quantity_branch["then"]["properties"]
    assert properties["replenishment_sequence_id"] == {"type": "integer", "minimum": 1}
    assert properties["replenishment_time_us"] == {"type": "integer", "minimum": 1}
    assert re.fullmatch(properties["replenished_quantity"]["pattern"], "0") is None
    assert re.fullmatch(properties["replenished_quantity"]["pattern"], "0.1")
    assert re.fullmatch(properties["recovered_fraction"]["pattern"], "0") is None
    assert re.fullmatch(properties["recovered_fraction"]["pattern"], "0.25")
    assert properties["directional_mid_shift_bps"] == {"const": "0"}
    assert properties["max_window_status"] == {"const": "REPLENISHED"}


def test_mid_shift_schema_branch_matches_runtime_semantics() -> None:
    properties = _branch_for_const("MID_SHIFT")["then"]["properties"]
    assert properties["replenishment_sequence_id"] == {"type": "integer", "minimum": 1}
    assert properties["replenishment_time_us"] == {"type": "integer", "minimum": 1}
    assert properties["replenished_quantity"] == {"const": "0"}
    assert properties["recovered_fraction"] == {"const": "0"}
    assert re.fullmatch(properties["directional_mid_shift_bps"]["pattern"], "0") is None
    assert re.fullmatch(properties["directional_mid_shift_bps"]["pattern"], "0.001")
    assert properties["max_window_status"] == {"const": "MID_SHIFTED"}
