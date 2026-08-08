from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_lot35_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    Lot35EntryGateError,
    canonical_checksum,
    validate,
    validate_gate_checksum,
    validate_scope_quality_and_safety,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot35_v3_entry_gate.json"


def load_gate() -> dict[str, object]:
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot35_entry_gate_validator_passes() -> None:
    assert validate() == {
        "schema_version": "lot35-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT35_IMPLEMENTATION_ENTRY",
        "output_checksum": EXPECTED_GATE_CHECKSUM,
        "next_locked_lot": 36,
        "external_connectivity_allowed": False,
        "raw_data_mutation_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def test_lot35_gate_checksum_recomputes() -> None:
    gate = load_gate()
    checksum = gate.pop("output_checksum")
    assert checksum == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(gate) == checksum


def test_lot35_gate_scope_is_reconciliation_only() -> None:
    gate = load_gate()
    allowed = set(gate["allowed_scope"])
    assert "EXACT_DELTA_COMPUTATION" in allowed
    assert "VERSIONED_TOLERANCE_EVALUATION" in allowed
    assert "SOURCE_OF_TRUTH_RESOLUTION" in allowed
    assert "RECONCILIATION_VETO" in allowed
    forbidden = set(gate["forbidden_scope"])
    assert "EXTERNAL_NETWORK_ACCESS" in forbidden
    assert "FRESHNESS_GAP_OUTAGE_V3_CLOSURE" in forbidden
    assert "FORECAST_GENERATION" in forbidden
    assert "TRADING" in forbidden
    assert "EXECUTION" in forbidden


def test_lot35_gate_keeps_lot36_locked_and_safety_fail_closed() -> None:
    gate = load_gate()
    safety = gate["safety"]
    assert isinstance(safety, dict)
    assert gate["next_lot"] == 36
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    assert safety["external_connectivity_allowed"] is False
    assert safety["network_ingestion_allowed"] is False
    assert safety["raw_data_mutation_allowed"] is False
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0


def test_lot35_gate_binds_certified_lot34_evidence() -> None:
    prerequisites = load_gate()["prerequisites"]
    assert isinstance(prerequisites, dict)
    assert prerequisites["latest_implemented_lot"] == 34
    assert prerequisites["lot34_record_count"] == 3
    assert prerequisites["lot34_anomaly_count"] == 0
    assert prerequisites["lot34_quality_score_bps"] == 10000
    assert prerequisites["lot34_veto_action"] == "ALLOW_ANALYSIS"
    assert prerequisites["line_coverage_percent"] == 98.8
    assert prerequisites["branch_coverage_percent"] == 97.3
    assert prerequisites["mutation_score_percent"] == 84.0
    assert prerequisites["anti_flake_repetitions"] == 3


def test_lot35_gate_rejects_checksum_tamper() -> None:
    gate = load_gate()
    gate["owner"] = "WrongOwner"
    with pytest.raises(Lot35EntryGateError, match="checksum"):
        validate_gate_checksum(gate)


def test_lot35_gate_rejects_scope_expansion() -> None:
    gate = load_gate()
    gate["allowed_scope"] = [*gate["allowed_scope"], "FORECAST_GENERATION"]
    with pytest.raises(Lot35EntryGateError, match="allowed scope"):
        validate_scope_quality_and_safety(gate)


def test_lot35_gate_rejects_safety_relaxation() -> None:
    gate = load_gate()
    safety = dict(gate["safety"])
    safety["external_connectivity_allowed"] = True
    gate["safety"] = safety
    with pytest.raises(Lot35EntryGateError, match="safety"):
        validate_scope_quality_and_safety(gate)


def test_lot35_gate_rejects_lower_quality_threshold() -> None:
    gate = load_gate()
    quality = dict(gate["quality_gates"])
    quality["mutation_score_min_percent"] = 0
    gate["quality_gates"] = quality
    with pytest.raises(Lot35EntryGateError, match="quality"):
        validate_scope_quality_and_safety(gate)
