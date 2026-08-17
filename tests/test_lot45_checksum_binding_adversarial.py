from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    OrderFlowPolicy,
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


def _standalone_artifacts():
    return build_order_flow((_trade(),), _policy())


def test_standalone_window_rejects_forged_checksum() -> None:
    flow, _ = _standalone_artifacts()

    with pytest.raises(Lot45ValidationError, match="window checksum canonical mismatch"):
        replace(flow.windows[0], window_checksum="f" * 64)


def test_standalone_order_flow_rejects_forged_checksum() -> None:
    flow, _ = _standalone_artifacts()

    with pytest.raises(Lot45ValidationError, match="order-flow checksum canonical mismatch"):
        replace(flow, order_flow_checksum="f" * 64)


def test_standalone_cvd_rejects_forged_checksum() -> None:
    _, cvd = _standalone_artifacts()

    with pytest.raises(Lot45ValidationError, match="CVD checksum canonical mismatch"):
        replace(cvd, cvd_checksum="f" * 64)


def test_zero_checksum_sentinel_is_immediately_canonicalized() -> None:
    flow, cvd = _standalone_artifacts()
    window = replace(flow.windows[0], window_checksum="0" * 64)
    rebuilt_flow = replace(flow, windows=(window,), order_flow_checksum="0" * 64)
    rebuilt_cvd = replace(cvd, cvd_checksum="0" * 64)

    assert window.window_checksum == canonical_checksum(window.payload_without_checksum())
    assert window.window_checksum != "0" * 64
    assert rebuilt_flow.order_flow_checksum == canonical_checksum(
        rebuilt_flow.payload_without_checksum()
    )
    assert rebuilt_flow.order_flow_checksum != "0" * 64
    assert rebuilt_cvd.cvd_checksum == canonical_checksum(rebuilt_cvd.payload_without_checksum())
    assert rebuilt_cvd.cvd_checksum != "0" * 64


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("trades_total", True),
        ("buy_trades_total", True),
        ("sell_trades_total", False),
        ("unknown_trades_total", False),
    ),
)
def test_order_flow_aggregate_counts_reject_booleans(field: str, value: bool) -> None:
    flow, _ = _standalone_artifacts()

    with pytest.raises(Lot45ValidationError, match=rf"{field} must be integer"):
        replace(flow, **{field: value, "order_flow_checksum": "0" * 64})
