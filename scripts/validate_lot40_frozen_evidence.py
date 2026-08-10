#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "b9a18a8aaef858b985c3f75ef2aa8955ec521e9f"
EVIDENCE_HEAD = "ea04fe826261eeed5a59eea60265b38b68404b6b"
STATE_PATH = ROOT / "data/audit/book_integrity_desynchronization_detector_lot40.json"
AUDIT_PATH = ROOT / "data/audit/book_integrity_desynchronization_detector_audit_lot40.json"
INTEGRITY_PATH = ROOT / "data/audit/book_integrity_state_lot40.json"
VETO_PATH = ROOT / "data/audit/book_health_veto_lot40.json"
COVERAGE_PATH = ROOT / "reports/lot40/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot40/mutation_summary.json"

EXPECTED_STATE = "e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477"
EXPECTED_AUDIT = "978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c"
EXPECTED_INTEGRITY = "35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a"
EXPECTED_VETO = "000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc"
EXPECTED_GATE = "23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18"
EXPECTED_LOT39_STATE = "d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0"
EXPECTED_LOT39_AUDIT = "1e29d0b8695a1b8825e1fc91728a6254ad93c689e1f961cfa424e6d5fed8ed41"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_LOT39_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"

LOT41_FORBIDDEN_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_models.py",
    ROOT / "scripts/run_lot41_spread_depth_and_imbalance_engine.py",
    ROOT / "scripts/validate_lot41.py",
    ROOT / "docs/LOT_41_SPREAD_DEPTH_AND_IMBALANCE_ENGINE.md",
)


class Lot40FrozenEvidenceError(RuntimeError):
    """Raised when frozen Lot 40 evidence no longer matches certification."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot40FrozenEvidenceError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(actual == expected, f"{label} certified checksum changed")
    require(checksum(body) == expected, f"{label} checksum mismatch")


def expected_safety() -> dict[str, object]:
    return {
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


def validate_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    integrity: dict[str, Any],
    veto: dict[str, Any],
) -> None:
    require(state["book_integrity"] == integrity, "state/integrity payload mismatch")
    require(state["book_health_veto"] == veto, "state/veto payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["integrity_checksum"] == EXPECTED_INTEGRITY, "audit/integrity link changed")
    require(audit["veto_checksum"] == EXPECTED_VETO, "audit/veto link changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["code_commit"] == SOURCE_HEAD, "audit source head changed")


def validate_lineage(state: dict[str, Any], audit: dict[str, Any]) -> None:
    lineage = state["lineage"]
    expected = {
        "entry_gate_checksum": EXPECTED_GATE,
        "lot39_state_checksum": EXPECTED_LOT39_STATE,
        "lot39_audit_checksum": EXPECTED_LOT39_AUDIT,
        "lot39_reconstructed_book_checksum": EXPECTED_LOT39_BOOK,
        "lot39_delta_fixture_checksum": EXPECTED_LOT39_FIXTURE,
    }
    for field, value in expected.items():
        require(lineage[field] == value, f"lineage changed: {field}")
        require(audit[field] == value, f"audit lineage changed: {field}")


def validate_health(integrity: dict[str, Any], veto: dict[str, Any]) -> None:
    require(integrity["health_status"] == "HEALTHY", "reference health is not HEALTHY")
    require(integrity["book_health_score"] == "100", "reference health score changed")
    require(integrity["synchronization_state"] == "SYNCED", "reference book not SYNCED")
    require(integrity["sequence_id"] == 1003, "reference sequence changed")
    require(integrity["bid_depth_levels"] == 2, "reference bid depth changed")
    require(integrity["ask_depth_levels"] == 3, "reference ask depth changed")
    require(integrity["stale_age_us"] == 30000, "reference stale age changed")
    require(integrity["crossed"] is False, "reference book became crossed")
    require(integrity["locked"] is False, "reference book became locked")
    require(integrity["checksum_valid"] is True, "reference checksum invalid")
    require(integrity["level_monotonicity_valid"] is True, "reference levels invalid")
    require(veto["consequence"] == "NONE", "reference consequence changed")
    require(veto["veto_active"] is False, "reference veto unexpectedly active")
    require(veto["critical_veto_active"] is False, "critical veto unexpectedly active")
    require(veto["system_health_threshold"] == "80", "system threshold changed")
    require(veto["trade_health_threshold"] == "90", "trade threshold changed")
    require(veto["critical_failure_consequence"] == "BLOCK", "critical consequence changed")
    require(veto["system_threshold_consequence"] == "PAUSE", "system consequence changed")


def validate_components(integrity: dict[str, Any]) -> None:
    components = integrity["components"]
    require(isinstance(components, list) and len(components) == 6, "component set changed")
    expected = (
        ("SEQUENCE_CONTINUITY", True, "20"),
        ("CROSSED_LOCKED_STATE", True, "20"),
        ("FRESHNESS", False, "15"),
        ("CHECKSUM_INTEGRITY", True, "20"),
        ("DEPTH_INTEGRITY", False, "20"),
        ("LEVEL_MONOTONICITY", True, "5"),
    )
    score = Decimal("0")
    for component, (name, critical, weight) in zip(components, expected, strict=True):
        require(component["name"] == name, f"component order changed: {name}")
        require(component["critical"] is critical, f"component criticality changed: {name}")
        require(component["passed"] is True, f"reference component failed: {name}")
        require(component["weight"] == weight, f"component weight changed: {name}")
        require(component["score"] == weight, f"component score changed: {name}")
        score += Decimal(component["score"])
    require(score == Decimal("100"), "component score total changed")


def validate_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    integrity = load(INTEGRITY_PATH)
    veto = load(VETO_PATH)
    verify(state, "output_checksum", EXPECTED_STATE, "Lot 40 state")
    verify(audit, "audit_checksum", EXPECTED_AUDIT, "Lot 40 audit")
    verify(integrity, "integrity_checksum", EXPECTED_INTEGRITY, "Lot 40 integrity")
    verify(veto, "veto_checksum", EXPECTED_VETO, "Lot 40 veto")
    validate_links(state, audit, integrity, veto)
    validate_lineage(state, audit)
    validate_health(integrity, veto)
    validate_components(integrity)
    require(state["validation_state"] == "VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY", "validation state changed")
    require(state["safety"] == expected_safety(), "state safety boundary changed")
    require(audit["safety"] == expected_safety(), "audit safety boundary changed")
    return state, audit, integrity, veto


def validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 97.31, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 91.24, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["completed_mutants"] == 1555, "mutation completed count changed")
    require(mutation["evaluated_mutants"] == 1555, "mutation evaluated count changed")
    require(mutation["total_mutants"] == 1555, "mutation total changed")
    require(mutation["killed_mutants"] == 1280, "mutation killed count changed")
    require(mutation["survived_mutants"] == 275, "mutation survivor count changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "mutation suspicious count changed")
    require(mutation["mutation_score_percent"] == 82.32, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below threshold")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    require(mutation["mutmut_run_exit_code"] == 0, "mutmut run exit code changed")
    require(mutation["mutmut_results_exit_code"] == 0, "mutmut results exit code changed")
    return coverage, mutation


def validate_lot41_lock() -> None:
    for path in LOT41_FORBIDDEN_PATHS:
        require(not path.exists(), f"Lot 41 implementation present before Lot 40 audit: {path}")


def validate() -> dict[str, object]:
    state, audit, integrity, veto = validate_artifacts()
    coverage, mutation = validate_quality()
    validate_lot41_lock()
    result: dict[str, object] = {
        "schema_version": "lot40-frozen-evidence-validation-v1",
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "integrity_checksum": integrity["integrity_checksum"],
        "veto_checksum": veto["veto_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "health_status": integrity["health_status"],
        "book_health_score": integrity["book_health_score"],
        "consequence": veto["consequence"],
        "lot41_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot40FrozenEvidenceError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT40 FROZEN EVIDENCE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
