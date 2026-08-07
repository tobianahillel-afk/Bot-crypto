#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot34_v3_entry_gate.json"
OVERLAY_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot33.json"
LOT33_STATE_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_lot33.json"
LOT33_AUDIT_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json"
LOT33_COLLECTION_PATH = ROOT / "data/audit/canonical_time_envelopes_lot33.json"
EXPECTED_BASE_COMMIT = "dcd7af6f3ce3b5c73c52893aaca708fea227b37e"
EXPECTED_CHECKSUM = "4a5bf1d61f97ce4a49836da577e6a2464544f16554143973caf32777de4830fa"
EXPECTED_ALLOWED = {
    "MISSING_INTERVAL_DETECTION",
    "DUPLICATE_DETECTION",
    "OUT_OF_ORDER_DETECTION",
    "STALE_DATA_DETECTION",
    "INVALID_OHLC_DETECTION",
    "NEGATIVE_VOLUME_DETECTION",
    "IMPOSSIBLE_SPREAD_DETECTION",
    "SCHEMA_DRIFT_DETECTION",
    "COVERAGE_FRESHNESS_COMPLETENESS_CONSISTENCY_SCORING",
    "NON_DESTRUCTIVE_QUARANTINE",
    "DATA_QUALITY_VETO",
}
EXPECTED_OUTPUTS = {
    "MarketDataQualityEngineStateV1",
    "MarketDataQualityEngineAuditV1",
    "DataQualityStateV1",
    "DataAnomalyV1",
    "DataQualityVetoV1",
}
EXPECTED_FORBIDDEN = {
    "DESTRUCTIVE_RAW_DATA_CORRECTION",
    "CANDLE_TRADE_BOOK_RECONCILIATION",
    "CONTINUOUS_MARKET_STATE_PUBLICATION",
    "FORECAST_GENERATION",
    "SIGNAL_GENERATION",
    "RISK_APPROVAL",
    "ORDER_ROUTING",
    "TRADING",
    "EXECUTION",
}
EXPECTED_QUALITY = {
    "anti_flake_repetitions": 3,
    "branch_coverage_min_percent": 90,
    "line_coverage_min_percent": 95,
    "mutation_score_min_percent": 80,
}
EXPECTED_SAFETY = {
    "analysis_only": True,
    "used_for_decision": False,
    "external_connectivity_allowed": False,
    "network_ingestion_allowed": False,
    "real_credentials_allowed": False,
    "market_event_publication_allowed": False,
    "raw_data_mutation_allowed": False,
    "signal_generation_allowed": False,
    "risk_approval_allowed": False,
    "order_routing_allowed": False,
    "trade_allowed": False,
    "execution_allowed": False,
    "approved_size": 0,
}


class Lot34EntryGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot34EntryGateError(message)


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


def validate_gate_checksum(gate: dict[str, Any]) -> None:
    payload = dict(gate)
    checksum = payload.pop("output_checksum", None)
    require(checksum == EXPECTED_CHECKSUM, "Lot 34 gate checksum value changed")
    require(canonical_checksum(payload) == checksum, "Lot 34 gate checksum mismatch")


def validate_prerequisites(gate: dict[str, Any]) -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = load(OVERLAY_PATH)
    state = load(LOT33_STATE_PATH)
    audit = load(LOT33_AUDIT_PATH)
    collection = load(LOT33_COLLECTION_PATH)
    require(project["version"] == "0.33.0", "Lot 34 gate requires project 0.33.0")
    require(overlay.get("latest_implemented_lot") == 33, "current lifecycle is not Lot 33")
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "lifecycle lots missing")
    lot33 = lots.get("33")
    require(isinstance(lot33, dict), "Lot 33 lifecycle missing")
    require(lot33.get("status") == "IMPLEMENTED_VALIDATED_TEMPORAL_ONLY", "Lot 33 status changed")
    require(
        lot33.get("merged_commit") == "0c6619e0a57afed6b8cd342e341b066917743edc",
        "Lot 33 merged commit changed",
    )
    require(
        lots.get("34") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 34 pre-gate state changed",
    )
    prerequisites = gate.get("prerequisites")
    require(isinstance(prerequisites, dict), "gate prerequisites missing")
    require(prerequisites.get("latest_implemented_lot") == 33, "gate latest lot mismatch")
    require(prerequisites.get("lot33_status") == lot33.get("status"), "gate Lot 33 status mismatch")
    require(
        prerequisites.get("lot33_merged_commit") == lot33.get("merged_commit"),
        "gate Lot 33 commit mismatch",
    )
    require(
        prerequisites.get("lot33_state_checksum") == state.get("output_checksum"),
        "gate Lot 33 state mismatch",
    )
    require(
        prerequisites.get("lot33_audit_checksum") == audit.get("audit_checksum"),
        "gate Lot 33 audit mismatch",
    )
    health = state.get("clock_health")
    require(isinstance(health, dict), "Lot 33 clock health missing")
    require(
        prerequisites.get("clock_health_status") == health.get("status") == "HEALTHY",
        "Lot 33 clock health is not healthy",
    )
    records = collection.get("records")
    require(
        isinstance(records, list)
        and len(records) == prerequisites.get("canonical_record_count") == 3,
        "Lot 33 canonical record count mismatch",
    )
    require(records == state.get("canonical_envelopes"), "Lot 33 collection differs from state")


def validate_scope(gate: dict[str, Any]) -> None:
    expected = {
        "schema_version": "lot34-v3-entry-gate-v1",
        "target_lot": 34,
        "base_commit": EXPECTED_BASE_COMMIT,
        "current_version": "0.33.0",
        "gate_status": "GO_LOT34_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT34",
        "implementation_started": False,
        "owner": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "next_lot": 35,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(gate.get(field) == value, f"gate field changed: {field}")
    require(set(gate.get("allowed_scope", [])) == EXPECTED_ALLOWED, "allowed scope changed")
    require(set(gate.get("required_outputs", [])) == EXPECTED_OUTPUTS, "required outputs changed")
    require(
        set(gate.get("forbidden_scope", [])) == EXPECTED_FORBIDDEN,
        "forbidden scope changed",
    )


def validate_quality_and_safety(gate: dict[str, Any]) -> None:
    require(gate.get("quality_gates") == EXPECTED_QUALITY, "quality gates changed")
    require(gate.get("safety") == EXPECTED_SAFETY, "gate safety boundary changed")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_gate_checksum(gate)
    validate_prerequisites(gate)
    validate_scope(gate)
    validate_quality_and_safety(gate)
    return {
        "schema_version": "lot34-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT34_IMPLEMENTATION_ENTRY",
        "output_checksum": EXPECTED_CHECKSUM,
        "next_locked_lot": 35,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot34EntryGateError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT34 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
