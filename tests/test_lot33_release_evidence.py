from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_lot33.json"
AUDIT_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json"
COLLECTION_PATH = ROOT / "data/audit/canonical_time_envelopes_lot33.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"
LOT32_STATE_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json"
LOT32_AUDIT_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json"
COVERAGE_PATH = ROOT / "reports/lot33/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot33/mutation_summary.json"
IMPLEMENTATION_COMMIT = "f4762cb7d68fd11a42962f8016f8af22e2bc1c5a"


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field)
    assert isinstance(checksum, str)
    assert canonical_checksum(content) == checksum
    return checksum


def test_lot33_release_artifacts_are_linked_and_fail_closed() -> None:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    collection = load(COLLECTION_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    payload_checksum(audit, "audit_checksum")
    assert collection == {
        "records": state["canonical_envelopes"],
        "schema_version": "canonical-time-envelope-collection-v1",
    }
    assert audit["state_output_checksum"] == state_checksum
    assert audit["code_commit"] == state["run_context"]["code_commit"]
    code_commit = audit["code_commit"]
    assert isinstance(code_commit, str)
    assert len(code_commit) == 40
    assert set(code_commit) <= set("0123456789abcdef")
    assert state["lineage"] == {
        "available_at": "2026-08-06T19:15:00.320000Z",
        "instrument_registry_checksum": file_checksum(REGISTRY_PATH),
        "instrument_registry_path": "data/audit/instrument_registry_lot32.json",
        "lineage_id": "lot33-from-certified-lot32-instrument-registry",
        "lot32_audit_checksum": file_checksum(LOT32_AUDIT_PATH),
        "lot32_state_checksum": file_checksum(LOT32_STATE_PATH),
        "schema_version": "lot33-lineage-envelope-v1",
    }
    assert audit["instrument_registry_checksum"] == file_checksum(REGISTRY_PATH)
    expected_safety = {
        "analysis_only": True,
        "used_for_decision": False,
        "external_connectivity_allowed": False,
        "network_ingestion_allowed": False,
        "real_credentials_allowed": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected_safety.items():
        assert state[field] == value
        assert audit[field] == value


def test_lot33_reference_temporal_observations_remain_exact() -> None:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    health = state["clock_health"]
    assert health == {
        "max_clock_drift_us": 5000,
        "max_out_of_order_delay_us": 500000,
        "max_total_latency_us": 500000,
        "observed_clock_drift_us": 1000,
        "observed_out_of_order_delay_us": 201000,
        "observed_total_latency_us": 420000,
        "reason_codes": ["CLOCK_THRESHOLDS_SATISFIED"],
        "schema_version": "clock-health-state-v1",
        "status": "HEALTHY",
    }
    assert audit["record_count"] == 3
    assert audit["out_of_order_record_count"] == 1
    assert audit["clock_health_status"] == "HEALTHY"
    assert audit["max_observed_clock_drift_us"] == 1000
    assert audit["max_observed_total_latency_us"] == 420000
    rows = [
        (
            item["raw"]["record_id"],
            item["event_time_utc"],
            item["raw"]["sequence_id"],
            item["clock_drift_us"],
            item["total_latency_us"],
            item["out_of_order_delay_us"],
        )
        for item in state["canonical_envelopes"]
    ]
    assert rows == [
        ("kraken-record-3-late", "2026-08-06T19:14:59.900000Z", 1, 1000, 420000, 201000),
        ("bitstamp-record-1", "2026-08-06T19:15:00.101000Z", 1, 1000, 70000, 0),
        ("coinbase-record-2", "2026-08-06T19:15:00.101000Z", 2, 500, 80000, 0),
    ]


def test_lot33_certified_quality_thresholds_remain_satisfied() -> None:
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    assert coverage["evidence_commit"] == IMPLEMENTATION_COMMIT
    assert coverage["status"] == "PASS"
    assert coverage["anti_flake_repetitions"] == 3
    assert coverage["line_coverage_percent"] >= coverage["line_minimum_percent"] >= 95.0
    assert coverage["branch_coverage_percent"] >= coverage["branch_minimum_percent"] >= 90.0
    assert mutation["evidence_commit"] == IMPLEMENTATION_COMMIT
    assert mutation["status"] == "PASS"
    assert mutation["evaluated_mutants"] == (
        mutation["killed_mutants"]
        + mutation["survived_mutants"]
        + mutation["timeout_mutants"]
    )
    assert mutation["mutation_score_percent"] >= mutation["minimum_score_percent"] >= 80.0
    assert mutation["killed_mutants"] == 96
    assert mutation["evaluated_mutants"] == 106
