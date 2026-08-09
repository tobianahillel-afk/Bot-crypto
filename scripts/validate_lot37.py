#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data/audit/microstructure_scope_and_offline_data_contracts_lot37.json"
AUDIT_PATH = ROOT / "data/audit/microstructure_scope_and_offline_data_contracts_audit_lot37.json"
REGISTRY_PATH = ROOT / "data/audit/microstructure_contract_registry_lot37.json"
MATRIX_PATH = ROOT / "data/audit/microstructure_capability_matrix_lot37.json"
GATE_PATH = ROOT / "data/audit/lot37_v4_entry_gate.json"
OVERLAY_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot36.json"
CONFIG_PATH = ROOT / "config/microstructure/microstructure_scope_offline_data_contracts_v1.json"
EXPECTED_GATE_CHECKSUM = "37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d"
EXPECTED_SAFETY = {
    "analysis_only": True,
    "approved_size": 0,
    "execution_allowed": False,
    "external_connectivity_allowed": False,
    "market_event_publication_allowed": False,
    "network_ingestion_allowed": False,
    "order_routing_allowed": False,
    "participant_behavior_inference_explicitly_labeled": True,
    "raw_data_mutation_allowed": False,
    "real_credentials_allowed": False,
    "risk_approval_allowed": False,
    "scenario_score_is_signal": False,
    "signal_generation_allowed": False,
    "trade_allowed": False,
    "used_for_decision": False,
}


class Lot37ValidationError(RuntimeError):
    """Raised when persisted Lot 37 evidence is not independently valid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot37ValidationError(message)


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def canonical_checksum(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verified_payload(path: Path, checksum_field: str) -> tuple[dict[str, Any], str]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(checksum_field, None)
    require(isinstance(checksum, str), f"{checksum_field} missing: {path.name}")
    require(canonical_checksum(body) == checksum, f"checksum mismatch: {path.name}")
    return payload, checksum


def validate_gate_and_lifecycle() -> None:
    gate, checksum = verified_payload(GATE_PATH, "output_checksum")
    require(checksum == EXPECTED_GATE_CHECKSUM, "Lot 37 gate checksum changed")
    require(gate.get("gate_status") == "GO_LOT37_IMPLEMENTATION_ENTRY", "Lot 37 gate not GO")
    require(gate.get("implementation_started") is False, "entry gate history was rewritten")
    require(gate.get("next_lot") == 38 and gate.get("next_lot_status") == "PLANNED_LOCKED", "Lot 38 gate boundary changed")
    require(gate.get("safety") == EXPECTED_SAFETY, "Lot 37 gate safety changed")
    overlay = load(OVERLAY_PATH)
    require(overlay.get("latest_implemented_lot") == 36, "Lot 37 implementation requires audited V3 closure")
    lot36 = overlay.get("lots", {}).get("36")
    require(isinstance(lot36, dict) and lot36.get("v3_closed") is True, "V3 closure missing")
    require(overlay.get("lots", {}).get("37") == {"implementation_started": False, "status": "PLANNED_LOCKED"}, "historical Lot 37 lock changed")


def validate_state(expected_code_commit: str | None) -> tuple[dict[str, Any], str]:
    state, checksum = verified_payload(STATE_PATH, "output_checksum")
    require(state.get("schema_version") == "microstructure-scope-offline-data-contracts-state-v1", "Lot 37 state schema changed")
    require(state.get("validation_state") == "VALIDATED_OFFLINE_CONTRACT_SCOPE", "Lot 37 state is not validated")
    require(state.get("safety") == EXPECTED_SAFETY, "Lot 37 state safety changed")
    run_context = state.get("run_context")
    require(isinstance(run_context, dict), "Lot 37 run context missing")
    require(run_context.get("runtime_mode") == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "Lot 37 runtime changed")
    if expected_code_commit is not None:
        require(run_context.get("code_commit") == expected_code_commit, "Lot 37 code commit mismatch")
    lineage = state.get("lineage")
    require(isinstance(lineage, dict), "Lot 37 lineage missing")
    require(lineage.get("entry_gate_checksum") == EXPECTED_GATE_CHECKSUM, "Lot 37 lineage gate mismatch")
    metrics = state.get("metrics")
    require(isinstance(metrics, dict), "Lot 37 metrics missing")
    expected_metrics = {
        "lot_37_contracts_total": 6,
        "lot_37_capabilities_total": 27,
        "lot_37_required_capabilities_total": 4,
        "lot_37_disabled_capabilities_total": 15,
        "lot_37_forbidden_capabilities_total": 8,
        "lot_37_public_api_symbols_total": 4,
        "lot_37_offline_fixture_total": 2,
        "lot_37_validation_failures_total": 0,
        "lot_37_processing_latency_us": 950000,
    }
    for field, value in expected_metrics.items():
        require(metrics.get(field) == value, f"Lot 37 metric changed: {field}")
    return state, checksum


def validate_collections(state: dict[str, Any]) -> tuple[str, str]:
    registry = load(REGISTRY_PATH)
    matrix = load(MATRIX_PATH)
    require(registry == state.get("contract_registry"), "Lot 37 registry collection mismatch")
    require(matrix == state.get("capability_matrix"), "Lot 37 capability matrix collection mismatch")
    registry_names = {item.get("contract_name") for item in registry.get("entries", []) if isinstance(item, dict)}
    require(len(registry_names) == 6, "Lot 37 contract registry membership changed")
    entries = [item for item in matrix.get("entries", []) if isinstance(item, dict)]
    require(len(entries) == 27, "Lot 37 capability matrix membership changed")
    require(sum(item.get("classification") == "DISABLED" for item in entries) == 15, "future V4 locks changed")
    require(sum(item.get("classification") == "FORBIDDEN" for item in entries) == 8, "forbidden capability set changed")
    require(all(item.get("implementation_status") == "PLANNED_LOCKED" for item in entries if item.get("classification") == "DISABLED"), "future V4 capability activated")
    return canonical_checksum(registry), canonical_checksum(matrix)


def validate_audit(state_checksum: str, registry_checksum: str, matrix_checksum: str, expected_code_commit: str | None) -> dict[str, Any]:
    audit, _ = verified_payload(AUDIT_PATH, "audit_checksum")
    require(audit.get("state_output_checksum") == state_checksum, "Lot 37 state/audit mismatch")
    require(audit.get("config_checksum") == hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(), "Lot 37 config checksum mismatch")
    require(audit.get("entry_gate_checksum") == EXPECTED_GATE_CHECKSUM, "Lot 37 audit gate mismatch")
    require(audit.get("contract_registry_checksum") == registry_checksum, "Lot 37 registry checksum mismatch")
    require(audit.get("capability_matrix_checksum") == matrix_checksum, "Lot 37 matrix checksum mismatch")
    require(audit.get("safety") == EXPECTED_SAFETY, "Lot 37 audit safety changed")
    if expected_code_commit is not None:
        require(audit.get("code_commit") == expected_code_commit, "Lot 37 audit code commit mismatch")
    return audit


def validate_schemas() -> None:
    config = load(CONFIG_PATH)
    contracts = config.get("contracts")
    require(isinstance(contracts, list) and len(contracts) == 6, "Lot 37 contract config incomplete")
    for entry in contracts:
        require(isinstance(entry, dict), "Lot 37 contract entry malformed")
        schema_path = entry.get("schema_path")
        require(isinstance(schema_path, str), "Lot 37 schema path missing")
        schema = load(ROOT / schema_path)
        require(schema.get("type") == "object", f"Lot 37 schema is not an object: {schema_path}")
        require(schema.get("additionalProperties") is False, f"Lot 37 schema is permissive: {schema_path}")


def validate(expected_code_commit: str | None = None) -> dict[str, object]:
    validate_gate_and_lifecycle()
    validate_schemas()
    state, state_checksum = validate_state(expected_code_commit)
    registry_checksum, matrix_checksum = validate_collections(state)
    audit = validate_audit(state_checksum, registry_checksum, matrix_checksum, expected_code_commit)
    return {
        "schema_version": "lot37-validation-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "state_output_checksum": state_checksum,
        "audit_checksum": audit["audit_checksum"],
        "contracts_total": 6,
        "capabilities_total": 27,
        "future_v4_capabilities_locked": 15,
        "forbidden_capabilities": 8,
        "next_lot": 38,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate persisted Lot 37 evidence")
    parser.add_argument("--expected-code-commit", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        print(json.dumps(validate(args.expected_code_commit), sort_keys=True))
    except (Lot37ValidationError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT37 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
