from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "59b189e9980772245993a9212b6c8ad5e9a88a00"
STATE_PATH = ROOT / "data/audit/microstructure_scope_and_offline_data_contracts_lot37.json"
AUDIT_PATH = ROOT / "data/audit/microstructure_scope_and_offline_data_contracts_audit_lot37.json"
REGISTRY_PATH = ROOT / "data/audit/microstructure_contract_registry_lot37.json"
MATRIX_PATH = ROOT / "data/audit/microstructure_capability_matrix_lot37.json"
COVERAGE_PATH = ROOT / "reports/lot37/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot37/mutation_summary.json"
EXPECTED_GATE = "37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"LOT37_EVIDENCE_NOT_OBJECT:{path}")
    return value


def _checksum(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _verify_outputs() -> tuple[dict[str, Any], dict[str, Any]]:
    state = _load(STATE_PATH)
    audit = _load(AUDIT_PATH)
    registry = _load(REGISTRY_PATH)
    matrix = _load(MATRIX_PATH)
    state_body = dict(state)
    state_checksum = state_body.pop("output_checksum")
    audit_body = dict(audit)
    audit_checksum = audit_body.pop("audit_checksum")
    assert _checksum(state_body) == state_checksum
    assert _checksum(audit_body) == audit_checksum
    assert audit["state_output_checksum"] == state_checksum
    assert audit["contract_registry_checksum"] == _checksum(registry)
    assert audit["capability_matrix_checksum"] == _checksum(matrix)
    assert state["contract_registry"] == registry
    assert state["capability_matrix"] == matrix
    return state, audit


def _verify_scope(state: dict[str, Any], audit: dict[str, Any]) -> None:
    assert state["run_context"]["code_commit"] == SOURCE_HEAD
    assert audit["code_commit"] == SOURCE_HEAD
    assert state["lineage"]["entry_gate_checksum"] == EXPECTED_GATE
    assert audit["entry_gate_checksum"] == EXPECTED_GATE
    assert state["validation_state"] == "VALIDATED_OFFLINE_CONTRACT_SCOPE"
    assert audit["validation_state"] == "VALIDATED_OFFLINE_CONTRACT_SCOPE"
    safety = state["safety"]
    assert safety == audit["safety"]
    assert safety["analysis_only"] is True
    assert safety["approved_size"] == 0
    for field in (
        "execution_allowed",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "order_routing_allowed",
        "risk_approval_allowed",
        "signal_generation_allowed",
        "trade_allowed",
        "used_for_decision",
    ):
        assert safety[field] is False
    lot38 = next(
        item for item in state["capability_matrix"]["entries"]
        if item["capability_id"] == "LOT38_ORDER_BOOK_L2_SNAPSHOT_ENGINE"
    )
    assert lot38["classification"] == "DISABLED"
    assert lot38["implementation_status"] == "PLANNED_LOCKED"


def _verify_quality() -> None:
    coverage = _load(COVERAGE_PATH)
    mutation = _load(MUTATION_PATH)
    assert coverage["source_head_sha"] == SOURCE_HEAD
    assert coverage["status"] == "PASS"
    assert coverage["line_coverage_percent"] >= coverage["line_minimum_percent"] == 95.0
    assert coverage["branch_coverage_percent"] >= coverage["branch_minimum_percent"] == 90.0
    assert coverage["anti_flake_repetitions"] == 3
    assert mutation["source_head_sha"] == SOURCE_HEAD
    assert mutation["status"] == "PASS"
    assert mutation["evaluated_mutants"] == mutation["total_mutants"] == 1368
    assert mutation["killed_mutants"] == 1098
    assert mutation["survived_mutants"] == 270
    assert mutation["timeout_mutants"] == 0
    expected_score = round(100.0 * 1098 / 1368, 2)
    assert mutation["mutation_score_percent"] == expected_score == 80.26
    assert mutation["mutation_score_percent"] >= mutation["minimum_score_percent"] == 80.0


def main() -> None:
    state, audit = _verify_outputs()
    _verify_scope(state, audit)
    _verify_quality()
    print("LOT37_FROZEN_EVIDENCE_VALIDATED")


if __name__ == "__main__":
    main()
