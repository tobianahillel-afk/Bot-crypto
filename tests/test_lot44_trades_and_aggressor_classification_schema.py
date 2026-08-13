from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    CONFIG_PATH,
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_LOT43_AUDIT,
    EXPECTED_LOT43_POST_MERGE,
    EXPECTED_LOT43_RESILIENCE,
    EXPECTED_LOT43_STATE,
    EXPECTED_SNAPSHOT_CHECKSUM,
    EXPECTED_TRADE_FIXTURE_CHECKSUM,
    _load_snapshot,
    _load_trade_fixture,
    _validate_config,
    _verify_gate,
    build_lot44_artifacts,
    classify_trade,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    TimestampedTradeV1,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (
    CONFIDENCE_SEMANTICS,
    TradesAggressorClassificationValidationError,
    decimal_from_text,
    decimal_text,
    duration_us,
    lot44_safety,
    parse_utc_timestamp,
    require_closed_mapping,
    require_git_sha,
    require_integer,
    require_reason_codes,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_run_context,
    validate_safety,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "a" * 40


def _reference():
    return build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)


def _trade(
    *,
    trade_id: str,
    price: str,
    event_time: str,
    receive_time: str,
) -> TimestampedTradeV1:
    return TimestampedTradeV1(
        source_id="kraken-reference-offline-fixture",
        venue="KRAKEN",
        instrument_id="BTC-EUR-SPOT",
        market_type="SPOT",
        trade_id=trade_id,
        event_time=event_time,
        receive_time=receive_time,
        price=Decimal(price),
        quantity=Decimal("0.1"),
        source_side="UNKNOWN",
    )


def _assert_validation_error(expected: str, call) -> None:
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match=expected,
    ):
        call()


def test_reference_quote_test_classification_and_conservation() -> None:
    state, audit = _reference()
    assert tuple(
        item.aggressor_classification for item in state.classified_trades
    ) == ("UNKNOWN", "BUY_AGGRESSOR", "SELL_AGGRESSOR")
    assert tuple(item.classification_method for item in state.classified_trades) == (
        "NONE",
        "QUOTE_TEST",
        "QUOTE_TEST",
    )
    assert state.metrics.total_volume == Decimal("0.16")
    assert state.metrics.buy_volume == Decimal("0.08")
    assert state.metrics.sell_volume == Decimal("0.03")
    assert state.metrics.unknown_volume == Decimal("0.05")
    assert state.metrics.unknown_volume_ratio == Decimal("0.3125")
    assert state.metrics.total_volume == (
        state.metrics.buy_volume
        + state.metrics.sell_volume
        + state.metrics.unknown_volume
    )
    assert audit.state_output_checksum == state.output_checksum


def test_reference_lineage_context_and_checksums_are_exact() -> None:
    state, audit = _reference()
    assert state.run_context.runtime_mode == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert state.run_context.config_version == "lot44-trades-aggressor-classification-config-v1"
    assert state.run_context.code_commit == CODE_COMMIT
    assert state.lineage.entry_gate_checksum == EXPECTED_GATE_CHECKSUM
    assert state.lineage.lot43_state_checksum == EXPECTED_LOT43_STATE
    assert state.lineage.lot43_audit_checksum == EXPECTED_LOT43_AUDIT
    assert state.lineage.lot43_resilience_checksum == EXPECTED_LOT43_RESILIENCE
    assert state.lineage.lot43_post_merge_checksum == EXPECTED_LOT43_POST_MERGE
    assert state.lineage.trade_fixture_checksum == EXPECTED_TRADE_FIXTURE_CHECKSUM
    assert state.lineage.order_book_snapshot_checksum == EXPECTED_SNAPSHOT_CHECKSUM
    assert canonical_checksum(state.payload_without_checksum()) == state.output_checksum
    assert canonical_checksum(audit.payload_without_checksum()) == audit.audit_checksum


def test_confidence_is_descriptive_not_probability_engine() -> None:
    state, _ = _reference()
    confidence = state.confidence_state
    assert confidence.semantics == CONFIDENCE_SEMANTICS
    assert confidence.policy_version == "lot44-aggressor-confidence-v1"
    assert confidence.quote_test_confidence == Decimal("1")
    assert confidence.tick_rule_confidence == Decimal("0.5")
    assert confidence.unknown_confidence == Decimal("0")
    assert canonical_checksum(confidence.payload_without_checksum()) == (
        confidence.confidence_checksum
    )
    assert all(
        item.confidence_version == "lot44-aggressor-confidence-v1"
        for item in state.classified_trades
    )


def test_inside_spread_remains_unknown_without_tick_fallback() -> None:
    state, _ = _reference()
    first = state.classified_trades[0]
    assert first.aggressor_classification == "UNKNOWN"
    assert first.classification_method == "NONE"
    assert first.confidence == Decimal("0")
    assert first.quote_snapshot_checksum == EXPECTED_SNAPSHOT_CHECKSUM
    assert first.reason_codes == (
        "TRADE_INSIDE_SPREAD_UNKNOWN",
        "UNKNOWN_VOLUME_PRESERVED",
    )


def test_reference_buy_sell_quote_reasons_and_confidence_are_exact() -> None:
    state, _ = _reference()
    buy, sell = state.classified_trades[1:]
    assert buy.reason_codes == (
        "TRADE_AT_OR_ABOVE_ASK",
        "PARTICIPANT_INTENT_NOT_ASSERTED",
    )
    assert sell.reason_codes == (
        "TRADE_AT_OR_BELOW_BID",
        "PARTICIPANT_INTENT_NOT_ASSERTED",
    )
    for item in (buy, sell):
        assert item.classification_method == "QUOTE_TEST"
        assert item.confidence == Decimal("1")
        assert item.quote_snapshot_checksum == EXPECTED_SNAPSHOT_CHECKSUM


def test_tick_rule_only_when_quote_unavailable() -> None:
    state, _ = _reference()
    previous = _trade(
        trade_id="prev",
        price="100",
        event_time="2026-08-06T19:18:39.000000Z",
        receive_time="2026-08-06T19:18:39.010000Z",
    )
    up = _trade(
        trade_id="up",
        price="101",
        event_time="2026-08-06T19:18:40.000000Z",
        receive_time="2026-08-06T19:18:40.010000Z",
    )
    result = classify_trade(
        up,
        None,
        previous,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "BUY_AGGRESSOR"
    assert result.classification_method == "TICK_RULE"
    assert result.confidence == Decimal("0.5")
    assert result.quote_snapshot_checksum == "0" * 64
    assert result.reason_codes == (
        "QUOTE_UNAVAILABLE_TICK_UP",
        "PARTICIPANT_INTENT_NOT_ASSERTED",
    )


def test_tick_rule_down_is_sell_with_exact_reason() -> None:
    state, _ = _reference()
    previous = _trade(
        trade_id="prev-down",
        price="101",
        event_time="2026-08-06T19:18:39.000000Z",
        receive_time="2026-08-06T19:18:39.010000Z",
    )
    down = _trade(
        trade_id="down",
        price="100",
        event_time="2026-08-06T19:18:40.000000Z",
        receive_time="2026-08-06T19:18:40.010000Z",
    )
    result = classify_trade(
        down,
        None,
        previous,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "SELL_AGGRESSOR"
    assert result.classification_method == "TICK_RULE"
    assert result.confidence == Decimal("0.5")
    assert result.reason_codes[0] == "QUOTE_UNAVAILABLE_TICK_DOWN"


def test_quote_unavailable_without_evidence_stays_unknown() -> None:
    state, _ = _reference()
    current = _trade(
        trade_id="no-evidence",
        price="100",
        event_time="2026-08-06T19:18:40.000000Z",
        receive_time="2026-08-06T19:18:40.010000Z",
    )
    for fallback in (False, True):
        previous = None if fallback else current
        result = classify_trade(
            current,
            None,
            previous,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=fallback,
        )
        assert result.aggressor_classification == "UNKNOWN"
        assert result.reason_codes[0] == "QUOTE_UNAVAILABLE_NO_FALLBACK_EVIDENCE"


def test_zero_tick_without_quote_stays_unknown() -> None:
    state, _ = _reference()
    previous = _trade(
        trade_id="prev",
        price="100",
        event_time="2026-08-06T19:18:39.000000Z",
        receive_time="2026-08-06T19:18:39.010000Z",
    )
    same = _trade(
        trade_id="same",
        price="100",
        event_time="2026-08-06T19:18:40.000000Z",
        receive_time="2026-08-06T19:18:40.010000Z",
    )
    result = classify_trade(
        same,
        None,
        previous,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "UNKNOWN"
    assert result.classification_method == "NONE"
    assert result.reason_codes[0] == "QUOTE_UNAVAILABLE_ZERO_TICK_UNKNOWN"


def test_tick_rule_rejects_future_previous_trade() -> None:
    state, _ = _reference()
    current = _trade(
        trade_id="current",
        price="101",
        event_time="2026-08-06T19:18:40.000000Z",
        receive_time="2026-08-06T19:18:40.010000Z",
    )
    future = _trade(
        trade_id="future-prev",
        price="100",
        event_time="2026-08-06T19:18:41.000000Z",
        receive_time="2026-08-06T19:18:41.010000Z",
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="tick-rule previous trade cannot be future",
    ):
        classify_trade(
            current,
            None,
            future,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=True,
        )


def test_future_quote_is_never_backfilled_and_does_not_tick_fallback() -> None:
    state, _ = _reference()
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    trade = _trade(
        trade_id="future-quote",
        price="50025.10",
        event_time="2026-08-06T19:18:39.900000Z",
        receive_time="2026-08-06T19:18:40.040000Z",
    )
    result = classify_trade(
        trade,
        snapshot,
        None,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "UNKNOWN"
    assert result.reason_codes == (
        "FUTURE_QUOTE_FORBIDDEN",
        "UNKNOWN_VOLUME_PRESERVED",
    )


def test_stale_quote_degrades_to_unknown() -> None:
    state, _ = _reference()
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    trade = _trade(
        trade_id="stale",
        price="50025.10",
        event_time="2026-08-06T19:18:41.000000Z",
        receive_time="2026-08-06T19:18:41.000000Z",
    )
    result = classify_trade(
        trade,
        snapshot,
        None,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "UNKNOWN"
    assert result.reason_codes == (
        "STALE_QUOTE_UNKNOWN",
        "UNKNOWN_VOLUME_PRESERVED",
    )


def test_locked_quote_degrades_to_unknown() -> None:
    state, _ = _reference()
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    locked = replace(
        snapshot,
        venue_state="LOCKED",
        bids=(
            OrderBookLevelV1(snapshot.asks[0].price, Decimal("1")),
            *snapshot.bids[1:],
        ),
    )
    trade = _trade(
        trade_id="locked",
        price="50025.10",
        event_time=snapshot.event_time,
        receive_time=snapshot.receive_time,
    )
    result = classify_trade(
        trade,
        locked,
        None,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "UNKNOWN"
    assert result.reason_codes == (
        "LOCKED_QUOTE_UNKNOWN",
        "UNKNOWN_VOLUME_PRESERVED",
    )


def test_identity_mismatch_fails_closed() -> None:
    state, _ = _reference()
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    trade = replace(
        state.classified_trades[1].trade,
        instrument_id="ETH-EUR-SPOT",
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="trade and quote identity mismatch",
    ):
        classify_trade(
            trade,
            snapshot,
            None,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=True,
        )


def test_loaded_snapshot_matches_every_frozen_reference_field() -> None:
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    assert snapshot.source_id == "kraken-reference-offline-fixture"
    assert snapshot.venue == "KRAKEN"
    assert snapshot.instrument_id == "BTC-EUR-SPOT"
    assert snapshot.market_type == "SPOT"
    assert snapshot.event_time == "2026-08-06T19:18:40.000000Z"
    assert snapshot.receive_time == "2026-08-06T19:18:40.050000Z"
    assert snapshot.sequence_id == 1001
    assert snapshot.venue_state == "OPEN"
    assert snapshot.snapshot_checksum == EXPECTED_SNAPSHOT_CHECKSUM
    assert tuple((x.price, x.quantity) for x in snapshot.bids) == (
        (Decimal("50024.9"), Decimal("0.8")),
        (Decimal("50024.8"), Decimal("1.25")),
    )
    assert tuple((x.price, x.quantity) for x in snapshot.asks) == (
        (Decimal("50025.1"), Decimal("0.7")),
        (Decimal("50025.2"), Decimal("1.1")),
    )
    assert snapshot.source_bid_depth == snapshot.source_ask_depth == 3
    assert snapshot.normalized_bid_depth == snapshot.normalized_ask_depth == 3
    assert snapshot.published_bid_depth == snapshot.published_ask_depth == 2


def test_loaded_trade_fixture_maps_all_frozen_fields() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    trades, checksum = _load_trade_fixture(ROOT, config)
    assert checksum == EXPECTED_TRADE_FIXTURE_CHECKSUM
    assert tuple(item.trade_id for item in trades) == (
        "fixture-trade-001",
        "fixture-trade-002",
        "fixture-trade-003",
    )
    assert tuple(item.price for item in trades) == (
        Decimal("50025.00"),
        Decimal("50025.10"),
        Decimal("50024.90"),
    )
    assert tuple(item.quantity for item in trades) == (
        Decimal("0.05000000"),
        Decimal("0.08000000"),
        Decimal("0.03000000"),
    )
    for item in trades:
        assert item.source_id == "kraken-reference-offline-fixture"
        assert item.venue == "KRAKEN"
        assert item.instrument_id == "BTC-EUR-SPOT"
        assert item.market_type == "SPOT"
        assert item.event_time == "2026-08-06T19:18:40.000000Z"
        assert item.receive_time == "2026-08-06T19:18:40.050000Z"
        assert item.source_side == "UNKNOWN"


def test_config_validator_rejects_shape_identity_and_policy_drift() -> None:
    valid = load_json_object(ROOT / CONFIG_PATH)
    _validate_config(valid)
    variants = []
    missing = deepcopy(valid)
    missing.pop("run_id")
    variants.append((missing, "Lot 44 config fields differ from contract"))
    for field, value, message in (
        ("schema_version", "bad", "Lot 44 config schema changed"),
        ("config_version", "bad", "Lot 44 config version changed"),
        ("confidence_version", "", "confidence_version must be non-empty text"),
        ("generated_at", "not-time", "generated_at must use UTC Z suffix"),
        ("max_quote_age_us", 0, "max_quote_age_us must be >= 1"),
        ("tick_rule_fallback_when_quote_unavailable", False, "tick-rule fallback policy changed"),
        ("quote_test_confidence", "0.4", "Lot 44 v1 confidence policy constants changed"),
        ("tick_rule_confidence", "1", "Lot 44 v1 confidence policy constants changed"),
        ("unknown_confidence", "0.1", "Lot 44 v1 confidence policy constants changed"),
    ):
        changed = deepcopy(valid)
        changed[field] = value
        variants.append((changed, message))
    for changed, message in variants:
        with pytest.raises(TradesAggressorClassificationValidationError, match=message):
            _validate_config(changed)


def test_gate_validator_accepts_only_frozen_gate_and_prerequisites() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    _verify_gate(ROOT, config)
    gate = load_json_object(ROOT / config["entry_gate_path"])
    assert gate["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert gate["gate_status"] == "GO_LOT44_IMPLEMENTATION_ENTRY"
    assert gate["human_decision"] == "APPROVED_START_LOT44"
    assert gate["target_lot"] == 44
    assert gate["owner"] == "MicrostructureDomain"
    assert gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert gate["implementation_started"] is False
    assert gate["next_lot"] == 45
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    assert gate["safety"] == lot44_safety()
    prerequisites = gate["prerequisites"]
    assert prerequisites["lot43_state_checksum"] == EXPECTED_LOT43_STATE
    assert prerequisites["lot43_audit_checksum"] == EXPECTED_LOT43_AUDIT
    assert prerequisites["lot43_resilience_checksum"] == EXPECTED_LOT43_RESILIENCE
    assert prerequisites["lot43_post_merge_audit_checksum"] == EXPECTED_LOT43_POST_MERGE
    assert prerequisites["lot43_post_merge_verdict"] == "GO_LOT43_POST_MERGE"


def test_scalar_validation_helpers_enforce_exact_contracts() -> None:
    assert require_text("abc", "field") == "abc"
    assert require_integer(3, "count", minimum=1) == 3
    assert require_sha256("a" * 64, "checksum") == "a" * 64
    assert require_git_sha("b" * 40, "commit") == "b" * 40
    for value in (None, "", "   "):
        with pytest.raises(TradesAggressorClassificationValidationError):
            require_text(value, "field")
    for value in (True, "3", 0):
        with pytest.raises(TradesAggressorClassificationValidationError):
            require_integer(value, "count", minimum=1)
    for value in ("a" * 63, "A" * 64, "g" * 64):
        with pytest.raises(TradesAggressorClassificationValidationError):
            require_sha256(value, "checksum")
    for value in ("b" * 39, "B" * 40, "z" * 40):
        with pytest.raises(TradesAggressorClassificationValidationError):
            require_git_sha(value, "commit")


def test_decimal_validation_and_rendering_are_exact() -> None:
    assert decimal_from_text("1.25", "value") == Decimal("1.25")
    assert decimal_from_text("0", "value", allow_zero=True) == 0
    assert decimal_text(Decimal("1.2300")) == "1.23"
    assert decimal_text(Decimal("100.000")) == "100"
    assert decimal_text(Decimal("0.5000")) == "0.5"
    assert decimal_text(Decimal("0")) == "0"
    for value in (0, "invalid", "NaN", "Infinity", "-1", "0"):
        with pytest.raises(TradesAggressorClassificationValidationError):
            decimal_from_text(value, "value")
    with pytest.raises(TradesAggressorClassificationValidationError):
        decimal_text(Decimal("NaN"))


def test_time_validation_enforces_utc_causality_and_microseconds() -> None:
    event = "2026-08-06T19:18:40.000000Z"
    received = "2026-08-06T19:18:40.050000Z"
    generated = "2026-08-06T19:18:40.100000Z"
    assert parse_utc_timestamp(event, "event_time").microsecond == 0
    validate_causal_times(event, received, generated)
    assert duration_us(event, received) == 50000
    for value in ("2026-08-06T19:18:40", "badZ"):
        with pytest.raises(TradesAggressorClassificationValidationError):
            parse_utc_timestamp(value, "event_time")
    with pytest.raises(TradesAggressorClassificationValidationError):
        validate_causal_times(received, event, generated)
    with pytest.raises(TradesAggressorClassificationValidationError):
        validate_causal_times(event, generated, received)
    with pytest.raises(TradesAggressorClassificationValidationError):
        duration_us(received, event)


def test_reason_run_context_safety_and_mapping_helpers_fail_closed() -> None:
    require_reason_codes(("ONE", "TWO"))
    validate_run_context(
        "run",
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "config-v1",
        "a" * 40,
        "corr",
    )
    validate_safety(lot44_safety())
    assert require_closed_mapping({"a": 1}, {"a"}, "payload") == {"a": 1}
    for codes in ((), ("DUP", "DUP"), ("",)):
        with pytest.raises(TradesAggressorClassificationValidationError):
            require_reason_codes(codes)
    with pytest.raises(TradesAggressorClassificationValidationError):
        validate_run_context("run", "LIVE", "config-v1", "a" * 40, "corr")
    with pytest.raises(TradesAggressorClassificationValidationError):
        validate_run_context("run", "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "", "a" * 40, "corr")
    with pytest.raises(TradesAggressorClassificationValidationError):
        validate_run_context("run", "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "v", "bad", "corr")
    for field in lot44_safety():
        changed = lot44_safety()
        changed[field] = 1 if changed[field] is False else False
        with pytest.raises(TradesAggressorClassificationValidationError):
            validate_safety(changed)
    for payload in ({}, {"a": 1, "b": 2}, "not-object"):
        with pytest.raises(TradesAggressorClassificationValidationError):
            require_closed_mapping(payload, {"a"}, "payload")


def test_safety_never_authorizes_decision_or_execution() -> None:
    state, _ = _reference()
    assert state.safety["used_for_decision"] is False
    assert state.safety["signal_generation_allowed"] is False
    assert state.safety["risk_approval_allowed"] is False
    assert state.safety["order_routing_allowed"] is False
    assert state.safety["trade_allowed"] is False
    assert state.safety["execution_allowed"] is False
    assert state.safety["approved_size"] == 0
