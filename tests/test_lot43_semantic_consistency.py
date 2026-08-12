from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
    analyze_book_resilience,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_models import (
    BookDepletionEventV1,
    BookResilienceSliceV1,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    REGIME_METHOD,
    Lot43ValidationError,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis import BookObservation
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import OrderBookLevelV1

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/schemas/book_resilience_state_v1.schema.json"
RECOVERY_THRESHOLD = Decimal("0.25")
ZERO_SHA256 = "0" * 64


def _policy() -> BookResiliencePolicy:
    return BookResiliencePolicy(
        50,
        Decimal("0.1"),
        Decimal("0.25"),
        RECOVERY_THRESHOLD,
        Decimal("0.05"),
        Decimal("0.05"),
        (10_000, 25_000),
        Decimal("0.05"),
        Decimal("0.5"),
    )


def _observation(sequence: int, receive_time: str) -> BookObservation:
    return BookObservation(
        "source",
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        "2026-08-06T19:18:40.000001Z",
        receive_time,
        (OrderBookLevelV1(Decimal("100"), Decimal("1")),),
        (OrderBookLevelV1(Decimal("102"), Decimal("1")),),
    )


def _event(**changes: object) -> BookDepletionEventV1:
    values: dict[str, object] = {
        "event_id": "lot43-semantic-event",
        "side": "BID",
        "depleted_price": Decimal("100"),
        "previous_quantity": Decimal("10"),
        "post_depletion_quantity": Decimal("2"),
        "depleted_quantity": Decimal("8"),
        "depletion_ratio": Decimal("0.8"),
        "depletion_sequence_id": 2,
        "depletion_event_time": "2026-08-06T19:18:40.000019Z",
        "depletion_receive_time": "2026-08-06T19:18:40.000020Z",
        "replenishment_kind": "NONE",
        "replenishment_sequence_id": None,
        "replenishment_time_us": None,
        "replenished_quantity": Decimal("0"),
        "recovered_fraction": Decimal("0"),
        "directional_mid_shift_bps": Decimal("0"),
        "max_window_status": "EXPIRED_NO_REPLENISHMENT",
        "participant_intent": "NOT_INFERRED",
        "reason_codes": ("LOT43_SEMANTIC_CONSISTENCY_TEST",),
        "event_checksum": ZERO_SHA256,
    }
    values.update(changes)
    return BookDepletionEventV1(**values)  # type: ignore[arg-type]


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
    recovery_threshold: Decimal = RECOVERY_THRESHOLD,
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
        ZERO_SHA256,
        replenishment_min_recovery_ratio=recovery_threshold,
    )


def test_analysis_rejects_future_observations_but_allows_decision_boundary() -> None:
    first = _observation(1, "2026-08-06T19:18:40.000010Z")
    boundary = _observation(2, "2026-08-06T19:18:40.000020Z")
    result = analyze_book_resilience(
        (first, boundary),
        _policy(),
        "2026-08-06T19:18:40.000020Z",
    )
    assert result.observations == (first, boundary)

    future = _observation(2, "2026-08-06T19:18:40.000021Z")
    with pytest.raises(Lot43ValidationError, match="available_at cannot exceed decision_time"):
        analyze_book_resilience(
            (first, future),
            _policy(),
            "2026-08-06T19:18:40.000020Z",
        )


def test_depletion_event_requires_utc_causal_timestamps() -> None:
    _event()
    with pytest.raises(Lot43ValidationError):
        _event(depletion_event_time="not-a-time")
    with pytest.raises(Lot43ValidationError):
        _event(depletion_receive_time="2026-08-06T19:18:40.000020+00:00")
    with pytest.raises(Lot43ValidationError, match="cannot exceed"):
        _event(
            depletion_event_time="2026-08-06T19:18:40.000021Z",
            depletion_receive_time="2026-08-06T19:18:40.000020Z",
        )


def test_replenishment_sequence_must_be_strictly_future() -> None:
    valid = {
        "replenishment_kind": "SAME_PRICE",
        "replenishment_time_us": 10,
        "replenished_quantity": Decimal("8"),
        "recovered_fraction": Decimal("1"),
        "max_window_status": "REPLENISHED",
    }
    assert _event(replenishment_sequence_id=3, **valid).replenishment_sequence_id == 3
    for invalid_sequence in (1, 2):
        with pytest.raises(Lot43ValidationError, match="strictly after depletion sequence"):
            _event(replenishment_sequence_id=invalid_sequence, **valid)


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
def test_resilience_slice_accepts_only_the_status_derived_from_policy(
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
def test_resilience_slice_rejects_status_count_threshold_mismatches(
    wrong_status: str,
    events: int,
    recovered: int,
    shifted: int,
    expired: int,
    pending: int,
    mean_fraction: Decimal | None,
    mean_time: Decimal | None,
) -> None:
    with pytest.raises(Lot43ValidationError, match="status/count/threshold mismatch"):
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


def test_resilient_status_requires_mean_at_or_above_versioned_threshold() -> None:
    with pytest.raises(Lot43ValidationError, match="status/count/threshold mismatch"):
        _slice(
            status="RESILIENT",
            events=1,
            recovered=1,
            shifted=0,
            expired=0,
            pending=0,
            mean_fraction=Decimal("0.24"),
            mean_time=Decimal("10000"),
        )
    partial = _slice(
        status="PARTIAL",
        events=1,
        recovered=1,
        shifted=0,
        expired=0,
        pending=0,
        mean_fraction=Decimal("0.24"),
        mean_time=Decimal("10000"),
    )
    assert partial.resilience_status == "PARTIAL"


def test_slice_requires_strictly_positive_versioned_recovery_threshold() -> None:
    with pytest.raises(Lot43ValidationError, match="strictly positive"):
        _slice(
            status="NO_EVENTS",
            events=0,
            recovered=0,
            shifted=0,
            expired=0,
            pending=0,
            mean_fraction=None,
            mean_time=None,
            recovery_threshold=Decimal("0"),
        )


def test_slice_serializes_versioned_recovery_threshold() -> None:
    slice_state = _slice(
        status="RESILIENT",
        events=1,
        recovered=1,
        shifted=0,
        expired=0,
        pending=0,
        mean_fraction=Decimal("0.5"),
        mean_time=Decimal("10000"),
    )
    assert slice_state.to_dict()["replenishment_min_recovery_ratio"] == "0.25"


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


def test_resilience_slice_schema_requires_positive_recovery_threshold() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    contract = schema["$defs"]["resilienceSlice"]
    assert "replenishment_min_recovery_ratio" in contract["required"]
    pattern = contract["properties"]["replenishment_min_recovery_ratio"]["pattern"]
    assert re.fullmatch(pattern, "0") is None
    assert re.fullmatch(pattern, "0.25")
    assert re.fullmatch(pattern, "1")
    assert re.fullmatch(pattern, "-0.1") is None
    assert re.fullmatch(pattern, "1.1") is None
