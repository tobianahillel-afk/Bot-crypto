#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_lot33.json"
AUDIT_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json"
COLLECTION_PATH = ROOT / "data/audit/canonical_time_envelopes_lot33.json"
OVERLAY_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot33.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"
LOT32_STATE_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json"
LOT32_AUDIT_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json"
COVERAGE_PATH = ROOT / "reports/lot33/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot33/mutation_summary.json"
MERGED_COMMIT = "0c6619e0a57afed6b8cd342e341b066917743edc"
STATE_CHECKSUM = "4bb5f8df3b49a8a54b6a932a37d35a4575edc63f897c55e88df90dfaf000f450"
AUDIT_CHECKSUM = "73afe6a1d7dc73565d76f7e6d5f7c96cbc4fdecc6dadce88c2e88edb1ca365ad"


class Lot33PostMergeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot33PostMergeError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


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


def payload_checksum(payload: dict[str, Any], field: str, expected: str) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(content) == checksum, f"{field} mismatch")
    require(checksum == expected, f"{field} certified value changed")
    return checksum


def validate_lifecycle() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = load(OVERLAY_PATH)
    require(project["version"] == "0.33.0", "project version must be 0.33.0")
    require(overlay.get("latest_implemented_lot") == 33, "latest lot must be 33")
    require(
        overlay.get("previous_overlay") == "data/audit/roadmap_lifecycle_overlay_lot32.json",
        "lifecycle predecessor mismatch",
    )
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "lifecycle lots missing")
    lot33 = lots.get("33")
    require(isinstance(lot33, dict), "Lot 33 lifecycle missing")
    require(lot33.get("status") == "IMPLEMENTED_VALIDATED_TEMPORAL_ONLY", "Lot 33 status")
    require(lot33.get("merged_commit") == MERGED_COMMIT, "Lot 33 merged commit mismatch")
    require(lot33.get("runtime_mode") == "DATA_GOVERNANCE_ONLY", "runtime mode changed")
    require(lot33.get("external_connectivity_allowed") is False, "connectivity enabled")
    require(lot33.get("network_ingestion_allowed") is False, "ingestion enabled")
    require(lot33.get("trade_allowed") is False, "trading enabled")
    require(lot33.get("execution_allowed") is False, "execution enabled")
    require(
        lots.get("34") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 34 must remain locked",
    )


def validate_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    collection = load(COLLECTION_PATH)
    state_checksum = payload_checksum(state, "output_checksum", STATE_CHECKSUM)
    payload_checksum(audit, "audit_checksum", AUDIT_CHECKSUM)
    require(audit.get("state_output_checksum") == state_checksum, "audit/state link mismatch")
    require(collection.get("records") == state.get("canonical_envelopes"), "collection mismatch")
    lineage = state.get("lineage")
    require(isinstance(lineage, dict), "Lot 33 lineage missing")
    expected = {
        "instrument_registry_checksum": file_checksum(REGISTRY_PATH),
        "lot32_state_checksum": file_checksum(LOT32_STATE_PATH),
        "lot32_audit_checksum": file_checksum(LOT32_AUDIT_PATH),
    }
    for field, value in expected.items():
        require(lineage.get(field) == value, f"lineage mismatch: {field}")
    require(audit.get("instrument_registry_checksum") == expected["instrument_registry_checksum"], "audit lineage mismatch")
    return state, audit


def validate_temporal_result(state: dict[str, Any], audit: dict[str, Any]) -> None:
    health = state.get("clock_health")
    require(isinstance(health, dict), "clock health missing")
    require(health.get("status") == "HEALTHY", "certified clock is not healthy")
    require(health.get("observed_clock_drift_us") == 1000, "clock drift changed")
    require(health.get("observed_out_of_order_delay_us") == 201000, "late delay changed")
    require(health.get("observed_total_latency_us") == 420000, "total latency changed")
    require(audit.get("record_count") == 3, "record count changed")
    require(audit.get("out_of_order_record_count") == 1, "late record count changed")
    records = state.get("canonical_envelopes")
    require(isinstance(records, list) and len(records) == 3, "canonical records changed")
    keys = [
        (item["event_time_utc"], item["raw"]["sequence_id"], item["raw"]["revision_id"])
        for item in records
    ]
    require(keys == sorted(keys) and len(set(keys)) == len(keys), "canonical order changed")
    require(records[1]["event_time_utc"] == records[2]["event_time_utc"], "tie fixture changed")
    require(records[1]["raw"]["sequence_id"] == 1, "first sequence changed")
    require(records[2]["raw"]["sequence_id"] == 2, "second sequence changed")


def validate_quality_and_safety(state: dict[str, Any], audit: dict[str, Any]) -> None:
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    require(coverage.get("line_coverage_percent", 0) >= 95.0, "line coverage below gate")
    require(coverage.get("branch_coverage_percent", 0) >= 90.0, "branch coverage below gate")
    require(coverage.get("anti_flake_repetitions") == 3, "anti-flake evidence changed")
    require(mutation.get("mutation_score_percent", 0) >= 80.0, "mutation below gate")
    require(mutation.get("killed_mutants") == 96, "killed-mutant count changed")
    require(mutation.get("evaluated_mutants") == 106, "evaluated-mutant count changed")
    safety = {
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
    for field, value in safety.items():
        require(state.get(field) == value, f"state safety mismatch: {field}")
        require(audit.get(field) == value, f"audit safety mismatch: {field}")


def validate() -> dict[str, object]:
    validate_lifecycle()
    state, audit = validate_artifacts()
    validate_temporal_result(state, audit)
    validate_quality_and_safety(state, audit)
    document = (ROOT / "docs/LOT_33_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    require("GO_LOT33_POST_MERGE_AUDIT" in document, "post-merge verdict missing")
    return {
        "schema_version": "lot33-post-merge-validation-v1",
        "status": "PASS",
        "project_version": "0.33.0",
        "latest_implemented_lot": 33,
        "next_locked_lot": 34,
        "state_output_checksum": STATE_CHECKSUM,
        "audit_checksum": AUDIT_CHECKSUM,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot33PostMergeError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT33 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
