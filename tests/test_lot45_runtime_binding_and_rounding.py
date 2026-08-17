from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal, localcontext

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    CALCULATION_DECIMAL_ROUNDING,
    CODE_BOUND_PATHS,
    OrderFlowPolicy,
    build_order_flow,
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_models import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_GATE_MERGE,
    EXPECTED_LOT44_AUDIT,
    EXPECTED_LOT44_CONFIDENCE,
    EXPECTED_LOT44_CONFIG,
    EXPECTED_LOT44_POST_MERGE,
    EXPECTED_LOT44_STATE,
    CVDPointV1,
    CVDSeriesV1,
    Lot45LineageEnvelopeV1,
    Lot45RunContextV1,
    OrderFlowDeltaCVDEngineStateV1,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    CONFIG_VERSION,
    POLICY_VERSION,
    RUNTIME_MODE,
    SESSION_POLICY_VERSION,
    VALIDATION_STATE,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    decimal_from_text,
    duration_us,
    event_window_bounds,
    lot45_safety,
    parse_utc_timestamp,
    require_git_sha,
    require_integer,
    require_sha256,
    session_id_for_event,
    validate_ratio,
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


@pytest.mark.parametrize("window_size_us", (500_000, 2_000_000))
def test_policy_rejects_non_certified_window_size(window_size_us: int) -> None:
    with pytest.raises(Lot45ValidationError, match="window size changed"):
        OrderFlowPolicy(
            50,
            window_size_us,
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
        _classified("buy", "2", "BUY_AGGRESSOR"),
        _classified("unknown", "1", "UNKNOWN"),
    )
    return build_order_flow(trades, _policy())


def _two_window_flow():
    trades = (
        _classified(
            "first-buy",
            "2",
            "BUY_AGGRESSOR",
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
        _classified(
            "second-buy",
            "1",
            "BUY_AGGRESSOR",
            event_time="2026-08-06T19:18:41.100000Z",
            receive_time="2026-08-06T19:18:41.110000Z",
        ),
    )
    return build_order_flow(trades, _policy())


def _lineage() -> Lot45LineageEnvelopeV1:
    return Lot45LineageEnvelopeV1(
        "test-lineage",
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_GATE_MERGE,
        EXPECTED_LOT44_STATE,
        EXPECTED_LOT44_AUDIT,
        EXPECTED_LOT44_CONFIDENCE,
        EXPECTED_LOT44_CONFIG,
        EXPECTED_LOT44_POST_MERGE,
        "2026-08-06T19:18:40.110000Z",
    )


def _state(flow, cvd) -> OrderFlowDeltaCVDEngineStateV1:
    latest_window = flow.windows[-1]
    run_context = Lot45RunContextV1(
        "test-run",
        RUNTIME_MODE,
        CONFIG_VERSION,
        "a" * 40,
        "test-correlation",
    )
    lineage = _lineage()
    generated_at = "2026-08-06T19:18:42.000000Z"
    reason_codes = ("TEST_STATE",)
    safety = lot45_safety()
    payload = {
        "schema_version": "order-flow-delta-cvd-engine-state-v1",
        "run_context": run_context.to_dict(),
        "lineage": lineage.to_dict(),
        "event_time": latest_window.event_time,
        "receive_time": latest_window.receive_time,
        "generated_at": generated_at,
        "validation_state": VALIDATION_STATE,
        "policy_version": POLICY_VERSION,
        "window_policy_version": WINDOW_POLICY_VERSION,
        "session_policy_version": SESSION_POLICY_VERSION,
        "order_flow": flow.to_dict(),
        "cvd_series": cvd.to_dict(),
        "reason_codes": list(reason_codes),
        "safety": safety,
    }
    return OrderFlowDeltaCVDEngineStateV1(
        run_context,
        lineage,
        latest_window.event_time,
        latest_window.receive_time,
        generated_at,
        VALIDATION_STATE,
        POLICY_VERSION,
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        flow,
        cvd,
        reason_codes,
        safety,
        canonical_checksum(payload),
    )


def _cvd_series(points: tuple[CVDPointV1, ...]) -> CVDSeriesV1:
    payload = {
        "schema_version": "cvd-series-v1",
        "session_policy_version": SESSION_POLICY_VERSION,
        "points": [point.to_dict() for point in points],
    }
    return CVDSeriesV1(
        SESSION_POLICY_VERSION,
        points,
        canonical_checksum(payload),
    )


def test_repeating_ratios_ignore_ambient_decimal_rounding() -> None:
    trades = (
        _classified("buy", "2", "BUY_AGGRESSOR"),
        _classified("unknown", "1", "UNKNOWN"),
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
    forged_cvd = _cvd_series((forged_point,))
    window = flow.windows[0]

    with pytest.raises(Lot45ValidationError, match="CVD point signed delta mismatch"):
        _state(flow, forged_cvd)
    assert window.signed_delta != forged_point.signed_delta


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"buy_volume": Decimal("-1")}, "buy_volume must be finite non-negative"),
        ({"sell_volume": Decimal("-1")}, "sell_volume must be finite non-negative"),
        ({"unknown_volume": Decimal("-1")}, "unknown_volume must be finite non-negative"),
        (
            {"confidence_weighted_volume": Decimal("-1")},
            "confidence_weighted_volume must be finite non-negative",
        ),
        (
            {"confidence_weighted_volume": Decimal("2")},
            "confidence-weighted volume cannot exceed classified volume",
        ),
        ({"buy_volume": Decimal("NaN")}, "buy_volume must be finite non-negative"),
    ),
)
def test_window_volume_and_weighted_volume_guards_fail_closed(
    changes: dict[str, Decimal],
    message: str,
) -> None:
    flow, _ = _repeating_ratio_flow()
    with pytest.raises(Lot45ValidationError, match=message):
        replace(flow.windows[0], **changes)


def test_window_time_guards_reject_reverse_and_pre_window_events() -> None:
    flow, _ = _repeating_ratio_flow()
    window = flow.windows[0]
    with pytest.raises(Lot45ValidationError, match="window_start must precede window_end"):
        replace(
            window,
            window_start="2026-08-06T19:18:40.900000Z",
            window_end="2026-08-06T19:18:40.800000Z",
        )
    with pytest.raises(Lot45ValidationError, match="inside event-time window"):
        replace(window, window_start="2026-08-06T19:18:40.200000Z")


def test_flow_rejects_raw_weighted_volume_aggregate_drift() -> None:
    flow, _ = _two_window_flow()
    with pytest.raises(Lot45ValidationError, match="confidence_weighted_volume aggregate mismatch"):
        replace(
            flow,
            confidence_weighted_volume=flow.confidence_weighted_volume + Decimal("1"),
        )


def test_engine_state_binding_rejects_length_checksum_and_event_time_drift() -> None:
    flow, cvd = _repeating_ratio_flow()
    point = cvd.points[0]

    checksum_drift = _cvd_series(
        (replace(point, window_checksum="2" * 64),),
    )
    with pytest.raises(Lot45ValidationError, match="CVD point window checksum mismatch"):
        _state(flow, checksum_drift)

    event_drift = _cvd_series(
        (replace(point, event_time="2026-08-06T19:18:40.150000Z"),),
    )
    with pytest.raises(Lot45ValidationError, match="CVD point event_time mismatch"):
        _state(flow, event_drift)

    extra_point = CVDPointV1(
        "2026-08-06T19:18:40.200000Z",
        "2026-08-06",
        "3" * 64,
        Decimal("0"),
        point.cvd,
    )
    length_drift = _cvd_series((point, extra_point))
    with pytest.raises(Lot45ValidationError, match="one-to-one"):
        _state(flow, length_drift)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("validation_state", "BROKEN", "Lot45 validation state changed"),
        ("policy_version", "broken-policy", "Lot45 policy version changed"),
        ("window_policy_version", "broken-window", "Lot45 window policy changed"),
        ("session_policy_version", "broken-session", "Lot45 session policy changed"),
    ),
)
def test_engine_state_rejects_every_version_drift(
    field: str,
    value: str,
    message: str,
) -> None:
    flow, cvd = _two_window_flow()
    state = _state(flow, cvd)
    with pytest.raises(Lot45ValidationError, match=message):
        replace(state, **{field: value})


def test_engine_state_rejects_event_and_receive_envelope_drift() -> None:
    flow, cvd = _two_window_flow()
    state = _state(flow, cvd)
    with pytest.raises(Lot45ValidationError, match="latest source event"):
        replace(state, event_time=flow.windows[0].event_time)
    with pytest.raises(Lot45ValidationError, match="latest source receive time"):
        replace(state, receive_time="2026-08-06T19:18:41.105000Z")


def test_engine_state_rejects_future_lineage_availability() -> None:
    flow, cvd = _two_window_flow()
    state = _state(flow, cvd)
    future_lineage = replace(
        state.lineage,
        available_at="2026-08-06T19:18:43.000000Z",
    )
    with pytest.raises(Lot45ValidationError, match="available_at cannot exceed generated_at"):
        replace(state, lineage=future_lineage, output_checksum=ZERO_SHA256)


@pytest.mark.parametrize(
    "field",
    (
        "entry_gate_checksum",
        "lot44_state_checksum",
        "lot44_audit_checksum",
        "lot44_confidence_checksum",
        "lot44_config_checksum",
        "lot44_post_merge_checksum",
    ),
)
def test_lineage_rejects_each_invalid_checksum(field: str) -> None:
    lineage = _lineage()
    with pytest.raises(Lot45ValidationError, match="lowercase sha256"):
        replace(lineage, **{field: "g" * 64})


@pytest.mark.parametrize(
    "field",
    (
        "entry_gate_checksum",
        "lot44_state_checksum",
        "lot44_audit_checksum",
        "lot44_confidence_checksum",
        "lot44_config_checksum",
        "lot44_post_merge_checksum",
    ),
)
def test_lineage_rejects_well_formed_but_uncertified_checksum(field: str) -> None:
    lineage = _lineage()
    with pytest.raises(Lot45ValidationError, match="certified value changed"):
        replace(lineage, **{field: "f" * 64})


def test_lineage_rejects_well_formed_but_uncertified_gate_commit() -> None:
    lineage = _lineage()
    with pytest.raises(Lot45ValidationError, match="certified value changed"):
        replace(lineage, entry_gate_merge_commit="a" * 40)


def test_run_context_rejects_each_identity_drift() -> None:
    with pytest.raises(Lot45ValidationError, match="run_id"):
        Lot45RunContextV1("", RUNTIME_MODE, CONFIG_VERSION, "a" * 40, "correlation")
    with pytest.raises(Lot45ValidationError, match="runtime mode"):
        Lot45RunContextV1("run", "LIVE", CONFIG_VERSION, "a" * 40, "correlation")
    with pytest.raises(Lot45ValidationError, match="config version"):
        Lot45RunContextV1("run", RUNTIME_MODE, "broken", "a" * 40, "correlation")
    with pytest.raises(Lot45ValidationError, match="git sha"):
        Lot45RunContextV1("run", RUNTIME_MODE, CONFIG_VERSION, "bad", "correlation")
    with pytest.raises(Lot45ValidationError, match="correlation_id"):
        Lot45RunContextV1("run", RUNTIME_MODE, CONFIG_VERSION, "a" * 40, "")


def test_validation_primitives_enforce_fail_closed_boundaries() -> None:
    with pytest.raises(Lot45ValidationError, match="must be integer"):
        require_integer(True, "value")
    with pytest.raises(Lot45ValidationError, match=">= 0"):
        require_integer(-1, "value")
    with pytest.raises(Lot45ValidationError, match="lowercase sha256"):
        require_sha256("A" * 64, "checksum")
    with pytest.raises(Lot45ValidationError, match="lowercase sha256"):
        require_sha256("0" * 63, "checksum")
    with pytest.raises(Lot45ValidationError, match="git sha"):
        require_git_sha("A" * 40, "commit")
    with pytest.raises(Lot45ValidationError, match="git sha"):
        require_git_sha("0" * 39, "commit")
    with pytest.raises(Lot45ValidationError, match="decimal text"):
        decimal_from_text(1, "decimal")
    with pytest.raises(Lot45ValidationError, match="invalid decimal"):
        decimal_from_text("not-a-decimal", "decimal")
    with pytest.raises(Lot45ValidationError, match="must be finite"):
        decimal_from_text("NaN", "decimal")
    with pytest.raises(Lot45ValidationError, match="non-negative"):
        decimal_from_text("-1", "decimal")
    with pytest.raises(Lot45ValidationError, match="UTC Z suffix"):
        parse_utc_timestamp("2026-08-06T19:18:40+00:00", "timestamp")
    with pytest.raises(Lot45ValidationError, match="duration cannot be negative"):
        duration_us("2026-08-06T19:18:41.000000Z", "2026-08-06T19:18:40.000000Z")
    assert duration_us(
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.123456Z",
    ) == 123456
    assert event_window_bounds(
        "2026-08-06T19:18:40.123456Z",
        1_000_000,
    ) == (
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:41.000000Z",
    )
    with pytest.raises(Lot45ValidationError, match="session policy version"):
        session_id_for_event("2026-08-06T19:18:40.000000Z", "broken")
    assert session_id_for_event(
        "2026-08-06T19:18:40.000000Z",
        SESSION_POLICY_VERSION,
    ) == "2026-08-06"
    with pytest.raises(Lot45ValidationError, match="must be finite"):
        validate_ratio(Decimal("NaN"), "ratio")
    with pytest.raises(Lot45ValidationError, match="outside"):
        validate_ratio(Decimal("-0.1"), "ratio")
    with pytest.raises(Lot45ValidationError, match="outside"):
        validate_ratio(Decimal("1.1"), "ratio")


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
