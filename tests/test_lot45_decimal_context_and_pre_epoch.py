from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, Inexact, Rounded, localcontext

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    OrderFlowPolicy,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    CALCULATION_DECIMAL_EMAX,
    CALCULATION_DECIMAL_EMIN,
    CALCULATION_DECIMAL_PRECISION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    event_window_bounds,
    frozen_decimal_context,
    validate_causal_times,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

ZERO_SHA256 = "0" * 64
QUOTE_SHA256 = "1" * 64


def _policy() -> OrderFlowPolicy:
    return OrderFlowPolicy(
        CALCULATION_DECIMAL_PRECISION,
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
    *,
    event_time: str,
    receive_time: str,
    unknown: bool = False,
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
    if unknown:
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


def test_frozen_decimal_context_ignores_ambient_traps_and_exponent_limits() -> None:
    trades = (
        _classified(
            "huge-buy",
            "2E+100",
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
        _classified(
            "huge-unknown",
            "1E+100",
            event_time="2026-08-06T19:18:40.200000Z",
            receive_time="2026-08-06T19:18:40.210000Z",
            unknown=True,
        ),
    )
    reference_flow, reference_cvd = build_order_flow(trades, _policy())

    with localcontext() as ambient:
        ambient.prec = 9
        ambient.Emin = -2
        ambient.Emax = 2
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        hardened_flow, hardened_cvd = build_order_flow(trades, _policy())
        replayed_windows = tuple(replace(window) for window in hardened_flow.windows)
        replayed_flow = replace(hardened_flow, windows=replayed_windows)
        replayed_points = tuple(replace(point) for point in hardened_cvd.points)
        replayed_cvd = replace(hardened_cvd, points=replayed_points)

    assert hardened_flow.to_dict() == reference_flow.to_dict()
    assert hardened_cvd.to_dict() == reference_cvd.to_dict()
    assert replayed_flow.to_dict() == reference_flow.to_dict()
    assert replayed_cvd.to_dict() == reference_cvd.to_dict()

    with frozen_decimal_context() as context:
        assert context.prec == CALCULATION_DECIMAL_PRECISION
        assert context.Emin == CALCULATION_DECIMAL_EMIN
        assert context.Emax == CALCULATION_DECIMAL_EMAX
        assert context.traps[Inexact] is False
        assert context.traps[Rounded] is False


def test_causal_validation_rejects_noncanonical_generated_at() -> None:
    with pytest.raises(Lot45ValidationError, match="canonical UTC timestamp text"):
        validate_causal_times(
            "2026-08-06T19:18:40.000000Z",
            "2026-08-06T19:18:40.100000Z",
            "2026-08-06T19:18:41Z",
        )


def test_pre_epoch_gregorian_timestamp_has_valid_tumbling_window() -> None:
    event_time = "1960-01-01T00:00:00.100000Z"
    receive_time = "1960-01-01T00:00:00.200000Z"

    assert event_window_bounds(event_time, 1_000_000) == (
        "1960-01-01T00:00:00.000000Z",
        "1960-01-01T00:00:01.000000Z",
    )

    flow, cvd = build_order_flow(
        (
            _classified(
                "pre-epoch-buy",
                "1",
                event_time=event_time,
                receive_time=receive_time,
            ),
        ),
        _policy(),
    )
    assert flow.windows[0].window_start == "1960-01-01T00:00:00.000000Z"
    assert flow.windows[0].window_end == "1960-01-01T00:00:01.000000Z"
    assert flow.windows[0].session_id == "1960-01-01"
    assert cvd.points[0].event_time == event_time
