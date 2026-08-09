from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine import (
    _levels,
    _validate_config,
    _validate_fixture_freshness,
    _validate_fixture_identity,
    _verify_gate,
    CONFIG_PATH,
    ZERO_SHA256,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    BookHealthStateV1,
    Lot38MetricsV1,
    OrderBookLevelV1,
    OrderBookSnapshotRawV1,
    OrderBookSnapshotV1,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_validation import (
    OrderBookL2SnapshotValidationError,
    duration_us,
    require_git_sha,
    require_integer,
    require_sha256,
    validate_reason_codes,
    validate_runtime_mode,
    validate_venue_state,
)

ROOT = Path(__file__).resolve().parents[1]


def config() -> dict[str, object]:
    return json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))


def lvl(price: str, quantity: str = "1") -> OrderBookLevelV1:
    return OrderBookLevelV1(Decimal(price), Decimal(quantity))


def raw(**overrides: object) -> OrderBookSnapshotRawV1:
    values: dict[str, object] = {
        "source_id": "source",
        "venue": "KRAKEN",
        "instrument_id": "BTC-EUR-SPOT",
        "market_type": "SPOT",
        "event_time": "2026-08-06T19:18:40.000000Z",
        "receive_time": "2026-08-06T19:18:40.050000Z",
        "sequence_id": 1,
        "venue_state": "OPEN",
        "bids": (lvl("100"),),
        "asks": (lvl("101"),),
        "used_for_decision": False,
    }
    values.update(overrides)
    return OrderBookSnapshotRawV1(**values)  # type: ignore[arg-type]


def test_config_contract_rejects_shape_and_identity_changes() -> None:
    value = config()
    _validate_config(value)
    missing = dict(value)
    missing.pop("run_id")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="fields"):
        _validate_config(missing)
    for field in ("schema_version", "config_version"):
        changed = dict(value)
        changed[field] = "wrong"
        with pytest.raises(OrderBookL2SnapshotValidationError, match="changed"):
            _validate_config(changed)


def test_config_contract_rejects_invalid_limits_and_state() -> None:
    value = config()
    for field in ("max_input_age_us", "published_depth_limit"):
        changed = dict(value)
        changed[field] = 0
        with pytest.raises(OrderBookL2SnapshotValidationError, match="integer"):
            _validate_config(changed)
    changed = dict(value)
    changed["fixture_venue_state"] = "UNKNOWN"
    with pytest.raises(OrderBookL2SnapshotValidationError, match="venue_state"):
        _validate_config(changed)


def test_gate_verification_accepts_exact_gate_and_rejects_wrong_path(
    tmp_path: Path,
) -> None:
    value = config()
    gate = _verify_gate(ROOT, value)
    assert gate["target_lot"] == 38
    changed = dict(value)
    changed["entry_gate_path"] = "missing.json"
    with pytest.raises(OSError):
        _verify_gate(tmp_path, changed)


def test_fixture_identity_is_explicitly_noncanonical() -> None:
    fixture = json.loads(
        (ROOT / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json").read_text(
            encoding="utf-8"
        )
    )
    _validate_fixture_identity(fixture)
    cases = (
        ("fixture_only", False, "fixture-only"),
        ("canonical_contract", True, "canonical"),
        ("used_for_decision", True, "decision"),
        ("schema_version", "wrong", "schema"),
    )
    for field, replacement, message in cases:
        changed = copy.deepcopy(fixture)
        changed[field] = replacement
        with pytest.raises(OrderBookL2SnapshotValidationError, match=message):
            _validate_fixture_identity(changed)


def test_fixture_freshness_rejects_future_and_stale_input() -> None:
    fixture = json.loads(
        (ROOT / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json").read_text(
            encoding="utf-8"
        )
    )
    value = config()
    _validate_fixture_freshness(fixture, value)
    future = copy.deepcopy(fixture)
    future["available_at"] = "2026-08-06T19:18:41.000000Z"
    with pytest.raises(OrderBookL2SnapshotValidationError, match="causal"):
        _validate_fixture_freshness(future, value)
    stale_config = dict(value)
    stale_config["input_reference_time"] = "2026-08-06T19:18:42.000000Z"
    with pytest.raises(OrderBookL2SnapshotValidationError, match="stale"):
        _validate_fixture_freshness(fixture, stale_config)


def test_levels_reject_invalid_collection_and_shape() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="non-empty"):
        _levels([], "bids")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="shape"):
        _levels([{"price": "1"}], "bids")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="positive"):
        _levels([{"price": "0", "quantity": "1"}], "bids")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="non-negative"):
        _levels([{"price": "1", "quantity": "-1"}], "bids")


def test_primitive_validation_rejects_boundary_types() -> None:
    for value in (True, -1, "1"):
        with pytest.raises(OrderBookL2SnapshotValidationError, match="integer"):
            require_integer(value, "field")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="git SHA"):
        require_git_sha("x" * 40, "sha")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="sha256"):
        require_sha256("x" * 64, "sha")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="runtime"):
        validate_runtime_mode("LIVE")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="venue_state"):
        validate_venue_state("HALTED")


def test_duration_and_reason_code_boundaries() -> None:
    from datetime import UTC, datetime, timedelta

    start = datetime(2026, 1, 1, tzinfo=UTC)
    assert duration_us(start, start + timedelta(microseconds=7)) == 7
    with pytest.raises(OrderBookL2SnapshotValidationError, match="backwards"):
        duration_us(start, start - timedelta(microseconds=1))
    with pytest.raises(OrderBookL2SnapshotValidationError, match="requires"):
        validate_reason_codes(())
    with pytest.raises(OrderBookL2SnapshotValidationError, match="unique"):
        validate_reason_codes(("A", "A"))
    with pytest.raises(OrderBookL2SnapshotValidationError, match="invalid"):
        validate_reason_codes(("not-canonical",))


def test_raw_contract_rejects_wrong_market_state_and_decision_flag() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="SPOT"):
        raw(market_type="PERP")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="venue_state"):
        raw(venue_state="UNKNOWN")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="decision"):
        raw(used_for_decision=True)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="bid and ask"):
        raw(bids=())


def snapshot(**overrides: object) -> OrderBookSnapshotV1:
    values: dict[str, object] = {
        "source_id": "source",
        "venue": "KRAKEN",
        "instrument_id": "BTC-EUR-SPOT",
        "market_type": "SPOT",
        "event_time": "2026-08-06T19:18:40.000000Z",
        "receive_time": "2026-08-06T19:18:40.050000Z",
        "sequence_id": 1,
        "sequence_anchor": ZERO_SHA256,
        "venue_state": "OPEN",
        "bids": (lvl("100"), lvl("99")),
        "asks": (lvl("101"), lvl("102")),
        "source_bid_depth": 2,
        "source_ask_depth": 2,
        "normalized_bid_depth": 2,
        "normalized_ask_depth": 2,
        "published_bid_depth": 2,
        "published_ask_depth": 2,
        "snapshot_checksum": ZERO_SHA256,
    }
    values.update(overrides)
    return OrderBookSnapshotV1(**values)  # type: ignore[arg-type]


def test_snapshot_contract_rejects_ordering_and_depth_mismatches() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="descending"):
        snapshot(bids=(lvl("99"), lvl("100")))
    with pytest.raises(OrderBookL2SnapshotValidationError, match="ascending"):
        snapshot(asks=(lvl("102"), lvl("101")))
    with pytest.raises(OrderBookL2SnapshotValidationError, match="bid depth mismatch"):
        snapshot(published_bid_depth=1)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="exceeds normalized"):
        snapshot(normalized_ask_depth=1)


def test_health_and_metrics_contracts_reject_inconsistent_values() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="status mismatch"):
        BookHealthStateV1(
            "LOCKED",
            "OPEN",
            False,
            False,
            True,
            1,
            1,
            1,
            1,
            1,
            1,
            ("LOT38_BOOK_OPEN_HEALTHY",),
            ZERO_SHA256,
        )
    with pytest.raises(OrderBookL2SnapshotValidationError, match="normalized levels"):
        Lot38MetricsV1(1, 2, 0, 1)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="published levels"):
        Lot38MetricsV1(2, 1, 1, 2)
