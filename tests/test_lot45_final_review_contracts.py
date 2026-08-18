from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    OrderFlowPolicy,
    _build_engine_audit,
    _build_engine_state,
    _verify_lot44_temporal,
    build_lot45_artifacts,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_models import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_LOT44_AUDIT,
    EXPECTED_LOT44_CONFIDENCE,
    EXPECTED_LOT44_POST_MERGE,
    EXPECTED_LOT44_STATE,
    OrderFlowDeltaCVDEngineAuditV1,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
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
from scripts.validate_lot45 import (
    _load_schema_documents,
    _validate_generated_payloads,
    _validate_schema_files,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO_SHA256 = "0" * 64
REFERENCE_CODE_TREE_SHA = "b807dec04368320f92e816248ac9039d94c1b529"


def _audit_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "code_commit": "a" * 40,
        "state_output_checksum": "1" * 64,
        "config_checksum": "4" * 64,
        "entry_gate_checksum": EXPECTED_GATE_CHECKSUM,
        "lot44_state_checksum": EXPECTED_LOT44_STATE,
        "lot44_audit_checksum": EXPECTED_LOT44_AUDIT,
        "lot44_confidence_checksum": EXPECTED_LOT44_CONFIDENCE,
        "lot44_post_merge_checksum": EXPECTED_LOT44_POST_MERGE,
        "order_flow_checksum": "2" * 64,
        "cvd_checksum": "3" * 64,
        "validation_state": VALIDATION_STATE,
        "safety": lot45_safety(),
    }
    payload = {
        "schema_version": "order-flow-delta-cvd-engine-audit-v1",
        **kwargs,
    }
    kwargs["audit_checksum"] = canonical_checksum(payload)
    return kwargs


def _canonical_payloads() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return build_lot45_artifacts(ROOT, REFERENCE_CODE_TREE_SHA)


def _policy(max_unknown_ratio: str = "1") -> OrderFlowPolicy:
    return OrderFlowPolicy(
        50,
        1_000_000,
        2_000_000,
        Decimal(max_unknown_ratio),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def _classified(trade_id: str, quantity: str, classification: str) -> ClassifiedTradeV1:
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
        classification,
        "QUOTE_TEST",
        Decimal("1"),
        "lot44-aggressor-confidence-v1",
        "1" * 64,
        ("QUOTE_REFERENCE",),
    )


def _state_config(generated_at: str) -> dict[str, Any]:
    return {
        "run_id": "lot45-final-review-state",
        "correlation_id": "lot45-final-review-state",
        "lineage_id": "lot45-from-certified-lot44-order-flow-inputs-v1",
        "generated_at": generated_at,
    }


def _state44(receive_time: str, generated_at: str) -> dict[str, Any]:
    return {
        "receive_time": receive_time,
        "generated_at": generated_at,
    }


def test_standalone_audit_accepts_exact_certified_upstream_hashes() -> None:
    audit = OrderFlowDeltaCVDEngineAuditV1(**_audit_kwargs())
    assert audit.audit_checksum != ZERO_SHA256
    assert audit.config_checksum == "4" * 64


def test_standalone_audit_rejects_zero_checksum_sentinel() -> None:
    kwargs = _audit_kwargs()
    kwargs["audit_checksum"] = ZERO_SHA256
    with pytest.raises(Lot45ValidationError, match="audit_checksum zero sentinel"):
        OrderFlowDeltaCVDEngineAuditV1(**kwargs)


@pytest.mark.parametrize(
    "field",
    (
        "entry_gate_checksum",
        "lot44_state_checksum",
        "lot44_audit_checksum",
        "lot44_confidence_checksum",
        "lot44_post_merge_checksum",
    ),
)
def test_standalone_audit_rejects_valid_shape_but_uncertified_upstream_hash(field: str) -> None:
    kwargs = _audit_kwargs()
    kwargs[field] = "f" * 64
    with pytest.raises(Lot45ValidationError, match=f"{field} certified value changed"):
        OrderFlowDeltaCVDEngineAuditV1(**kwargs)


def test_generated_payload_schema_gate_accepts_canonical_artifacts() -> None:
    schemas = _load_schema_documents()
    _validate_schema_files(schemas)
    _validate_generated_payloads(schemas, *_canonical_payloads())


def test_generated_payload_schema_gate_rejects_nested_violation() -> None:
    state, audit, order_flow, cvd = _canonical_payloads()
    state["order_flow"]["windows"][0]["classification_coverage"] = "garbage"
    schemas = _load_schema_documents()
    _validate_schema_files(schemas)
    with pytest.raises(
        Lot45ValidationError,
        match=r"Lot45 state payload violates schema at order_flow\.windows\.0\.classification_coverage",
    ):
        _validate_generated_payloads(schemas, state, audit, order_flow, cvd)


def test_reconstructed_flow_enforces_certified_unknown_volume_limit() -> None:
    flow, _ = build_order_flow(
        (
            _classified("buy", "1", "BUY_AGGRESSOR"),
            _classified("unknown", "2", "UNKNOWN"),
        ),
        _policy("1"),
    )
    assert flow.unknown_volume_ratio > Decimal("0.5")
    with pytest.raises(Lot45ValidationError, match="unknown volume ratio exceeds Lot45 policy limit"):
        replace(flow)


def test_reconstructed_state_enforces_certified_input_age_limit() -> None:
    trades = (_classified("buy", "1", "BUY_AGGRESSOR"),)
    flow, cvd = build_order_flow(trades, _policy())
    with pytest.raises(Lot45ValidationError, match="lineage input age exceeds policy limit"):
        _build_engine_state(
            _state_config("2026-08-06T19:18:50.000000Z"),
            "a" * 40,
            _state44(
                "2026-08-06T19:18:40.110000Z",
                "2026-08-06T19:18:40.110000Z",
            ),
            trades,
            flow,
            cvd,
        )


def test_reconstructed_state_rejects_lineage_available_before_latest_receive() -> None:
    trades = (_classified("buy", "1", "BUY_AGGRESSOR"),)
    flow, cvd = build_order_flow(trades, _policy())
    with pytest.raises(
        Lot45ValidationError,
        match="lineage available_at cannot precede latest source receive_time",
    ):
        _build_engine_state(
            _state_config("2026-08-06T19:18:41.100000Z"),
            "a" * 40,
            _state44(
                "2026-08-06T19:18:40.050000Z",
                "2026-08-06T19:18:40.050000Z",
            ),
            trades,
            flow,
            cvd,
        )


def test_reconstructed_state_allows_lineage_available_at_latest_receive() -> None:
    trades = (_classified("buy", "1", "BUY_AGGRESSOR"),)
    flow, cvd = build_order_flow(trades, _policy())
    state = _build_engine_state(
        _state_config("2026-08-06T19:18:41.100000Z"),
        "a" * 40,
        _state44(
            "2026-08-06T19:18:40.110000Z",
            "2026-08-06T19:18:40.110000Z",
        ),
        trades,
        flow,
        cvd,
    )
    assert state.lineage.available_at == state.receive_time


def test_lineage_availability_uses_upstream_generated_at() -> None:
    trades = (_classified("buy", "1", "BUY_AGGRESSOR"),)
    flow, cvd = build_order_flow(trades, _policy())
    state = _build_engine_state(
        _state_config("2026-08-06T19:18:41.100000Z"),
        "a" * 40,
        _state44(
            "2026-08-06T19:18:40.110000Z",
            "2026-08-06T19:18:41.000000Z",
        ),
        trades,
        flow,
        cvd,
    )
    assert state.lineage.available_at == "2026-08-06T19:18:41.000000Z"
    assert state.lineage.available_at != state.receive_time


def test_lot44_temporal_rejects_generation_before_receive() -> None:
    state44 = json.loads(
        (ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json").read_text(
            encoding="utf-8"
        )
    )
    state44["generated_at"] = "2026-08-06T19:18:40.040000Z"
    with pytest.raises(Lot45ValidationError, match="causal|generated|receive"):
        _verify_lot44_temporal(
            state44,
            {"generated_at": "2026-08-06T19:18:41.100000Z"},
            _policy("1"),
        )


def test_lot44_freshness_is_measured_from_upstream_generation() -> None:
    state44 = json.loads(
        (ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json").read_text(
            encoding="utf-8"
        )
    )
    with pytest.raises(Lot45ValidationError, match="Lot44 input is stale for Lot45"):
        _verify_lot44_temporal(
            state44,
            {"generated_at": "2026-08-06T19:18:43.100000Z"},
            _policy("1"),
        )


def test_every_published_zero_checksum_sentinel_is_rejected() -> None:
    trades = (_classified("buy", "1", "BUY_AGGRESSOR"),)
    flow, cvd = build_order_flow(trades, _policy())
    config = _state_config("2026-08-06T19:18:41.000000Z")
    state = _build_engine_state(
        config,
        "a" * 40,
        _state44(
            "2026-08-06T19:18:40.110000Z",
            "2026-08-06T19:18:40.110000Z",
        ),
        trades,
        flow,
        cvd,
    )
    audit = _build_engine_audit(config, "a" * 40, state, flow, cvd)

    cases = (
        (lambda: replace(flow.windows[0], window_checksum=ZERO_SHA256), "window_checksum zero sentinel"),
        (lambda: replace(flow, order_flow_checksum=ZERO_SHA256), "order_flow_checksum zero sentinel"),
        (lambda: replace(cvd, cvd_checksum=ZERO_SHA256), "cvd_checksum zero sentinel"),
        (lambda: replace(state, output_checksum=ZERO_SHA256), "output_checksum zero sentinel"),
        (lambda: replace(audit, audit_checksum=ZERO_SHA256), "audit_checksum zero sentinel"),
    )
    for build, message in cases:
        with pytest.raises(Lot45ValidationError, match=message):
            build()
