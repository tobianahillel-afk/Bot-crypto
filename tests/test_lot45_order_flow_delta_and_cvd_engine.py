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
REFERENCE_CODE_TREE_SHA = "c22c7bcd81c511a3ee5cd4a27b2249ce4e9d45b5"


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
    with pytest.raises(Lot45ValidationError, match="differs from code_commit"):
        build_lot45_artifacts(ROOT, EXPECTED_GATE_MERGE)


def test_runtime_dependency_drift_is_bound_to_code_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    import crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine as engine

    original_run_git = engine._run_git

    def fake_run_git(root: Path, *args: str):
        if args and args[0] == "diff" and "src/crypto_quant_bot/data_governance/source_registry_validation.py" in args:
            class Result:
                returncode = 1
                stdout = ""
                stderr = ""

            return Result()
        return original_run_git(root, *args)

    monkeypatch.setattr(engine, "_run_git", fake_run_git)
    with pytest.raises(Lot45ValidationError, match="differs from code_commit"):
        build_lot45_artifacts(ROOT, REFERENCE_CODE_TREE_SHA)


def test_mixed_trade_identity_fails_closed() -> None:
    first = _classified(
        "trade-1",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.200000Z",
        "1",
        "BUY_AGGRESSOR",
    )
    second = _classified(
        "trade-2",
        "2026-08-06T19:18:40.300000Z",
        "2026-08-06T19:18:40.400000Z",
        "1",
        "SELL_AGGRESSOR",
        venue="venue-b",
    )
    with pytest.raises(Lot45ValidationError, match="identity"):
        build_order_flow((first, second), _policy())


def test_duplicate_trade_ids_fail_closed() -> None:
    first = _classified(
        "duplicate",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.200000Z",
        "1",
        "BUY_AGGRESSOR",
    )
    second = _classified(
        "duplicate",
        "2026-08-06T19:18:40.300000Z",
        "2026-08-06T19:18:40.400000Z",
        "1",
        "SELL_AGGRESSOR",
    )
    with pytest.raises(Lot45ValidationError, match="trade ids"):
        build_order_flow((first, second), _policy())


def test_unknown_volume_threshold_fails_closed() -> None:
    unknown = _classified(
        "unknown",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.200000Z",
        "1",
        "UNKNOWN",
    )
    with pytest.raises(Lot45ValidationError, match="unknown-volume ratio"):
        build_order_flow((unknown,), _policy(unknown_ratio="0"))


def test_window_model_invariants_fail_closed() -> None:
    trade = _classified(
        "trade-1",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.200000Z",
        "1",
        "BUY_AGGRESSOR",
    )
    order_flow, _ = build_order_flow((trade,), _policy())
    window = order_flow.windows[0]
    for mutation in (
        {"window_end": window.window_start},
        {"trades_total": 0},
        {"buy_trades_total": window.trades_total + 1},
        {"total_volume": Decimal("2")},
        {"signed_delta": Decimal("0")},
        {"signed_imbalance": Decimal("0")},
        {"classification_coverage": Decimal("0")},
        {"confidence_weighted_coverage": Decimal("0")},
        {"window_checksum": "f" * 64},
    ):
        with pytest.raises((RuntimeError, ValueError)):
            replace(window, **mutation)


def test_order_flow_aggregate_invariants_fail_closed() -> None:
    trades = (
        _classified(
            "trade-1",
            "2026-08-06T19:18:40.100000Z",
            "2026-08-06T19:18:40.200000Z",
            "1",
            "BUY_AGGRESSOR",
        ),
        _classified(
            "trade-2",
            "2026-08-06T19:18:40.300000Z",
            "2026-08-06T19:18:40.400000Z",
            "1",
            "SELL_AGGRESSOR",
        ),
    )
    order_flow, _ = build_order_flow(trades, _policy())
    for mutation in (
        {"trades_total": 0},
        {"buy_trades_total": 3},
        {"total_volume": Decimal("3")},
        {"signed_delta": Decimal("1")},
        {"unknown_volume_ratio": Decimal("1")},
        {"classification_coverage": Decimal("0")},
        {"confidence_weighted_coverage": Decimal("0")},
        {"order_flow_checksum": "f" * 64},
    ):
        with pytest.raises((RuntimeError, ValueError)):
            replace(order_flow, **mutation)


def test_cvd_invariants_fail_closed() -> None:
    trade = _classified(
        "trade-1",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.200000Z",
        "1",
        "BUY_AGGRESSOR",
    )
    _, cvd = build_order_flow((trade,), _policy())
    point = cvd.points[0]
    for mutation in (
        {"window_checksum": "f" * 64},
        {"signed_delta": Decimal("0")},
        {"cvd": Decimal("0")},
    ):
        with pytest.raises((RuntimeError, ValueError)):
            replace(point, **mutation)
    with pytest.raises((RuntimeError, ValueError)):
        replace(cvd, cvd_checksum="f" * 64)


def test_decimal_text_contract() -> None:
    assert decimal_text(Decimal("0.000")) == "0"
    assert decimal_text(Decimal("1.2300")) == "1.23"
    assert decimal_text(Decimal("-0.5000")) == "-0.5"
