from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    load_json_object,
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
