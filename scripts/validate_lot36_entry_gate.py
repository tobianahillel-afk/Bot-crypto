#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot36_v3_entry_gate.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
OVERLAY_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot35.json"
STATE_PATH = ROOT / "data/audit/candle_trade_book_reconciliation_lot35.json"
AUDIT_PATH = ROOT / "data/audit/candle_trade_book_reconciliation_audit_lot35.json"
REPORTS_PATH = ROOT / "data/audit/reconciliation_reports_lot35.json"
VETO_PATH = ROOT / "data/audit/reconciliation_veto_lot35.json"
COVERAGE_PATH = ROOT / "reports/lot35/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot35/mutation_summary.json"

EXPECTED_BASE_COMMIT = "d9df26bfa2b294a5ca0b973807af32b39e882dda"
EXPECTED_IMPLEMENTATION_COMMIT = "a4501bb0d400c6c1b5cf970fc5aa6456ad8c6ea8"
EXPECTED_MERGED_COMMIT = "d083d4f27c89759ebed37b2ecacccbe88dccad11"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_STATE_CHECKSUM = "8fc7243beffdf985fd6947557b87ab7bd27f9191520eb2d5d9af25d1e7a886b4"
EXPECTED_AUDIT_CHECKSUM = "98a88396f5b2e5ffc1cde02435399540ad213f5ec361b33e8a19c08b0fedf1de"
EXPECTED_GATE_CHECKSUM = "ccddc668b83267effb6e82827c6a0f1f8d5879803f7d3e5cc6f9cfc745ba78a5"

EXPECTED_ALLOWED = {
    "ENTRY_GATE_SCHEMA_FRESHNESS_VALIDATION",
    "FRESHNESS_GAP_OUTAGE_AUDIT",
    "V3_MARKET_DATA_GOVERNANCE_CLOSURE",
    "CANONICAL_LINEAGE_BINDING",
    "ATOMIC_STATE_AUDIT_PERSISTENCE",
    "DETERMINISTIC_REPLAY_AND_CHECKSUM_COMPARISON",
    "NEGATIVE_AND_FORBIDDEN_CAPABILITY_VALIDATION",
    "CLOSURE_MANIFEST_AFTER_VALIDATORS_AND_HUMAN_REVIEW",
    "DATA_QUALITY_ANOMALY_REAUDIT_FOR_CLOSURE",
    "COVERAGE_FRESHNESS_COMPLETENESS_CONSISTENCY_SCORING",
    "ANOMALY_SEVERITY_INTERVAL_CORRECTION_QUARANTINE_STATUS",
    "DATA_QUALITY_VETO_BEFORE_ANALYSIS_SIGNAL_ORDER",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT36",
}
EXPECTED_OUTPUTS = {
    "FreshnessGapOutageAuditV3ClosureStateV1",
    "FreshnessGapOutageAuditV3ClosureAuditV1",
    "ReplayEvidenceV1",
    "LotValidationReportV1",
    "ClosureManifestV1",
    "DataQualityStateV1",
    "DataAnomalyV1",
    "DataQualityVetoV1",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "DESTRUCTIVE_RAW_DATA_CORRECTION",
    "LOT34_DATA_QUALITY_ENGINE_REIMPLEMENTATION",
    "LOT35_RECONCILIATION_ENGINE_REIMPLEMENTATION",
    "V4_OR_LATER_CAPABILITY_ACTIVATION",
    "CONTINUOUS_MARKET_STATE_PUBLICATION",
    "MICROSTRUCTURE_MODELING",
    "FORECAST_GENERATION",
    "SIGNAL_GENERATION",
    "RISK_APPROVAL",
    "ORDER_ROUTING",
    "TRADING",
    "EXECUTION",
}
EXPECTED_QUALITY_GATES = {
    "anti_flake_repetitions": 3,
    "branch_coverage_min_percent": 90,
    "line_coverage_min_percent": 95,
    "mutation_score_min_percent": 80,
}
EXPECTED_SAFETY = {
    "analysis_only": True,
    "approved_size": 0,
    "execution_allowed": False,
    "external_connectivity_allowed": False,
    "market_event_publication_allowed": False,
    "network_ingestion_allowed": False,
    "order_routing_allowed": False,
    "raw_data_mutation_allowed": False,
    "real_credentials_allowed": False,
    "risk_approval_allowed": False,
    "signal_generation_allowed": False,
    "trade_allowed": False,
    "used_for_decision": False,
}


class Lot36EntryGateError(RuntimeError):
    """Raised when the Lot 36 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot36EntryGateError(message)


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def validate_payload_checksum(
    payload: dict[str, Any], field: str, expected: str, label: str
) -> None:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(checksum == expected, f"{label} checksum value changed")
    require(canonical_checksum(content) == checksum, f"{label} checksum mismatch")


def validate_gate_checksum(gate: dict[str, Any]) -> None:
    validate_payload_checksum(gate, "output_checksum", EXPECTED_GATE_CHECKSUM, "Lot 36 gate")


def canonical_roadmap_record() -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= 37, "canonical roadmap Lot 36 line missing")
    record = json.loads(lines[36])
    require(isinstance(record, dict), "canonical Lot 36 roadmap record must be an object")
    return record


def validate_canonical_roadmap(gate: dict[str, Any]) -> None:
    record = canonical_roadmap_record()
    expected_identity = {
        "lot_id": "Lot 36",
        "lot_number": 36,
        "title": "Freshness, Gap, Outage Audit & V3 Closure",
        "version_id": "V3_MARKET_DATA_GOVERNANCE",
        "version_number": 3,
        "responsible_component": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "package_boundary": "src/crypto_quant_bot/data_governance",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected_identity.items():
        require(record.get(field) == value, f"canonical Lot 36 field changed: {field}")
    require(set(record.get("output_contracts", [])) == EXPECTED_OUTPUTS, "canonical Lot 36 outputs changed")
    validate_roadmap_reference(gate)


def validate_roadmap_reference(gate: dict[str, Any]) -> None:
    expected = {
        "source_path": "data/audit/product_scope_roadmap_lot21.jsonl",
        "source_line": 37,
        "source_blob_sha": EXPECTED_ROADMAP_BLOB,
        "lot_id": "Lot 36",
        "title": "Freshness, Gap, Outage Audit & V3 Closure",
        "version_id": "V3_MARKET_DATA_GOVERNANCE",
    }
    require(gate.get("canonical_roadmap") == expected, "Lot 36 canonical roadmap binding changed")


def validate_lifecycle() -> dict[str, Any]:
    overlay = load(OVERLAY_PATH)
    require(overlay.get("latest_implemented_lot") == 35, "historical lifecycle is not Lot 35")
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "historical lifecycle lots missing")
    lot35 = lots.get("35")
    require(isinstance(lot35, dict), "Lot 35 lifecycle missing")
    require(lot35.get("status") == "IMPLEMENTED_VALIDATED_RECONCILIATION_ONLY", "Lot 35 status changed")
    require(lot35.get("implementation_commit") == EXPECTED_IMPLEMENTATION_COMMIT, "Lot 35 implementation changed")
    require(lot35.get("merged_commit") == EXPECTED_MERGED_COMMIT, "Lot 35 merge commit changed")
    for field in ("trade_allowed", "execution_allowed", "external_connectivity_allowed", "network_ingestion_allowed", "raw_data_mutation_allowed"):
        require(lot35.get(field) is False, f"Lot 35 permission enabled: {field}")
    require(lots.get("36") == {"implementation_started": False, "status": "PLANNED_LOCKED"}, "Lot 36 historical lock changed")
    return lot35


def validate_lot35_evidence() -> dict[str, object]:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    validate_payload_checksum(state, "output_checksum", EXPECTED_STATE_CHECKSUM, "Lot 35 state")
    validate_payload_checksum(audit, "audit_checksum", EXPECTED_AUDIT_CHECKSUM, "Lot 35 audit")
    require(audit.get("state_output_checksum") == EXPECTED_STATE_CHECKSUM, "Lot 35 state/audit link changed")
    validate_lot35_collections(state)
    metrics = validate_lot35_metrics(state)
    quality = validate_lot35_quality()
    return {**metrics, **quality}


def validate_lot35_collections(state: dict[str, Any]) -> None:
    reports = load(REPORTS_PATH)
    veto = load(VETO_PATH)
    require(reports.get("records") == state.get("reports"), "Lot 35 report collection mismatch")
    require(veto == state.get("veto"), "Lot 35 veto artifact mismatch")
    require(veto.get("action") == "ALLOW_ANALYSIS", "Lot 35 reference veto changed")


def validate_lot35_metrics(state: dict[str, Any]) -> dict[str, object]:
    metrics = state.get("metrics")
    require(isinstance(metrics, dict), "Lot 35 metrics missing")
    expected = {
        "report_count": 3,
        "match_count": 2,
        "tolerated_diff_count": 1,
        "minor_divergence_count": 0,
        "critical_divergence_count": 0,
    }
    observed = {
        "report_count": metrics.get("lot_35_records_processed_total"),
        "match_count": metrics.get("lot_35_match_total"),
        "tolerated_diff_count": metrics.get("lot_35_tolerated_diff_total"),
        "minor_divergence_count": metrics.get("lot_35_minor_divergence_total"),
        "critical_divergence_count": metrics.get("lot_35_critical_divergence_total"),
    }
    require(observed == expected, "Lot 35 certified reconciliation metrics changed")
    return observed


def validate_lot35_quality() -> dict[str, object]:
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    require(coverage.get("status") == "PASS", "Lot 35 coverage evidence is not PASS")
    require(mutation.get("status") == "PASS", "Lot 35 mutation evidence is not PASS")
    expected = {
        "line_coverage_percent": 96.43,
        "branch_coverage_percent": 93.75,
        "mutation_score_percent": 83.73,
        "anti_flake_repetitions": 3,
    }
    observed = {
        "line_coverage_percent": coverage.get("line_coverage_percent"),
        "branch_coverage_percent": coverage.get("branch_coverage_percent"),
        "mutation_score_percent": mutation.get("mutation_score_percent"),
        "anti_flake_repetitions": coverage.get("anti_flake_repetitions"),
    }
    require(observed == expected, "Lot 35 certified quality evidence changed")
    return observed


def validate_prerequisites(gate: dict[str, Any], lot35: dict[str, Any], evidence: dict[str, object]) -> None:
    expected = {
        "latest_implemented_lot": 35,
        "lot35_status": lot35["status"],
        "lot35_implementation_commit": EXPECTED_IMPLEMENTATION_COMMIT,
        "lot35_implementation_merged_commit": EXPECTED_MERGED_COMMIT,
        "lot35_post_merge_audit_commit": EXPECTED_BASE_COMMIT,
        "lot35_state_checksum": EXPECTED_STATE_CHECKSUM,
        "lot35_audit_checksum": EXPECTED_AUDIT_CHECKSUM,
        "lot35_report_count": evidence["report_count"],
        "lot35_match_count": evidence["match_count"],
        "lot35_tolerated_diff_count": evidence["tolerated_diff_count"],
        "lot35_minor_divergence_count": evidence["minor_divergence_count"],
        "lot35_critical_divergence_count": evidence["critical_divergence_count"],
        "lot35_veto_action": "ALLOW_ANALYSIS",
        "line_coverage_percent": evidence["line_coverage_percent"],
        "branch_coverage_percent": evidence["branch_coverage_percent"],
        "mutation_score_percent": evidence["mutation_score_percent"],
        "anti_flake_repetitions": evidence["anti_flake_repetitions"],
    }
    require(gate.get("prerequisites") == expected, "Lot 36 prerequisites differ from certified Lot 35 evidence")


def validate_scope_quality_and_safety(gate: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version": "lot36-v3-entry-gate-v1",
        "target_lot": 36,
        "base_commit": EXPECTED_BASE_COMMIT,
        "current_version": "0.35.0",
        "gate_status": "GO_LOT36_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT36",
        "implementation_started": False,
        "owner": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "next_lot": 37,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected_fields.items():
        require(gate.get(field) == value, f"Lot 36 gate field changed: {field}")
    require(set(gate.get("allowed_scope", [])) == EXPECTED_ALLOWED, "Lot 36 allowed scope changed")
    require(set(gate.get("required_outputs", [])) == EXPECTED_OUTPUTS, "Lot 36 required outputs changed")
    require(set(gate.get("forbidden_scope", [])) == EXPECTED_FORBIDDEN, "Lot 36 forbidden scope changed")
    require(gate.get("quality_gates") == EXPECTED_QUALITY_GATES, "Lot 36 quality gates changed")
    require(gate.get("safety") == EXPECTED_SAFETY, "Lot 36 safety boundary changed")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_gate_checksum(gate)
    validate_canonical_roadmap(gate)
    lot35 = validate_lifecycle()
    evidence = validate_lot35_evidence()
    validate_prerequisites(gate, lot35, evidence)
    validate_scope_quality_and_safety(gate)
    return {
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


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot36EntryGateError, OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT36 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
