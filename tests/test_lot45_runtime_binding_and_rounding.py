from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal, localcontext

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    CALCULATION_DECIMAL_ROUNDING,
    CODE_BOUND_PATHS,
    OrderFlowPolicy,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_models import (
    CVDSeriesV1,
    Lot45LineageEnvelopeV1,
    Lot45RunContextV1,
    OrderFlowDeltaCVDEngineStateV1,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    CONFIG_VERSION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    VALIDATION_STATE,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    lot45_safety,
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
    *,
    event_time: str = "2026-08-06T19:18:40.100000Z",
    receive_time: str = "2026-08-06T19:18:40.110000Z",
) -> ClassifiedTradeV1:
    trade = TimestampedTradeV1(
        "source-a",
        "venue-a",
        "BTC-USDT",
        "SPOT",
        trade_id,
        event_time,
        receive_time,
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


def test_all_decimal_model_invariants_ignore_ambient_precision_and_rounding() -> None:
    first = "12345678901234567890123456789"
    second = "12345678901234567890123456788"
    trades = (
        _classified(
            "w1-buy",
            first,
            "BUY_AGGRESSOR",
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
        _classified(
            "w1-unknown",
            "1",
            "UNKNOWN",
            event_time="2026-08-06T19:18:40.200000Z",
            receive_time="2026-08-06T19:18:40.210000Z",
        ),
        _classified(
            "w2-buy",
            second,
            "BUY_AGGRESSOR",
            event_time="2026-08-06T19:18:41.100000Z",
            receive_time="2026-08-06T19:18:41.110000Z",
        ),
        _classified(
            "w2-unknown",
            "1",
            "UNKNOWN",
            event_time="2026-08-06T19:18:41.200000Z",
            receive_time="2026-08-06T19:18:41.210000Z",
        ),
    )
    flow, cvd = build_order_flow(trades, _policy())

    for precision in (9, 28):
        for rounding in (ROUND_DOWN, ROUND_UP):
            with localcontext() as ambient:
                ambient.prec = precision
                ambient.rounding = rounding
                replayed_windows = tuple(replace(window) for window in flow.windows)
                replayed_flow = replace(flow, windows=replayed_windows)
                replayed_points = tuple(replace(point) for point in cvd.points)
                replayed_cvd = replace(cvd, points=replayed_points)
            assert replayed_flow.to_dict() == flow.to_dict()
            assert replayed_cvd.to_dict() == cvd.to_dict()


def test_weighted_coverage_aggregates_from_raw_weighted_volume() -> None:
    trades = (
        _classified(
            "w1-buy",
            "1",
            "BUY_AGGRESSOR",
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
        _classified(
            "w1-unknown",
            "1",
            "UNKNOWN",
            event_time="2026-08-06T19:18:40.200000Z",
            receive_time="2026-08-06T19:18:40.210000Z",
        ),
        _classified(
            "w2-buy",
            "5",
            "BUY_AGGRESSOR",
            event_time="2026-08-06T19:18:41.100000Z",
            receive_time="2026-08-06T19:18:41.110000Z",
        ),
        _classified(
            "w2-unknown",
            "8",
            "UNKNOWN",
            event_time="2026-08-06T19:18:41.200000Z",
            receive_time="2026-08-06T19:18:41.210000Z",
        ),
    )
    flow, _ = build_order_flow(trades, _policy())

    assert [window.confidence_weighted_volume for window in flow.windows] == [
        Decimal("1"),
        Decimal("5"),
    ]
    assert flow.confidence_weighted_volume == Decimal("6")
    assert flow.total_volume == Decimal("15")
    assert flow.confidence_weighted_coverage == Decimal("0.4")


def test_session_ids_are_derived_from_event_time() -> None:
    flow, cvd = _repeating_ratio_flow()

    with pytest.raises(Lot45ValidationError, match="session_id"):
        replace(flow.windows[0], session_id="2099-01-01")
    with pytest.raises(Lot45ValidationError, match="session_id"):
        replace(cvd.points[0], session_id="2099-01-01")


def test_engine_state_binds_cvd_metrics_to_corresponding_window() -> None:
    trades = (
        _classified("buy", "1", "BUY_AGGRESSOR"),
        _classified("unknown", "1", "UNKNOWN"),
    )
    flow, cvd = build_order_flow(trades, _policy())
    point = cvd.points[0]
    forged_point = replace(point, signed_delta=Decimal("0"), cvd=Decimal("0"))
    forged_cvd = CVDSeriesV1(SESSION_POLICY_VERSION, (forged_point,), cvd.cvd_checksum)
    window = flow.windows[0]

    run_context = Lot45RunContextV1(
        "test-run",
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        CONFIG_VERSION,
        "a" * 40,
        "test-correlation",
    )
    lineage = Lot45LineageEnvelopeV1(
        "test-lineage",
        "1" * 64,
        "b" * 40,
        "2" * 64,
        "3" * 64,
        "4" * 64,
        "5" * 64,
        "6" * 64,
        "2026-08-06T19:18:40.110000Z",
    )
    with pytest.raises(Lot45ValidationError, match="CVD point signed delta mismatch"):
        OrderFlowDeltaCVDEngineStateV1(
            run_context,
            lineage,
            window.event_time,
            window.receive_time,
            "2026-08-06T19:18:41.000000Z",
            VALIDATION_STATE,
            POLICY_VERSION,
            WINDOW_POLICY_VERSION,
            SESSION_POLICY_VERSION,
            flow,
            forged_cvd,
            ("TEST_BINDING",),
            lot45_safety(),
            ZERO_SHA256,
        )


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
