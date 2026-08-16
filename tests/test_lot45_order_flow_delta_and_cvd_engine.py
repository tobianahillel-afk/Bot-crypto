from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    EXPECTED_GATE_MERGE,
    OrderFlowPolicy,
    build_lot45_artifacts,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_models import (
    CVDPointV1,
    CVDSeriesV1,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    decimal_text,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO_SHA256 = "0" * 64
QUOTE_SHA256 = "1" * 64
REFERENCE_CODE_TREE_SHA = "7bcb1bae7822bda412c73b08548957f79d596c98"


def _policy(*, unknown_ratio: str = "1") -> OrderFlowPolicy:
    return OrderFlowPolicy(
        50,
        1_000_000,
        2_000_000,
        Decimal(unknown_ratio),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def _classified(
    trade_id: str,
    event_time: str,
    receive_time: str,
    quantity: str,
    classification: str,
    *,
    source_id: str = "source-a",
    venue: str = "venue-a",
    instrument_id: str = "BTC-USDT",
) -> ClassifiedTradeV1:
    trade = TimestampedTradeV1(
        source_id,
        venue,
        instrument_id,
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
        classification,
        "QUOTE_TEST",
        Decimal("1"),
        "lot44-aggressor-confidence-v1",
        QUOTE_SHA256,
        ("QUOTE_REFERENCE",),
    )


def test_reference_frozen_lot44_builds_expected_order_flow() -> None:
    state, audit, order_flow, cvd = build_lot45_artifacts(ROOT, REFERENCE_CODE_TREE_SHA)

    assert state["validation_state"] == "VALIDATED_OFFLINE_ORDER_FLOW_DELTA_CVD_ONLY"
    assert order_flow["trades_total"] == 3
    assert order_flow["buy_trades_total"] == 1
    assert order_flow["sell_trades_total"] == 1
    assert order_flow["unknown_trades_total"] == 1
    assert order_flow["total_volume"] == "0.16"
    assert order_flow["buy_volume"] == "0.08"
    assert order_flow["sell_volume"] == "0.03"
    assert order_flow["unknown_volume"] == "0.05"
    assert order_flow["signed_delta"] == "0.05"
    assert order_flow["unknown_volume_ratio"] == "0.3125"
    assert order_flow["classification_coverage"] == "0.6875"
    assert order_flow["confidence_weighted_coverage"] == "0.6875"
    assert cvd["points"][-1]["cvd"] == "0.05"
    assert audit["state_output_checksum"] == state["output_checksum"]
    assert audit["order_flow_checksum"] == order_flow["order_flow_checksum"]
    assert audit["cvd_checksum"] == cvd["cvd_checksum"]
    assert state["safety"]["trade_allowed"] is False
    assert state["safety"]["execution_allowed"] is False
    assert state["safety"]["approved_size"] == 0


def test_artifacts_reject_nonexistent_and_mismatched_code_commits() -> None:
    with pytest.raises(Lot45ValidationError, match="does not resolve"):
        build_lot45_artifacts(ROOT, "0" * 40)
    with pytest.raises(Lot45ValidationError, match="committed tree"):
        build_lot45_artifacts(ROOT, EXPECTED_GATE_MERGE)


def test_out_of_order_input_replays_identically() -> None:
    trades = (
        _classified("t3", "2026-08-06T19:18:40.900000Z", "2026-08-06T19:18:40.950000Z", "0.05", "UNKNOWN"),
        _classified("t1", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.300000Z", "0.08", "BUY_AGGRESSOR"),
        _classified("t2", "2026-08-06T19:18:40.200000Z", "2026-08-06T19:18:40.250000Z", "0.03", "SELL_AGGRESSOR"),
    )
    first_flow, first_cvd = build_order_flow(trades, _policy())
    second_flow, second_cvd = build_order_flow(tuple(reversed(trades)), _policy())
    assert first_flow.to_dict() == second_flow.to_dict()
    assert first_cvd.to_dict() == second_cvd.to_dict()


def test_unknown_volume_is_conserved_and_never_signed() -> None:
    trades = (
        _classified("buy", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "2", "BUY_AGGRESSOR"),
        _classified("sell", "2026-08-06T19:18:40.200000Z", "2026-08-06T19:18:40.210000Z", "1", "SELL_AGGRESSOR"),
        _classified("unknown", "2026-08-06T19:18:40.300000Z", "2026-08-06T19:18:40.310000Z", "7", "UNKNOWN"),
    )
    flow, cvd = build_order_flow(trades, _policy())
    assert flow.total_volume == Decimal("10")
    assert flow.unknown_volume == Decimal("7")
    assert flow.signed_delta == Decimal("1")
    assert cvd.points[-1].cvd == Decimal("1")
    assert flow.classification_coverage == Decimal("0.3")
    assert flow.confidence_weighted_coverage == Decimal("0.3")


def test_public_builder_enforces_unknown_volume_threshold() -> None:
    trades = (
        _classified("unknown", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "1", "UNKNOWN"),
    )
    with pytest.raises(Lot45ValidationError, match="unknown-volume ratio"):
        build_order_flow(trades, _policy(unknown_ratio="0"))


def test_multiple_windows_compute_delta_impulse_without_future_state() -> None:
    trades = (
        _classified("w1-buy", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "3", "BUY_AGGRESSOR"),
        _classified("w2-sell", "2026-08-06T19:18:41.100000Z", "2026-08-06T19:18:41.110000Z", "1", "SELL_AGGRESSOR"),
        _classified("w3-buy", "2026-08-06T19:18:42.100000Z", "2026-08-06T19:18:42.110000Z", "2", "BUY_AGGRESSOR"),
    )
    flow, cvd = build_order_flow(trades, _policy())
    assert [window.signed_delta for window in flow.windows] == [
        Decimal("3"),
        Decimal("-1"),
        Decimal("2"),
    ]
    assert [window.delta_impulse for window in flow.windows] == [
        Decimal("3"),
        Decimal("-4"),
        Decimal("3"),
    ]
    assert [point.cvd for point in cvd.points] == [
        Decimal("3"),
        Decimal("2"),
        Decimal("4"),
    ]


def test_cvd_resets_on_versioned_utc_day_session_boundary() -> None:
    trades = (
        _classified("day1", "2026-08-06T23:59:59.100000Z", "2026-08-06T23:59:59.110000Z", "2", "BUY_AGGRESSOR"),
        _classified("day2", "2026-08-07T00:00:00.100000Z", "2026-08-07T00:00:00.110000Z", "1", "SELL_AGGRESSOR"),
    )
    flow, cvd = build_order_flow(trades, _policy())
    assert [window.session_id for window in flow.windows] == ["2026-08-06", "2026-08-07"]
    assert [point.cvd for point in cvd.points] == [Decimal("2"), Decimal("-1")]
    assert [window.delta_impulse for window in flow.windows] == [Decimal("2"), Decimal("-1")]


def test_mixed_trade_identity_fails_closed() -> None:
    trades = (
        _classified("a", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "1", "BUY_AGGRESSOR"),
        _classified(
            "b",
            "2026-08-06T19:18:40.200000Z",
            "2026-08-06T19:18:40.210000Z",
            "1",
            "SELL_AGGRESSOR",
            instrument_id="ETH-USDT",
        ),
    )
    with pytest.raises(Lot45ValidationError, match="identity"):
        build_order_flow(trades, _policy())


def test_duplicate_trade_ids_fail_closed_in_public_builder() -> None:
    trades = (
        _classified("duplicate", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "1", "BUY_AGGRESSOR"),
        _classified("duplicate", "2026-08-06T19:18:40.200000Z", "2026-08-06T19:18:40.210000Z", "1", "SELL_AGGRESSOR"),
    )
    with pytest.raises(Lot45ValidationError, match="trade ids"):
        build_order_flow(trades, _policy())


def test_input_list_is_defensively_copied_by_order_flow() -> None:
    trades = [
        _classified("a", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "1", "BUY_AGGRESSOR"),
        _classified("b", "2026-08-06T19:18:40.200000Z", "2026-08-06T19:18:40.210000Z", "1", "SELL_AGGRESSOR"),
    ]
    flow, cvd = build_order_flow(trades, _policy())  # type: ignore[arg-type]
    flow_before = flow.to_dict()
    cvd_before = cvd.to_dict()
    trades.clear()
    assert flow.to_dict() == flow_before
    assert cvd.to_dict() == cvd_before


def test_cvd_model_rejects_invalid_recurrence() -> None:
    point = CVDPointV1(
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06",
        QUOTE_SHA256,
        Decimal("1"),
        Decimal("1"),
    )
    second = CVDPointV1(
        "2026-08-06T19:18:41.100000Z",
        "2026-08-06",
        "2" * 64,
        Decimal("1"),
        Decimal("99"),
    )
    with pytest.raises(Lot45ValidationError, match="recurrence"):
        CVDSeriesV1(SESSION_POLICY_VERSION, (point, second), "3" * 64)


def test_signed_decimal_zero_serializes_canonically() -> None:
    assert decimal_text(Decimal("-0")) == "0"


def test_policy_rejects_unknown_ratio_outside_unit_interval() -> None:
    with pytest.raises(Lot45ValidationError, match="max_unknown_volume_ratio"):
        _policy(unknown_ratio="1.1")


def test_trade_timestamp_future_receive_is_rejected_upstream() -> None:
    with pytest.raises(RuntimeError, match="causal"):
        TimestampedTradeV1(
            "source-a",
            "venue-a",
            "BTC-USDT",
            "SPOT",
            "bad",
            "2026-08-06T19:18:41.000000Z",
            "2026-08-06T19:18:40.000000Z",
            Decimal("100"),
            Decimal("1"),
            "UNKNOWN",
        )


def test_repeating_ratios_use_deterministic_precision() -> None:
    trades = (
        _classified("a", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "1", "BUY_AGGRESSOR"),
        _classified("b", "2026-08-06T19:18:40.200000Z", "2026-08-06T19:18:40.210000Z", "2", "UNKNOWN"),
    )
    first, _ = build_order_flow(trades, _policy())
    second, _ = build_order_flow(tuple(reversed(trades)), _policy())
    assert first.classification_coverage == second.classification_coverage
    assert first.to_dict() == second.to_dict()


def test_window_model_rejects_every_derived_invariant_drift() -> None:
    trades = (
        _classified("buy", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "1", "BUY_AGGRESSOR"),
        _classified("unknown", "2026-08-06T19:18:40.200000Z", "2026-08-06T19:18:40.210000Z", "1", "UNKNOWN"),
    )
    flow, _ = build_order_flow(trades, _policy())
    window = flow.windows[0]

    cases = (
        ({"window_start": window.window_end}, "window_start must precede"),
        ({"event_time": window.window_end}, "inside event-time window"),
        ({"receive_time": "2026-08-06T19:18:40.050000Z"}, "precedes event_time"),
        ({"session_id": ""}, "non-empty text"),
        ({"trades_total": 0}, "cannot be empty"),
        ({"buy_trades_total": window.buy_trades_total + 1}, "trade count conservation"),
        ({"total_volume": Decimal("-1")}, "finite non-negative"),
        ({"total_volume": window.total_volume + Decimal("1")}, "volume conservation"),
        ({"signed_delta": window.signed_delta + Decimal("1")}, "buy minus sell"),
        ({"signed_imbalance": window.signed_imbalance + Decimal("0.1")}, "signed imbalance mismatch"),
        ({"classification_coverage": window.classification_coverage + Decimal("0.1")}, "classification coverage mismatch"),
        ({"confidence_weighted_coverage": Decimal("0.75")}, "weighted confidence"),
        ({"delta_impulse": Decimal("NaN")}, "delta impulse must be finite"),
    )
    for changes, message in cases:
        with pytest.raises(Lot45ValidationError, match=message):
            replace(window, **changes)


def test_flow_model_rejects_sequence_and_aggregate_drift() -> None:
    trades = (
        _classified("first", "2026-08-06T19:18:40.100000Z", "2026-08-06T19:18:40.110000Z", "2", "BUY_AGGRESSOR"),
        _classified("second", "2026-08-06T19:18:41.100000Z", "2026-08-06T19:18:41.110000Z", "1", "SELL_AGGRESSOR"),
    )
    flow, _ = build_order_flow(trades, _policy())
    first, second = flow.windows

    with pytest.raises(Lot45ValidationError, match="event-time ordered"):
        replace(flow, windows=(second, first))
    with pytest.raises(Lot45ValidationError, match="must be unique"):
        replace(flow, windows=(first, first))
    bad_impulse = replace(second, delta_impulse=second.delta_impulse + Decimal("1"))
    with pytest.raises(Lot45ValidationError, match="delta impulse mismatch"):
        replace(flow, windows=(first, bad_impulse))

    aggregate_cases = (
        ({"trades_total": flow.trades_total + 1}, "trades_total aggregate mismatch"),
        ({"buy_trades_total": flow.buy_trades_total + 1}, "buy_trades_total aggregate mismatch"),
        ({"total_volume": flow.total_volume + Decimal("1")}, "total_volume aggregate mismatch"),
        ({"signed_delta": flow.signed_delta + Decimal("1")}, "aggregate delta mismatch"),
        ({"unknown_volume_ratio": Decimal("0.1")}, "unknown volume ratio mismatch"),
        ({"classification_coverage": Decimal("0.9")}, "aggregate coverage mismatch"),
        ({"confidence_weighted_coverage": Decimal("0.9")}, "aggregate weighted coverage mismatch"),
    )
    for changes, message in aggregate_cases:
        with pytest.raises(Lot45ValidationError, match=message):
            replace(flow, **changes)


def test_cvd_series_rejects_empty_order_duplicate_and_session_reset_drift() -> None:
    trades = (
        _classified("first", "2026-08-06T23:59:59.100000Z", "2026-08-06T23:59:59.110000Z", "2", "BUY_AGGRESSOR"),
        _classified("second", "2026-08-07T00:00:00.100000Z", "2026-08-07T00:00:00.110000Z", "1", "SELL_AGGRESSOR"),
    )
    _, cvd = build_order_flow(trades, _policy())
    first, second = cvd.points

    with pytest.raises(Lot45ValidationError, match="cannot be empty"):
        CVDSeriesV1(SESSION_POLICY_VERSION, (), cvd.cvd_checksum)
    with pytest.raises(Lot45ValidationError, match="event-time ordered"):
        CVDSeriesV1(SESSION_POLICY_VERSION, (second, first), cvd.cvd_checksum)
    duplicate_time = replace(second, event_time=first.event_time)
    with pytest.raises(Lot45ValidationError, match="event times must be unique"):
        CVDSeriesV1(SESSION_POLICY_VERSION, (first, duplicate_time), cvd.cvd_checksum)
    wrong_reset = replace(second, cvd=first.cvd + second.signed_delta)
    with pytest.raises(Lot45ValidationError, match="recurrence"):
        CVDSeriesV1(SESSION_POLICY_VERSION, (first, wrong_reset), cvd.cvd_checksum)
