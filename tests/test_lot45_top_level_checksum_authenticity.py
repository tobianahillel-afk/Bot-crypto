from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    OrderFlowPolicy,
    _build_engine_audit,
    _build_engine_state,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

ZERO_SHA256 = "0" * 64


def _policy() -> OrderFlowPolicy:
    return OrderFlowPolicy(
        50,
        1_000_000,
        2_000_000,
        Decimal("1"),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def _trade() -> ClassifiedTradeV1:
    trade = TimestampedTradeV1(
        "source-a",
        "venue-a",
        "BTC-USDT",
        "SPOT",
        "top-level-checksum-trade",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.110000Z",
        Decimal("100"),
        Decimal("1"),
        "UNKNOWN",
    )
    return ClassifiedTradeV1(
        trade,
        "BUY_AGGRESSOR",
        "QUOTE_TEST",
        Decimal("1"),
        "lot44-aggressor-confidence-v1",
        "1" * 64,
        ("QUOTE_REFERENCE",),
    )


def _state_and_audit():
    trades = (_trade(),)
    flow, cvd = build_order_flow(trades, _policy())
    config = {
        "run_id": "lot45-top-level-checksum-adversarial",
        "correlation_id": "lot45-top-level-checksum-adversarial",
        "lineage_id": "lot45-from-certified-lot44-order-flow-inputs-v1",
        "generated_at": "2026-08-06T19:18:41.100000Z",
    }
    state44 = {
        "receive_time": "2026-08-06T19:18:40.110000Z",
        "generated_at": "2026-08-06T19:18:41.000000Z",
    }
    state = _build_engine_state(config, "1" * 40, state44, trades, flow, cvd)
    audit = _build_engine_audit(config, "1" * 40, state, flow, cvd)
    return state, audit


def test_engine_state_rejects_forged_top_level_output_checksum() -> None:
    state, _ = _state_and_audit()

    with pytest.raises(Lot45ValidationError, match="output_checksum canonical mismatch"):
        replace(
            state,
            generated_at="2026-08-06T19:18:43.000000Z",
            output_checksum="f" * 64,
        )


def test_engine_state_rejects_zero_checksum_sentinel_on_reconstruction() -> None:
    state, _ = _state_and_audit()

    with pytest.raises(Lot45ValidationError, match="zero sentinel forbidden"):
        replace(
            state,
            generated_at="2026-08-06T19:18:43.000000Z",
            output_checksum=ZERO_SHA256,
        )


def test_engine_audit_rejects_forged_top_level_audit_checksum() -> None:
    _, audit = _state_and_audit()

    with pytest.raises(Lot45ValidationError, match="audit_checksum canonical mismatch"):
        replace(audit, audit_checksum="f" * 64)


@pytest.mark.parametrize(
    "field",
    (
        "state_output_checksum",
        "config_checksum",
        "entry_gate_checksum",
        "lot44_state_checksum",
        "lot44_audit_checksum",
        "lot44_confidence_checksum",
        "lot44_post_merge_checksum",
        "order_flow_checksum",
        "cvd_checksum",
    ),
)
def test_engine_audit_rejects_invalid_bound_checksum_fields(field: str) -> None:
    _, audit = _state_and_audit()

    with pytest.raises(Lot45ValidationError, match=field):
        replace(
            audit,
            **{field: "not-a-sha256", "audit_checksum": "0" * 64},
        )
