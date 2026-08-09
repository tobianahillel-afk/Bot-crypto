from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine import (
    _aggregate_levels,
    _build_health,
    _build_snapshot,
    _sequence_anchor,
    build_lot38_artifacts,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
    OrderBookSnapshotRawV1,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_validation import (
    OrderBookL2SnapshotValidationError,
    decimal_text,
    duration_us,
    lot38_safety,
    require_git_sha,
    require_integer,
    require_sha256,
    validate_causal_times,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "a" * 40


def level(price: str, quantity: str) -> OrderBookLevelV1:
    return OrderBookLevelV1(Decimal(price), Decimal(quantity))


def raw(
    *,
    source_id: str = "source-a",
    sequence_id: int = 7,
    bids: tuple[OrderBookLevelV1, ...] | None = None,
    asks: tuple[OrderBookLevelV1, ...] | None = None,
) -> OrderBookSnapshotRawV1:
    return OrderBookSnapshotRawV1(
        source_id=source_id,
        venue="KRAKEN",
        instrument_id="BTC-EUR-SPOT",
        market_type="SPOT",
        event_time="2026-08-06T19:18:40.000000Z",
        receive_time="2026-08-06T19:18:40.050000Z",
        sequence_id=sequence_id,
        venue_state="OPEN",
        bids=bids or (level("100", "1"), level("99", "2")),
        asks=asks or (level("101", "3"), level("102", "4")),
        used_for_decision=False,
    )


def test_duration_uses_exact_day_second_and_microsecond_components() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    delta = timedelta(days=1, seconds=2, microseconds=3)
    assert duration_us(start, start + delta) == 86_402_000_003


def test_integer_validator_rejects_bool_and_minimum_minus_one() -> None:
    assert require_integer(3, "field", minimum=3) == 3
    with pytest.raises(OrderBookL2SnapshotValidationError):
        require_integer(2, "field", minimum=3)
    with pytest.raises(OrderBookL2SnapshotValidationError):
        require_integer(True, "field", minimum=0)


def test_sha_validators_require_exact_lowercase_lengths() -> None:
    require_git_sha("a" * 40, "git")
    require_sha256("b" * 64, "sha")
    for invalid in ("a" * 39, "A" * 40, "g" * 40):
        with pytest.raises(OrderBookL2SnapshotValidationError):
            require_git_sha(invalid, "git")
    for invalid in ("b" * 63, "B" * 64, "z" * 64):
        with pytest.raises(OrderBookL2SnapshotValidationError):
            require_sha256(invalid, "sha")


def test_causal_times_accept_equal_boundaries_and_reject_each_inversion() -> None:
    t0 = "2026-08-06T19:18:40.000000Z"
    t1 = "2026-08-06T19:18:40.000001Z"
    t2 = "2026-08-06T19:18:40.000002Z"
    validate_causal_times(t0, t0, t0)
    validate_causal_times(t0, t1, t2)
    with pytest.raises(OrderBookL2SnapshotValidationError):
        validate_causal_times(t1, t0, t2)
    with pytest.raises(OrderBookL2SnapshotValidationError):
        validate_causal_times(t0, t2, t1)


def test_decimal_text_preserves_exact_non_float_semantics() -> None:
    assert decimal_text(Decimal("0.0001000")) == "0.0001"
    assert decimal_text(Decimal("100.000")) == "100"
    assert decimal_text(Decimal("123456789.123456789")) == "123456789.123456789"


def test_aggregation_sums_all_duplicates_exactly() -> None:
    levels = (
        level("100", "0.1"),
        level("99", "1"),
        level("100", "0.2"),
        level("100", "0.3"),
    )
    aggregated = _aggregate_levels(levels, descending=True)
    assert tuple(item.price for item in aggregated) == (Decimal("100"), Decimal("99"))
    assert aggregated[0].quantity == Decimal("0.6")
    assert aggregated[1].quantity == Decimal("1")


def test_sequence_anchor_binds_every_identity_component() -> None:
    reference = raw()
    base = _sequence_anchor(reference)
    assert _sequence_anchor(raw(source_id="source-b")) != base
    assert _sequence_anchor(raw(sequence_id=8)) != base
    changed_time = OrderBookSnapshotRawV1(
        source_id=reference.source_id,
        venue=reference.venue,
        instrument_id=reference.instrument_id,
        market_type=reference.market_type,
        event_time="2026-08-06T19:18:39.999999Z",
        receive_time=reference.receive_time,
        sequence_id=reference.sequence_id,
        venue_state=reference.venue_state,
        bids=reference.bids,
        asks=reference.asks,
        used_for_decision=False,
    )
    assert _sequence_anchor(changed_time) != base


def test_depth_limit_is_part_of_canonical_snapshot_payload() -> None:
    source = raw(
        bids=(level("100", "1"), level("99", "2"), level("98", "3")),
        asks=(level("101", "1"), level("102", "2"), level("103", "3")),
    )
    depth_one = _build_snapshot(source, 1)
    depth_two = _build_snapshot(source, 2)
    assert depth_one.published_bid_depth == 1
    assert depth_two.published_bid_depth == 2
    assert depth_one.snapshot_checksum != depth_two.snapshot_checksum
    assert canonical_checksum(depth_one.payload_without_checksum()) == depth_one.snapshot_checksum


def test_health_checksum_binds_status_depths_and_reasons() -> None:
    snapshot = _build_snapshot(raw(), 2)
    health = _build_health(snapshot)
    assert canonical_checksum(health.payload_without_checksum()) == health.health_checksum
    payload = health.payload_without_checksum()
    payload["published_bid_depth"] = 1
    assert canonical_checksum(payload) != health.health_checksum


def test_reference_artifact_checksums_are_self_consistent() -> None:
    state, audit = build_lot38_artifacts(ROOT, CODE_COMMIT)
    assert canonical_checksum(state.payload_without_checksum()) == state.output_checksum
    assert canonical_checksum(audit.payload_without_checksum()) == audit.audit_checksum
    assert canonical_checksum(state.snapshot.payload_without_checksum()) == state.snapshot.snapshot_checksum
    assert canonical_checksum(state.book_health.payload_without_checksum()) == state.book_health.health_checksum
    assert audit.state_output_checksum == state.output_checksum


def test_safety_has_no_permissive_boolean_or_size() -> None:
    safety = lot38_safety()
    assert safety == {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "participant_behavior_inference_explicitly_labeled": True,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "scenario_score_is_signal": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }
