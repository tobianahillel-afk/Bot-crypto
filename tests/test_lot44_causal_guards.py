from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    load_json_object,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    CONFIG_PATH,
    _load_snapshot,
    _validate_confidence_policy,
    build_lot44_artifacts,
    classify_trade,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    AggressorConfidenceStateV1,
    ClassifiedTradeV1,
    Lot44MetricsV1,
    TimestampedTradeV1,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (
    TradesAggressorClassificationValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "c" * 40


def _trade(
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


def test_quote_with_future_event_is_unknown_even_when_received_first() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    delayed_trade = _trade(
        "future-event-quote",
        "50025.10",
        "2026-08-06T19:18:39.900000Z",
        "2026-08-06T19:18:40.100000Z",
    )

    result = classify_trade(
        delayed_trade,
        snapshot,
        None,
        max_quote_age_us=250000,
        confidence=state.confidence_state,
        tick_rule_fallback=True,
    )

    assert snapshot.receive_time < delayed_trade.receive_time
    assert snapshot.event_time > delayed_trade.event_time
    assert result.aggressor_classification == "UNKNOWN"
    assert result.classification_method == "NONE"
    assert result.reason_codes == (
        "FUTURE_QUOTE_FORBIDDEN",
        "UNKNOWN_VOLUME_PRESERVED",
    )


def test_tick_rule_rejects_future_event_even_when_previous_arrived_first() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    current = _trade(
        "current-delayed",
        "101",
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.100000Z",
    )
    future_event_previous = _trade(
        "future-event-previous",
        "100",
        "2026-08-06T19:18:40.050000Z",
        "2026-08-06T19:18:40.060000Z",
    )

    assert future_event_previous.receive_time < current.receive_time
    assert future_event_previous.event_time > current.event_time
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="tick-rule previous trade cannot be future",
    ):
        classify_trade(
            current,
            None,
            future_event_previous,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=True,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source_id", "different-source"),
        ("venue", "OTHER-VENUE"),
        ("instrument_id", "ETH-EUR-SPOT"),
    ),
)
def test_tick_rule_rejects_previous_trade_identity_mismatch(
    field: str,
    value: str,
) -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    current = _trade(
        "identity-current",
        "101",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.150000Z",
    )
    previous = _trade(
        "identity-previous",
        "100",
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.050000Z",
    )
    mismatched = replace(previous, **{field: value})
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="tick-rule previous trade identity mismatch",
    ):
        classify_trade(
            current,
            None,
            mismatched,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=True,
        )


@pytest.mark.parametrize(
    ("classification", "method", "confidence"),
    (
        ("UNKNOWN", "NONE", Decimal("0.5")),
        ("BUY_AGGRESSOR", "NONE", Decimal("0")),
        ("UNKNOWN", "QUOTE_TEST", Decimal("1")),
        ("BUY_AGGRESSOR", "QUOTE_TEST", Decimal("0")),
        ("SELL_AGGRESSOR", "TICK_RULE", Decimal("1")),
    ),
)
def test_classified_trade_rejects_schema_incompatible_tuple(
    classification: str,
    method: str,
    confidence: Decimal,
) -> None:
    trade = _trade(
        "tuple-invalid",
        "100",
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.050000Z",
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="classification method/class/confidence tuple invalid",
    ):
        ClassifiedTradeV1(
            trade=trade,
            aggressor_classification=classification,
            classification_method=method,
            confidence=confidence,
            confidence_version="lot44-aggressor-confidence-v1",
            quote_snapshot_checksum="0" * 64,
            reason_codes=("NEGATIVE_TEST",),
        )


def test_confidence_state_requires_exact_v1_constants() -> None:
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 v1 confidence constants changed",
    ):
        AggressorConfidenceStateV1(
            policy_version="lot44-aggressor-confidence-v1",
            semantics="DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY",
            quote_test_confidence=Decimal("0.9"),
            tick_rule_confidence=Decimal("0.4"),
            unknown_confidence=Decimal("0"),
            confidence_checksum="0" * 64,
        )


def test_config_requires_exact_v1_confidence_constants() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    config["quote_test_confidence"] = "0.9"
    config["tick_rule_confidence"] = "0.4"
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 v1 confidence policy constants changed",
    ):
        _validate_confidence_policy(config)


def test_state_rejects_self_consistent_wrong_category_counts() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    bad_metrics = replace(
        state.metrics,
        buy_trades_total=2,
        sell_trades_total=1,
        unknown_trades_total=0,
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="metrics do not match classified trades",
    ):
        replace(state, metrics=bad_metrics)


def test_state_rejects_self_consistent_wrong_category_volumes() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    bad_metrics = Lot44MetricsV1(
        trades_total=3,
        buy_trades_total=1,
        sell_trades_total=1,
        unknown_trades_total=1,
        total_volume=Decimal("0.16"),
        buy_volume=Decimal("0.05"),
        sell_volume=Decimal("0.03"),
        unknown_volume=Decimal("0.08"),
        unknown_volume_ratio=Decimal("0.5"),
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="metrics do not match classified trades",
    ):
        replace(state, metrics=bad_metrics)
