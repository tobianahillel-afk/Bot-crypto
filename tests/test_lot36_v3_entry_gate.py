from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_lot36_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_ROADMAP_BLOB,
    Lot36EntryGateError,
    canonical_checksum,
    canonical_roadmap_record,
    git_blob_sha,
    validate,
    validate_gate_checksum,
    validate_scope_quality_and_safety,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot36_v3_entry_gate.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"


def load_gate() -> dict[str, object]:
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot36_entry_gate_validator_passes() -> None:
    assert validate() == {
        "schema_version": "lot36-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT36_IMPLEMENTATION_ENTRY",
        "canonical_title": "Freshness, Gap, Outage Audit & V3 Closure",
        "output_checksum": EXPECTED_GATE_CHECKSUM,
        "next_locked_lot": 37,
        "external_connectivity_allowed": False,
        "raw_data_mutation_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def test_lot36_gate_checksum_recomputes() -> None:
    gate = load_gate()
    checksum = gate.pop("output_checksum")
    assert checksum == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(gate) == checksum


def test_lot36_gate_binds_exact_canonical_roadmap_blob_and_record() -> None:
    raw = ROADMAP_PATH.read_bytes()
    assert git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB
    record = canonical_roadmap_record()
    assert record["lot_number"] == 36
    assert record["lot_id"] == "Lot 36"
    assert record["title"] == "Freshness, Gap, Outage Audit & V3 Closure"
    assert record["version_id"] == "V3_MARKET_DATA_GOVERNANCE"
    assert record["status"] == "PLANNED_LOCKED"


def test_lot36_scope_is_v3_closure_only() -> None:
    gate = load_gate()
    allowed = set(gate["allowed_scope"])
    assert "FRESHNESS_GAP_OUTAGE_AUDIT" in allowed
    assert "V3_MARKET_DATA_GOVERNANCE_CLOSURE" in allowed
    assert "DETERMINISTIC_REPLAY_AND_CHECKSUM_COMPARISON" in allowed
    assert "FULL_CHAIN_VALIDATION_UNTIL_LOT36" in allowed
    forbidden = set(gate["forbidden_scope"])
    assert "V4_OR_LATER_CAPABILITY_ACTIVATION" in forbidden
    assert "MICROSTRUCTURE_MODELING" in forbidden
    assert "SIGNAL_GENERATION" in forbidden
    assert "TRADING" in forbidden
    assert "EXECUTION" in forbidden


def test_lot36_required_outputs_match_canonical_record() -> None:
    gate = load_gate()
    record = canonical_roadmap_record()
    assert set(gate["required_outputs"]) == set(record["output_contracts"])


def test_lot36_gate_keeps_lot37_locked_and_safety_fail_closed() -> None:
    gate = load_gate()
    safety = gate["safety"]
    assert isinstance(safety, dict)
    assert gate["next_lot"] == 37
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    assert safety["external_connectivity_allowed"] is False
    assert safety["network_ingestion_allowed"] is False
    assert safety["raw_data_mutation_allowed"] is False
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0


def test_lot36_gate_binds_certified_lot35_evidence() -> None:
    prerequisites = load_gate()["prerequisites"]
    assert isinstance(prerequisites, dict)
    assert prerequisites["latest_implemented_lot"] == 35
    assert prerequisites["lot35_report_count"] == 3
    assert prerequisites["lot35_match_count"] == 2
    assert prerequisites["lot35_tolerated_diff_count"] == 1
    assert prerequisites["lot35_minor_divergence_count"] == 0
    assert prerequisites["lot35_critical_divergence_count"] == 0
    assert prerequisites["lot35_veto_action"] == "ALLOW_ANALYSIS"
    assert prerequisites["line_coverage_percent"] == 96.43
    assert prerequisites["branch_coverage_percent"] == 93.75
    assert prerequisites["mutation_score_percent"] == 83.73
    assert prerequisites["anti_flake_repetitions"] == 3


def test_lot36_gate_rejects_checksum_tamper() -> None:
    gate = load_gate()
    gate["owner"] = "WrongOwner"
    with pytest.raises(Lot36EntryGateError, match="checksum"):
        validate_gate_checksum(gate)


def test_lot36_gate_rejects_v4_scope_expansion() -> None:
    gate = load_gate()
    gate["allowed_scope"] = [*gate["allowed_scope"], "MICROSTRUCTURE_MODELING"]
    with pytest.raises(Lot36EntryGateError, match="allowed scope"):
        validate_scope_quality_and_safety(gate)


def test_lot36_gate_rejects_safety_relaxation() -> None:
    gate = load_gate()
    safety = dict(gate["safety"])
    safety["external_connectivity_allowed"] = True
    gate["safety"] = safety
    with pytest.raises(Lot36EntryGateError, match="safety"):
        validate_scope_quality_and_safety(gate)


def test_lot36_gate_rejects_lower_quality_threshold() -> None:
    gate = load_gate()
    quality = dict(gate["quality_gates"])
    quality["mutation_score_min_percent"] = 0
    gate["quality_gates"] = quality
    with pytest.raises(Lot36EntryGateError, match="quality"):
        validate_scope_quality_and_safety(gate)
