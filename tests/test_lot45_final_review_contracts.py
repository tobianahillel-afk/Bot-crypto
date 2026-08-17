from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_models import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_LOT44_AUDIT,
    EXPECTED_LOT44_CONFIDENCE,
    EXPECTED_LOT44_CONFIG,
    EXPECTED_LOT44_POST_MERGE,
    EXPECTED_LOT44_STATE,
    OrderFlowDeltaCVDEngineAuditV1,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    VALIDATION_STATE,
    Lot45ValidationError,
    lot45_safety,
)
from scripts.validate_lot45 import (
    _load_schema_documents,
    _validate_generated_payloads,
    _validate_schema_files,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO_SHA256 = "0" * 64


def _audit_kwargs() -> dict[str, Any]:
    return {
        "code_commit": "a" * 40,
        "state_output_checksum": "1" * 64,
        "config_checksum": EXPECTED_LOT44_CONFIG,
        "entry_gate_checksum": EXPECTED_GATE_CHECKSUM,
        "lot44_state_checksum": EXPECTED_LOT44_STATE,
        "lot44_audit_checksum": EXPECTED_LOT44_AUDIT,
        "lot44_confidence_checksum": EXPECTED_LOT44_CONFIDENCE,
        "lot44_post_merge_checksum": EXPECTED_LOT44_POST_MERGE,
        "order_flow_checksum": "2" * 64,
        "cvd_checksum": "3" * 64,
        "validation_state": VALIDATION_STATE,
        "safety": lot45_safety(),
        "audit_checksum": ZERO_SHA256,
    }


def _canonical_payloads() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    paths = (
        ROOT / "data/audit/order_flow_delta_and_cvd_engine_lot45.json",
        ROOT / "data/audit/order_flow_delta_and_cvd_engine_audit_lot45.json",
        ROOT / "data/audit/order_flow_state_lot45.json",
        ROOT / "data/audit/cvd_series_lot45.json",
    )
    return tuple(json.loads(path.read_text(encoding="utf-8")) for path in paths)  # type: ignore[return-value]


def test_standalone_audit_accepts_exact_certified_upstream_hashes() -> None:
    audit = OrderFlowDeltaCVDEngineAuditV1(**_audit_kwargs())
    assert audit.audit_checksum != ZERO_SHA256


@pytest.mark.parametrize(
    "field",
    (
        "config_checksum",
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
