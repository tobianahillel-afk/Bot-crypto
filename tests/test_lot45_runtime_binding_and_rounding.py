from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal, localcontext

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    CALCULATION_DECIMAL_ROUNDING,
    CODE_BOUND_PATHS,
    OrderFlowPolicy,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

ZERO_SHA256 = "0" * 64
QUOTE_SHA256 = "1" * 64


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


def _classified(
    trade_id: str,
    quantity: str,
    classification: str,
) -> ClassifiedTradeV1:
    trade = TimestampedTradeV1(
        "source-a",
        "venue-a",
        "BTC-USDT",
        "SPOT",
        trade_id,
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.110000Z",
        Decimal("100"),
        Decimal(quantity),
        "UNKNOWN",
    )
    if classification == "UNKNOWN":
        return ClassifiedTradeV1(
            trade,
            "UNKNOWN",
            "NONE",
            Decimal("0"),
            "lot44-aggressor-confidence-v1",
            ZERO_SHA256,
            ("UNKNOWN_REFERENCE",),
        )
    return ClassifiedTradeV1(
        trade,
        "BUY_AGGRESSOR",
        "QUOTE_TEST",
        Decimal("1"),
        "lot44-aggressor-confidence-v1",
        QUOTE_SHA256,
        ("QUOTE_REFERENCE",),
    )


def _repeating_ratio_flow():
    trades = (
        _classified("buy", "1", "BUY_AGGRESSOR"),
        _classified("unknown", "2", "UNKNOWN"),
    )
    return build_order_flow(trades, _policy())


def test_repeating_ratios_ignore_ambient_decimal_rounding() -> None:
    trades = (
        _classified("buy", "1", "BUY_AGGRESSOR"),
        _classified("unknown", "2", "UNKNOWN"),
    )

    with localcontext() as ambient:
        ambient.rounding = ROUND_DOWN
        down_flow, down_cvd = build_order_flow(trades, _policy())
    with localcontext() as ambient:
        ambient.rounding = ROUND_UP
        up_flow, up_cvd = build_order_flow(trades, _policy())

    assert CALCULATION_DECIMAL_ROUNDING == ROUND_HALF_EVEN
    assert down_flow.to_dict() == up_flow.to_dict()
    assert down_cvd.to_dict() == up_cvd.to_dict()


def test_model_validation_ignores_ambient_decimal_rounding() -> None:
    flow, _ = _repeating_ratio_flow()
    window = flow.windows[0]

    for rounding in (ROUND_DOWN, ROUND_UP):
        with localcontext() as ambient:
            ambient.rounding = rounding
            replayed_window = replace(window)
            replayed_flow = replace(flow, windows=(replayed_window,))
        assert replayed_window.to_dict() == window.to_dict()
        assert replayed_flow.to_dict() == flow.to_dict()


def test_code_binding_covers_complete_runtime_package_tree() -> None:
    assert "src/crypto_quant_bot" in CODE_BOUND_PATHS

    required = {
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_validation.py",
        "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
        "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
        "src/crypto_quant_bot/data_governance/market_data_governance_scope_and_source_registry.py",
        "src/crypto_quant_bot/data_governance/market_data_governance_scope_and_source_registry_models.py",
        "src/crypto_quant_bot/data_governance/source_registry_models.py",
        "src/crypto_quant_bot/data_governance/source_registry_state.py",
        "src/crypto_quant_bot/data_governance/source_registry_validation.py",
        "scripts/run_lot45_order_flow_delta_and_cvd_engine.py",
        "scripts/validate_lot45.py",
        "config/microstructure/order_flow_delta_and_cvd_engine_v1.json",
        "contracts/schemas/order_flow_delta_cvd_engine_state_v1.schema.json",
        "contracts/schemas/order_flow_delta_cvd_engine_audit_v1.schema.json",
        "contracts/schemas/order_flow_state_v1.schema.json",
        "contracts/schemas/cvd_series_v1.schema.json",
    }

    assert required <= set(CODE_BOUND_PATHS)
