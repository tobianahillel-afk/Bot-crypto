#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "b74bea4329d5e5cb7cf2452058b684ea5a5df13c"
EXPECTED_GATE = "29fe4a5fd14b3bce95e3016fce67e10f94edcca1c2aad60c9fda382f3eb9d6a0"
STATE_PATH = ROOT / "data/audit/order_book_l2_snapshot_engine_lot38.json"
AUDIT_PATH = ROOT / "data/audit/order_book_l2_snapshot_engine_audit_lot38.json"
SNAPSHOT_PATH = ROOT / "data/audit/order_book_snapshot_lot38.json"
HEALTH_PATH = ROOT / "data/audit/book_health_state_lot38.json"
COVERAGE_PATH = ROOT / "reports/lot38/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot38/mutation_summary.json"
GATE_PATH = ROOT / "data/audit/lot38_v4_entry_gate.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"LOT38_EVIDENCE_NOT_OBJECT:{path}")
    return value


def _checksum(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _without_checksum(value: dict[str, Any], field: str) -> tuple[dict[str, Any], str]:
    body = dict(value)
    checksum = body.pop(field)
    if not isinstance(checksum, str):
        raise AssertionError(f"LOT38_CHECKSUM_NOT_TEXT:{field}")
    return body, checksum


def _verify_outputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = _load(STATE_PATH)
    audit = _load(AUDIT_PATH)
    snapshot = _load(SNAPSHOT_PATH)
    health = _load(HEALTH_PATH)

    state_body, state_checksum = _without_checksum(state, "output_checksum")
    audit_body, audit_checksum = _without_checksum(audit, "audit_checksum")
    snapshot_body, snapshot_checksum = _without_checksum(snapshot, "snapshot_checksum")
    health_body, health_checksum = _without_checksum(health, "health_checksum")

    assert _checksum(state_body) == state_checksum
    assert _checksum(audit_body) == audit_checksum
    assert _checksum(snapshot_body) == snapshot_checksum
    assert _checksum(health_body) == health_checksum

    assert state["snapshot"] == snapshot
    assert state["book_health"] == health
    assert audit["state_output_checksum"] == state_checksum
    assert audit["snapshot_checksum"] == snapshot_checksum
    assert audit["health_checksum"] == health_checksum
    return state, audit, snapshot, health


def _verify_scope(
    state: dict[str, Any],
    audit: dict[str, Any],
    snapshot: dict[str, Any],
    health: dict[str, Any],
) -> None:
    gate = _load(GATE_PATH)
    assert gate["output_checksum"] == EXPECTED_GATE
    assert gate["gate_status"] == "GO_LOT38_IMPLEMENTATION_ENTRY"
    assert gate["target_lot"] == 38
    assert gate["next_lot"] == 39
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    assert gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"

    assert state["run_context"]["code_commit"] == SOURCE_HEAD
    assert audit["code_commit"] == SOURCE_HEAD
    assert state["lineage"]["entry_gate_checksum"] == EXPECTED_GATE
    assert audit["entry_gate_checksum"] == EXPECTED_GATE
    assert state["validation_state"] == "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY"
    assert audit["validation_state"] == "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY"

    assert snapshot["bids"] == [
        {"price": "50024.9", "quantity": "0.8"},
        {"price": "50024.8", "quantity": "1.25"},
    ]
    assert snapshot["asks"] == [
        {"price": "50025.1", "quantity": "0.7"},
        {"price": "50025.2", "quantity": "1.1"},
    ]
    assert snapshot["source_bid_depth"] == snapshot["normalized_bid_depth"] == 3
    assert snapshot["source_ask_depth"] == snapshot["normalized_ask_depth"] == 3
    assert snapshot["published_bid_depth"] == snapshot["published_ask_depth"] == 2
    assert snapshot["venue_state"] == "OPEN"
    assert health["health_status"] == "HEALTHY"
    assert health["crossed"] is False
    assert health["locked"] is False
    assert health["sequence_present"] is True

    safety = state["safety"]
    assert safety == audit["safety"] == gate["safety"]
    assert safety["analysis_only"] is True
    assert safety["approved_size"] == 0
    for field in (
        "execution_allowed",
        "external_connectivity_allowed",
        "market_event_publication_allowed",
        "network_ingestion_allowed",
        "order_routing_allowed",
        "raw_data_mutation_allowed",
        "real_credentials_allowed",
        "risk_approval_allowed",
        "scenario_score_is_signal",
        "signal_generation_allowed",
        "trade_allowed",
        "used_for_decision",
    ):
        assert safety[field] is False


def _verify_quality() -> None:
    coverage = _load(COVERAGE_PATH)
    mutation = _load(MUTATION_PATH)

    assert coverage["source_head_sha"] == SOURCE_HEAD
    assert coverage["status"] == "PASS"
    assert coverage["line_coverage_percent"] == 99.61
    assert coverage["branch_coverage_percent"] == 99.35
    assert coverage["line_coverage_percent"] >= coverage["line_coverage_min_percent"] == 95.0
    assert coverage["branch_coverage_percent"] >= coverage["branch_coverage_min_percent"] == 90.0
    assert coverage["anti_flake_repetitions"] == 3

    assert mutation["source_head_sha"] == SOURCE_HEAD
    assert mutation["status"] == "PASS"
    assert mutation["evaluated_mutants"] == mutation["completed_mutants"] == 1232
    assert mutation["total_mutants"] == 1232
    assert mutation["killed_mutants"] == 1006
    assert mutation["survived_mutants"] == 226
    assert mutation["timeout_mutants"] == 0
    assert mutation["suspicious_mutants"] == 0
    assert mutation["max_children"] == 1
    assert mutation["python_hash_seed"] == "0"
    expected_score = round(100.0 * 1006 / 1232, 2)
    assert mutation["mutation_score_percent"] == expected_score == 81.66
    assert mutation["mutation_score_percent"] >= mutation["minimum_score_percent"] == 80.0
    assert mutation["mutmut_run_exit_code"] == 0
    assert mutation["mutmut_results_exit_code"] == 0


def main() -> None:
    state, audit, snapshot, health = _verify_outputs()
    _verify_scope(state, audit, snapshot, health)
    _verify_quality()
    print("LOT38_FROZEN_EVIDENCE_VALIDATED")


if __name__ == "__main__":
    main()
