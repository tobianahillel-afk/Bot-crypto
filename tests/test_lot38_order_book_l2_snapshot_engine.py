from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine import (
    _aggregate_levels,
    _build_health,
    _build_snapshot,
    build_lot38_artifacts,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
    OrderBookSnapshotRawV1,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_validation import (
    OrderBookL2SnapshotValidationError,
    decimal_from_text,
    decimal_text,
    lot38_safety,
    parse_utc_timestamp,
    validate_lot38_safety,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "1" * 40
FIXTURE_PATH = ROOT / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"


def level(price: str, quantity: str) -> OrderBookLevelV1:
    return OrderBookLevelV1(Decimal(price), Decimal(quantity))


def raw_snapshot(
    *,
    bids: tuple[OrderBookLevelV1, ...] | None = None,
    asks: tuple[OrderBookLevelV1, ...] | None = None,
    venue_state: str = "OPEN",
    sequence_id: int = 1001,
    event_time: str = "2026-08-06T19:18:40.000000Z",
    receive_time: str = "2026-08-06T19:18:40.050000Z",
) -> OrderBookSnapshotRawV1:
    return OrderBookSnapshotRawV1(
        source_id="offline-source",
        venue="KRAKEN",
        instrument_id="BTC-EUR-SPOT",
        market_type="SPOT",
        event_time=event_time,
        receive_time=receive_time,
        sequence_id=sequence_id,
        venue_state=venue_state,
        bids=bids or (level("100", "1"), level("99", "2")),
        asks=asks or (level("101", "1.5"), level("102", "3")),
        used_for_decision=False,
    )


def test_reference_snapshot_is_deterministic_and_depth_capped() -> None:
    state, audit = build_lot38_artifacts(ROOT, CODE_COMMIT)
    snapshot = state.snapshot
    assert snapshot.source_bid_depth == 3
    assert snapshot.source_ask_depth == 3
    assert snapshot.normalized_bid_depth == 3
    assert snapshot.normalized_ask_depth == 3
    assert snapshot.published_bid_depth == 2
    assert snapshot.published_ask_depth == 2
    assert [item.to_dict() for item in snapshot.bids] == [
        {"price": "50024.9", "quantity": "0.8"},
        {"price": "50024.8", "quantity": "1.25"},
    ]
    assert [item.to_dict() for item in snapshot.asks] == [
        {"price": "50025.1", "quantity": "0.7"},
        {"price": "50025.2", "quantity": "1.1"},
    ]
    assert state.book_health.health_status == "HEALTHY"
    assert state.metrics.duplicate_levels_aggregated_total == 0
    assert audit.snapshot_checksum == snapshot.snapshot_checksum
    assert audit.health_checksum == state.book_health.health_checksum


def test_reference_build_does_not_mutate_raw_fixture() -> None:
    before = FIXTURE_PATH.read_bytes()
    build_lot38_artifacts(ROOT, CODE_COMMIT)
    assert FIXTURE_PATH.read_bytes() == before


def test_raw_level_order_does_not_change_snapshot_checksum() -> None:
    bids = (level("99", "2"), level("100", "1"), level("98", "4"))
    asks = (level("102", "3"), level("101", "1.5"), level("103", "2"))
    first = _build_snapshot(raw_snapshot(bids=bids, asks=asks), 3)
    second = _build_snapshot(
        raw_snapshot(bids=tuple(reversed(bids)), asks=tuple(reversed(asks))),
        3,
    )
    assert first.to_dict() == second.to_dict()
    assert first.snapshot_checksum == second.snapshot_checksum


def test_duplicate_price_levels_are_aggregated_before_depth_cap() -> None:
    bids = (
        level("100", "1.2"),
        level("99", "2"),
        level("100", "0.8"),
    )
    asks = (
        level("101", "1"),
        level("102", "2"),
        level("101", "0.5"),
    )
    snapshot = _build_snapshot(raw_snapshot(bids=bids, asks=asks), 2)
    assert snapshot.source_bid_depth == 3
    assert snapshot.source_ask_depth == 3
    assert snapshot.normalized_bid_depth == 2
    assert snapshot.normalized_ask_depth == 2
    assert snapshot.bids[0].to_dict() == {"price": "100", "quantity": "2"}
    assert snapshot.asks[0].to_dict() == {"price": "101", "quantity": "1.5"}


def test_aggregate_levels_is_side_direction_aware() -> None:
    levels = (level("2", "1"), level("1", "2"), level("2", "3"))
    bids = _aggregate_levels(levels, descending=True)
    asks = _aggregate_levels(levels, descending=False)
    assert [item.price for item in bids] == [Decimal("2"), Decimal("1")]
    assert [item.price for item in asks] == [Decimal("1"), Decimal("2")]
    assert bids[0].quantity == Decimal("4")


def test_negative_quantity_is_rejected() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="non-negative"):
        level("100", "-0.1")


def test_zero_quantity_is_explicitly_allowed_by_lot38_contract() -> None:
    assert level("100", "0").quantity == Decimal("0")


def test_crossed_book_is_rejected() -> None:
    raw = raw_snapshot(bids=(level("102", "1"),), asks=(level("101", "1"),))
    with pytest.raises(OrderBookL2SnapshotValidationError, match="crossed"):
        _build_snapshot(raw, 1)


def test_locked_book_requires_explicit_locked_venue_state() -> None:
    equal_bids = (level("101", "1"),)
    equal_asks = (level("101", "2"),)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="LOCKED"):
        _build_snapshot(raw_snapshot(bids=equal_bids, asks=equal_asks), 1)
    snapshot = _build_snapshot(
        raw_snapshot(bids=equal_bids, asks=equal_asks, venue_state="LOCKED"),
        1,
    )
    health = _build_health(snapshot)
    assert health.health_status == "LOCKED"
    assert health.locked is True


def test_locked_flag_cannot_be_used_for_an_open_book() -> None:
    raw = raw_snapshot(venue_state="LOCKED")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="LOCKED"):
        _build_snapshot(raw, 2)


def test_sequence_anchor_changes_when_sequence_changes() -> None:
    first = _build_snapshot(raw_snapshot(sequence_id=1001), 2)
    second = _build_snapshot(raw_snapshot(sequence_id=1002), 2)
    assert first.sequence_anchor != second.sequence_anchor
    assert first.snapshot_checksum != second.snapshot_checksum


def test_raw_snapshot_rejects_noncausal_receive_time() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="causal"):
        raw_snapshot(
            event_time="2026-08-06T19:18:41.000000Z",
            receive_time="2026-08-06T19:18:40.000000Z",
        )


def test_decimal_contract_is_canonical_and_strict() -> None:
    assert decimal_text(Decimal("50024.9000")) == "50024.9"
    assert decimal_from_text("0", "quantity", allow_zero=True) == Decimal("0")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="positive"):
        decimal_from_text("0", "price", allow_zero=False)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="decimal text"):
        decimal_from_text(1, "price", allow_zero=False)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="invalid decimal"):
        decimal_from_text("bad", "price", allow_zero=False)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="finite"):
        decimal_from_text("NaN", "price", allow_zero=False)


def test_timestamp_contract_requires_utc_z() -> None:
    assert parse_utc_timestamp("2026-08-06T19:18:40.000000Z", "time").utcoffset() is not None
    with pytest.raises(OrderBookL2SnapshotValidationError, match="UTC Z"):
        parse_utc_timestamp("2026-08-06T19:18:40+00:00", "time")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="ISO"):
        parse_utc_timestamp("not-a-timeZ", "time")


def test_safety_map_is_fail_closed_and_tamper_evident() -> None:
    safety = lot38_safety()
    assert safety["analysis_only"] is True
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0
    tampered = dict(safety)
    tampered["trade_allowed"] = True
    with pytest.raises(OrderBookL2SnapshotValidationError, match="safety"):
        validate_lot38_safety(tampered)


def test_state_and_audit_are_json_serializable() -> None:
    state, audit = build_lot38_artifacts(ROOT, CODE_COMMIT)
    json.dumps(state.to_dict(), sort_keys=True)
    json.dumps(audit.to_dict(), sort_keys=True)
