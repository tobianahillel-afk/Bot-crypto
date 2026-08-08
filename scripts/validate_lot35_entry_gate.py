#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot35_v3_entry_gate.json"
OVERLAY_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot34.json"
STATE_PATH = ROOT / "data/audit/market_data_quality_engine_lot34.json"
AUDIT_PATH = ROOT / "data/audit/market_data_quality_engine_audit_lot34.json"
QUALITY_PATH = ROOT / "data/audit/data_quality_states_lot34.json"
ANOMALY_PATH = ROOT / "data/audit/data_anomalies_lot34.json"
VETO_PATH = ROOT / "data/audit/data_quality_veto_lot34.json"
COVERAGE_PATH = ROOT / "reports/lot34/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot34/mutation_summary.json"

EXPECTED_BASE_COMMIT = "ff9bff8e670d2d6dd86df713c4baf5d0228e53c8"
EXPECTED_IMPLEMENTATION_COMMIT = "27880f7e14f3d1c97cce9a73f9fe4b5498947068"
EXPECTED_STATE_CHECKSUM = "bc66816383ddf141016ad66796cc5dd4ad3442cd3594d96ad1f7db13d7c6bc01"
EXPECTED_AUDIT_CHECKSUM = "cd4410a2ea9ef6cdc061caf5115d908d03575e219eb9f4da402bff1712f6c7ce"
EXPECTED_GATE_CHECKSUM = "e3ca9847c39a9ab8a043639cda556308506e9d5a497eb7821d3b962278c507ab"
EXPECTED_ALLOWED = {
    "IDENTIFIER_QUANTITY_PRICE_FEE_RECONCILIATION",
    "BALANCE_POSITION_TIMESTAMP_RECONCILIATION",
    "MATCH_TOLERATED_MINOR_CRITICAL_CLASSIFICATION",
    "EXACT_DELTA_COMPUTATION",
    "VERSIONED_TOLERANCE_EVALUATION",
    "SOURCE_OF_TRUTH_RESOLUTION",
    "RECONCILIATION_REPORTING",
    "RECONCILIATION_VETO",
    "ORPHAN_DUPLICATE_DETECTION",
    "IDEMPOTENT_RESTART_RECONCILIATION",
    "FAIL_CLOSED_PAUSE_BLOCK_KILL_SWITCH",
}
EXPECTED_OUTPUTS = {
    "CandleTradeBookReconciliationStateV1",
    "CandleTradeBookReconciliationAuditV1",
    "ReconciliationReportV1",
    "ReconciliationVetoV1",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "DESTRUCTIVE_RAW_DATA_CORRECTION",
    "MARKET_DATA_QUALITY_ENGINE_REIMPLEMENTATION",
    "FRESHNESS_GAP_OUTAGE_V3_CLOSURE",
    "CONTINUOUS_MARKET_STATE_PUBLICATION",
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


class Lot35EntryGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot35EntryGateError(message)


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


def validate_payload_checksum(
    payload: dict[str, Any], field: str, expected: str, label: str
) -> None:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(checksum == expected, f"{label} checksum value changed")
    require(canonical_checksum(content) == checksum, f"{label} checksum mismatch")


def validate_gate_checksum(gate: dict[str, Any]) -> None:
    validate_payload_checksum(gate, "output_checksum", EXPECTED_GATE_CHECKSUM, "Lot 35 gate")


def validate_current_lifecycle() -> dict[str, Any]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["version"] == "0.34.0", "Lot 35 gate requires project version 0.34.0")
    overlay = load(OVERLAY_PATH)
    require(overlay.get("latest_implemented_lot") == 34, "current lifecycle is not Lot 34")
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "lifecycle lots missing")
    lot34 = lots.get("34")
    require(isinstance(lot34, dict), "Lot 34 lifecycle missing")
    require(
        lot34.get("status") == "IMPLEMENTED_VALIDATED_DATA_QUALITY_ONLY",
        "Lot 34 lifecycle status changed",
    )
    require(
        lot34.get("merged_commit") == EXPECTED_IMPLEMENTATION_COMMIT,
        "Lot 34 implementation merge commit changed",
    )
    require(lot34.get("external_connectivity_allowed") is False, "Lot 34 connectivity enabled")
    require(lot34.get("network_ingestion_allowed") is False, "Lot 34 ingestion enabled")
    require(lot34.get("raw_data_mutation_allowed") is False, "Lot 34 raw mutation enabled")
    require(
        lots.get("35") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 35 must remain locked until its entry gate is merged",
    )
    return lot34


def validate_lot34_evidence() -> dict[str, object]:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    quality = load(QUALITY_PATH)
    anomaly = load(ANOMALY_PATH)
    veto = load(VETO_PATH)
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    validate_payload_checksum(state, "output_checksum", EXPECTED_STATE_CHECKSUM, "Lot 34 state")
    validate_payload_checksum(audit, "audit_checksum", EXPECTED_AUDIT_CHECKSUM, "Lot 34 audit")
    require(audit.get("state_output_checksum") == EXPECTED_STATE_CHECKSUM, "Lot 34 audit link changed")
    for field, value in EXPECTED_SAFETY.items():
        require(state.get(field) == value, f"Lot 34 state safety changed: {field}")
        require(audit.get(field) == value, f"Lot 34 audit safety changed: {field}")
    metrics = state.get("metrics")
    require(isinstance(metrics, dict), "Lot 34 metrics missing")
    record_count = metrics.get("lot_34_records_processed_total")
    anomaly_count = metrics.get("lot_34_anomalies_detected_total")
    require(record_count == 3, "Lot 34 certified record count changed")
    require(anomaly_count == 0, "Lot 34 certified anomaly count changed")
    quality_records = quality.get("records")
    require(isinstance(quality_records, list) and len(quality_records) == 1, "Lot 34 quality evidence changed")
    quality_score = quality_records[0].get("quality_score_bps")
    require(quality_score == 10000, "Lot 34 certified quality score changed")
    anomaly_records = anomaly.get("records")
    require(isinstance(anomaly_records, list) and not anomaly_records, "Lot 34 anomaly evidence changed")
    veto_action = veto.get("action")
    require(veto_action == "ALLOW_ANALYSIS", "Lot 34 certified veto action changed")
    require(coverage.get("status") == "PASS", "Lot 34 coverage evidence is not PASS")
    require(coverage.get("line_coverage_percent") == 98.8, "Lot 34 line coverage changed")
    require(coverage.get("branch_coverage_percent") == 97.3, "Lot 34 branch coverage changed")
    require(coverage.get("anti_flake_repetitions") == 3, "Lot 34 anti-flake evidence changed")
    require(mutation.get("status") == "PASS", "Lot 34 mutation evidence is not PASS")
    require(mutation.get("mutation_score_percent") == 84.0, "Lot 34 mutation score changed")
    return {
        "record_count": record_count,
        "anomaly_count": anomaly_count,
        "quality_score_bps": quality_score,
        "veto_action": veto_action,
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "anti_flake_repetitions": coverage["anti_flake_repetitions"],
    }


def validate_prerequisites(
    gate: dict[str, Any], lot34: dict[str, Any], evidence: dict[str, object]
) -> None:
    prerequisites = gate.get("prerequisites")
    require(isinstance(prerequisites, dict), "Lot 35 gate prerequisites missing")
    expected = {
        "latest_implemented_lot": 34,
        "lot34_status": lot34["status"],
        "lot34_implementation_merged_commit": EXPECTED_IMPLEMENTATION_COMMIT,
        "lot34_post_merge_audit_commit": EXPECTED_BASE_COMMIT,
        "lot34_state_checksum": EXPECTED_STATE_CHECKSUM,
        "lot34_audit_checksum": EXPECTED_AUDIT_CHECKSUM,
        "lot34_record_count": evidence["record_count"],
        "lot34_anomaly_count": evidence["anomaly_count"],
        "lot34_quality_score_bps": evidence["quality_score_bps"],
        "lot34_veto_action": evidence["veto_action"],
        "line_coverage_percent": evidence["line_coverage_percent"],
        "branch_coverage_percent": evidence["branch_coverage_percent"],
        "mutation_score_percent": evidence["mutation_score_percent"],
        "anti_flake_repetitions": evidence["anti_flake_repetitions"],
    }
    require(prerequisites == expected, "Lot 35 prerequisites differ from certified Lot 34 evidence")


def validate_scope_quality_and_safety(gate: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version": "lot35-v3-entry-gate-v1",
        "target_lot": 35,
        "base_commit": EXPECTED_BASE_COMMIT,
        "current_version": "0.34.0",
        "gate_status": "GO_LOT35_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT35",
        "implementation_started": False,
        "owner": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "next_lot": 36,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected_fields.items():
        require(gate.get(field) == value, f"Lot 35 gate field changed: {field}")
    require(set(gate.get("allowed_scope", [])) == EXPECTED_ALLOWED, "Lot 35 allowed scope changed")
    require(set(gate.get("required_outputs", [])) == EXPECTED_OUTPUTS, "Lot 35 required outputs changed")
    require(set(gate.get("forbidden_scope", [])) == EXPECTED_FORBIDDEN, "Lot 35 forbidden scope changed")
    require(gate.get("quality_gates") == EXPECTED_QUALITY_GATES, "Lot 35 quality gates changed")
    require(gate.get("safety") == EXPECTED_SAFETY, "Lot 35 safety boundary changed")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_gate_checksum(gate)
    lot34 = validate_current_lifecycle()
    evidence = validate_lot34_evidence()
    validate_prerequisites(gate, lot34, evidence)
    validate_scope_quality_and_safety(gate)
    return {
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


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot35EntryGateError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT35 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
