from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    load_json_object,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    CONFIG_PATH,
    _load_snapshot,
    build_lot44_artifacts,
    classify_trade,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    TimestampedTradeV1,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (
    CONFIDENCE_SEMANTICS,
    TradesAggressorClassificationValidationError,
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


def test_confidence_is_descriptive_not_probability_engine() -> None:
    state, _ = _reference()
    confidence = state.confidence_state
    assert confidence.semantics == CONFIDENCE_SEMANTICS
    assert confidence.quote_test_confidence == Decimal("1")
    assert confidence.tick_rule_confidence == Decimal("0.5")
    assert confidence.unknown_confidence == Decimal("0")
    assert all(
        item.confidence_version == "lot44-aggressor-confidence-v1"
        for item in state.classified_trades
    )


def test_inside_spread_remains_unknown_without_tick_fallback() -> None:
    state, _ = _reference()
    first = state.classified_trades[0]
    assert first.aggressor_classification == "UNKNOWN"
    assert first.classification_method == "NONE"
    assert "TRADE_INSIDE_SPREAD_UNKNOWN" in first.reason_codes


def test_tick_rule_only_when_quote_unavailable() -> None:
    state, _ = _reference()
    confidence = state.confidence_state
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
        confidence=confidence,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "BUY_AGGRESSOR"
    assert result.classification_method == "TICK_RULE"
    assert result.confidence == Decimal("0.5")


def test_zero_tick_without_quote_stays_unknown() -> None:
    state, _ = _reference()
    confidence = state.confidence_state
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
        confidence=confidence,
        tick_rule_fallback=True,
    )
    assert result.aggressor_classification == "UNKNOWN"
    assert result.classification_method == "NONE"


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
    assert "FUTURE_QUOTE_FORBIDDEN" in result.reason_codes


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
    assert "STALE_QUOTE_UNKNOWN" in result.reason_codes


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
    assert "LOCKED_QUOTE_UNKNOWN" in result.reason_codes


def test_identity_mismatch_fails_closed() -> None:
    state, _ = _reference()
    snapshot = _load_snapshot(ROOT, load_json_object(ROOT / CONFIG_PATH))
    trade = replace(
        state.classified_trades[1].trade,
        instrument_id="ETH-EUR-SPOT",
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="identity mismatch",
    ):
        classify_trade(
            trade,
            snapshot,
            None,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=True,
        )


def test_safety_never_authorizes_decision_or_execution() -> None:
    state, _ = _reference()
    assert state.safety["used_for_decision"] is False
    assert state.safety["signal_generation_allowed"] is False
    assert state.safety["risk_approval_allowed"] is False
    assert state.safety["order_routing_allowed"] is False
    assert state.safety["trade_allowed"] is False
    assert state.safety["execution_allowed"] is False
    assert state.safety["approved_size"] == 0
