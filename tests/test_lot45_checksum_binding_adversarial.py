from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    OrderFlowPolicy,
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
        "checksum-binding-trade",
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


def test_engine_state_rejects_jointly_forged_window_and_cvd_checksums() -> None:
    trades = (_trade(),)
    flow, cvd = build_order_flow(trades, _policy())

    forged_checksum = "f" * 64
    forged_window = replace(flow.windows[0], window_checksum=forged_checksum)
    forged_flow = replace(flow, windows=(forged_window,))
    forged_flow = replace(
        forged_flow,
        order_flow_checksum=canonical_checksum(forged_flow.payload_without_checksum()),
    )

    forged_point = replace(cvd.points[0], window_checksum=forged_checksum)
    forged_cvd = replace(cvd, points=(forged_point,))
    forged_cvd = replace(
        forged_cvd,
        cvd_checksum=canonical_checksum(forged_cvd.payload_without_checksum()),
    )

    config = {
        "run_id": "lot45-checksum-adversarial",
        "correlation_id": "lot45-checksum-adversarial",
        "lineage_id": "lot45-from-certified-lot44-order-flow-inputs-v1",
        "generated_at": "2026-08-06T19:18:41.100000Z",
    }
    state44 = {"receive_time": "2026-08-06T19:18:40.050000Z"}

    with pytest.raises(Lot45ValidationError, match="window checksum canonical mismatch"):
        _build_engine_state(
            config,
            "1" * 40,
            state44,
            trades,
            forged_flow,
            forged_cvd,
        )
