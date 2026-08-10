#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_lot39_post_merge import validate as validate_lot39_post_merge  # noqa: E402

GATE_PATH = ROOT / "data/audit/lot40_v4_entry_gate.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot39.json"
STATE_PATH = ROOT / "data/audit/order_book_delta_and_sequence_reconstructor_lot39.json"
AUDIT_PATH = ROOT / "data/audit/order_book_delta_and_sequence_reconstructor_audit_lot39.json"
BOOK_PATH = ROOT / "data/audit/reconstructed_order_book_lot39.json"
FIXTURE_PATH = ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json"
COVERAGE_PATH = ROOT / "reports/lot39/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot39/mutation_summary.json"

EXPECTED_BASE = "5381a773a9d69036b38c57904b2f4a66ffb2f595"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18"
EXPECTED_STATE_CHECKSUM = "d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0"
EXPECTED_AUDIT_CHECKSUM = "1e29d0b8695a1b8825e1fc91728a6254ad93c689e1f961cfa424e6d5fed8ed41"
EXPECTED_BOOK_CHECKSUM = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_FIXTURE_SHA256 = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"

EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
}
EXPECTED_OUTPUTS = {
    "BookIntegrityDesynchronizationDetectorStateV1",
    "BookIntegrityDesynchronizationDetectorAuditV1",
    "BookIntegrityStateV1",
    "BookHealthVetoV1",
}
EXPECTED_ALLOWED = {
    "OFFLINE_BOOK_INTEGRITY_DESYNCHRONIZATION_DETECTION",
    "SEQUENCE_CONTINUITY_VALIDATION",
    "CROSSED_AND_LOCKED_STATE_VALIDATION",
    "STALE_AGE_VALIDATION",
    "CHECKSUM_INTEGRITY_VALIDATION",
    "DEPTH_COLLAPSE_DETECTION",
    "LEVEL_MONOTONICITY_VALIDATION",
    "BOOK_HEALTH_SCORE_WITH_PUBLISHED_COMPONENTS",
    "BOOK_INTEGRITY_STATE_V1",
    "BOOK_HEALTH_VETO_V1",
    "WAIT_BELOW_VERSIONED_TRADE_HEALTH_THRESHOLD",
    "BLOCK_OR_PAUSE_BELOW_VERSIONED_SYSTEM_HEALTH_THRESHOLD",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "NEGATIVE_AND_FORBIDDEN_CAPABILITY_VALIDATION",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT40",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "NETWORK_INGESTION",
    "SPREAD_DEPTH_IMBALANCE_ENGINE",
    "LIQUIDITY_ZONE_WALL_VOID_INFERENCE",
    "BOOK_RESILIENCE_REPLENISHMENT_ENGINE",
    "TRADE_AGGRESSOR_CLASSIFICATION",
    "ORDER_FLOW_DELTA_CVD_ENGINE",
    "CLASSIFICATION_CONFIDENCE_ENGINE",
    "ABSORPTION_HIDDEN_LIQUIDITY_INFERENCE",
    "VOLUME_CLUSTER_TIME_AT_LEVEL_ENGINE",
    "STOP_ZONE_LIQUIDITY_POOL_INFERENCE",
    "SWEEP_FAKEOUT_TRAP_FAILED_AUCTION_ENGINE",
    "DERIVATIVES_CONTEXT_ENGINE",
    "GAME_THEORY_SCENARIO_AGGREGATION",
    "PARTICIPANT_INTENT_AS_FACT",
    "SCENARIO_TO_SIGNAL_CONVERSION",
    "FORECAST_GENERATION",
    "SIGNAL_GENERATION",
    "RISK_APPROVAL",
    "ORDER_ROUTING",
    "TRADING",
    "EXECUTION",
}
EXPECTED_PREREQUISITES = {
    "anti_flake_repetitions": 3,
    "branch_coverage_percent": 96.97,
    "latest_implemented_lot": 39,
    "line_coverage_percent": 99.24,
    "lot39_audit_checksum": EXPECTED_AUDIT_CHECKSUM,
    "lot39_delta_fixture_checksum": EXPECTED_FIXTURE_SHA256,
    "lot39_evidence_head": "b1bf9605fe20cacca76861e3fc6941ad38ea8f23",
    "lot39_final_pr_head": "3dc7ec29bb1a4152017854581573c26465ee33a2",
    "lot39_implementation_merge": "e2b787905e126a4f8ba19c933d39550ad338ac74",
    "lot39_post_merge_audit_merge_commit": EXPECTED_BASE,
    "lot39_post_merge_verdict": "GO_LOT39_POST_MERGE",
    "lot39_reconstructed_book_checksum": EXPECTED_BOOK_CHECKSUM,
    "lot39_source_head": "203a2b2d3d69644bd67c0e583df9d0405941def6",
    "lot39_state_checksum": EXPECTED_STATE_CHECKSUM,
    "lot39_status": "IMPLEMENTED_VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY",
    "lot40_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 81.81,
    "reference_reconstructed_sequence_id": 1003,
    "reference_sequence_gap_event_absent": True,
    "reference_synchronization_state": "SYNCED",
}

LOT40_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_integrity_and_desynchronization_detector.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_integrity_and_desynchronization_detector_models.py",
    ROOT / "config/microstructure/book_integrity_desynchronization_detector_v1.json",
    ROOT / "contracts/schemas/book_integrity_desynchronization_detector_state_v1.schema.json",
    ROOT / "contracts/schemas/book_integrity_desynchronization_detector_audit_v1.schema.json",
    ROOT / "contracts/schemas/book_integrity_state_v1.schema.json",
    ROOT / "contracts/schemas/book_health_veto_v1.schema.json",
    ROOT / "scripts/run_lot40_book_integrity_desynchronization_detector.py",
    ROOT / "scripts/validate_lot40.py",
    ROOT / "tests/test_lot40_book_integrity_desynchronization_detector.py",
    ROOT / "data/audit/book_integrity_desynchronization_detector_lot40.json",
    ROOT / "docs/LOT_40_BOOK_INTEGRITY_DESYNCHRONIZATION_DETECTOR.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_40.md",
)
LOT41_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_models.py",
    ROOT / "scripts/run_lot41_spread_depth_and_imbalance_engine.py",
    ROOT / "scripts/validate_lot41.py",
    ROOT / "docs/LOT_41_SPREAD_DEPTH_AND_IMBALANCE_ENGINE.md",
)


class Lot40EntryGateError(RuntimeError):
    """Raised when the Lot 40 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot40EntryGateError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def verify_checksum(
    path: Path,
    field: str,
    expected: str,
    label: str,
) -> dict[str, Any]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(field, None)
    require(checksum == expected, f"{label} checksum value changed")
    require(canonical_checksum(body) == checksum, f"{label} checksum mismatch")
    return payload


def validate_gate_checksum(gate: dict[str, Any]) -> None:
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    require(checksum == EXPECTED_GATE_CHECKSUM, "Lot 40 gate checksum value changed")
    require(canonical_checksum(body) == checksum, "Lot 40 gate checksum mismatch")


def canonical_roadmap_record() -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= 41, "canonical roadmap Lot 40 line missing")
    record = json.loads(lines[40])
    require(isinstance(record, dict), "canonical Lot 40 roadmap record must be object")
    return record


def validate_roadmap(gate: dict[str, Any]) -> None:
    record = canonical_roadmap_record()
    expected = {
        "lot_id": "Lot 40",
        "lot_number": 40,
        "title": "Book Integrity / Desynchronization Detector",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(record.get(field) == value, f"canonical Lot 40 field changed: {field}")
    require(set(record.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 40 inputs changed")
    require(set(record.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 40 outputs changed")
    require(len(record.get("processing_sequence", [])) >= 7, "Lot 40 sequence incomplete")
    require(len(record.get("acceptance_tests", [])) >= 10, "Lot 40 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 41, "Lot 40 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 40", "Lot 40 roadmap lot binding changed")
    require(binding["title"] == expected["title"], "Lot 40 roadmap title binding changed")


def validate_previous_release() -> dict[str, object]:
    previous = validate_lot39_post_merge()
    require(previous["status"] == "PASS", "Lot 39 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT39_POST_MERGE", "Lot 39 audit verdict changed")
    require(previous["project_version"] == "0.39.0", "Lot 39 audited version changed")
    require(previous["latest_implemented_lot"] == 39, "latest implemented lot must be 39")
    require(previous["next_lot"] == 40, "Lot 39 audit next lot changed")
    require(previous["next_lot_status"] == "PLANNED_LOCKED", "Lot 40 is not locked")
    return previous


def validate_lifecycle() -> None:
    lifecycle = load(LIFECYCLE_PATH)
    require(lifecycle["latest_implemented_lot"] == 39, "lifecycle latest lot must remain 39")
    require(
        lifecycle["lots"]["39"]["status"]
        == "IMPLEMENTED_VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY",
        "Lot 39 lifecycle status changed",
    )
    require(
        lifecycle["lots"]["40"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 40 lifecycle must remain exactly locked before gate merge",
    )


def validate_lot39_artifacts_and_quality() -> None:
    state = verify_checksum(STATE_PATH, "output_checksum", EXPECTED_STATE_CHECKSUM, "Lot 39 state")
    audit = verify_checksum(AUDIT_PATH, "audit_checksum", EXPECTED_AUDIT_CHECKSUM, "Lot 39 audit")
    book = verify_checksum(BOOK_PATH, "book_checksum", EXPECTED_BOOK_CHECKSUM, "Lot 39 book")
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)

    require(file_sha256(FIXTURE_PATH) == EXPECTED_FIXTURE_SHA256, "Lot 39 delta fixture changed")
    require(state["reconstructed_book"] == book, "Lot 39 state/book mismatch")
    require(state["sequence_gap_event"] is None, "Lot 39 healthy state has gap evidence")
    require(state["synchronization_state"] == "SYNCED", "Lot 39 state is not SYNCED")
    require(audit["synchronization_state"] == "SYNCED", "Lot 39 audit is not SYNCED")
    require(audit["state_output_checksum"] == EXPECTED_STATE_CHECKSUM, "Lot 39 audit/state link changed")
    require(
        audit["reconstructed_book_checksum"] == EXPECTED_BOOK_CHECKSUM,
        "Lot 39 audit/book link changed",
    )
    require(audit["sequence_gap_event_checksum"] is None, "Lot 39 audit unexpectedly links gap")
    require(state["delta_fixture_checksum"] == EXPECTED_FIXTURE_SHA256, "Lot 39 fixture link changed")
    require(audit["delta_fixture_checksum"] == EXPECTED_FIXTURE_SHA256, "Lot 39 audit fixture link changed")
    require(book["synchronization_state"] == "SYNCED", "reference reconstructed book is not SYNCED")
    require(book["sequence_id"] == 1003, "reference reconstructed sequence changed")
    require(coverage["status"] == "PASS", "Lot 39 coverage evidence not PASS")
    require(coverage["line_coverage_percent"] == 99.24, "Lot 39 line coverage changed")
    require(coverage["branch_coverage_percent"] == 96.97, "Lot 39 branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "Lot 39 anti-flake evidence changed")
    require(mutation["status"] == "PASS", "Lot 39 mutation evidence not PASS")
    require(mutation["mutation_score_percent"] == 81.81, "Lot 39 mutation score changed")
    require(mutation["killed_mutants"] == 1651, "Lot 39 killed mutant count changed")
    require(mutation["total_mutants"] == 2018, "Lot 39 total mutant count changed")
    require(mutation["timeout_mutants"] == 0, "Lot 39 mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "Lot 39 suspicious mutant count changed")
    for path in (
        ROOT / "contracts/schemas/order_book_delta_v1.schema.json",
        ROOT / "contracts/schemas/reconstructed_order_book_v1.schema.json",
        ROOT / "contracts/schemas/sequence_gap_event_v1.schema.json",
    ):
        require(path.exists(), f"certified Lot 39 contract missing: {path}")


def validate_prerequisites(gate: dict[str, Any]) -> None:
    require(gate["prerequisites"] == EXPECTED_PREREQUISITES, "Lot 40 prerequisite evidence changed")


def validate_scope(gate: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version": "lot40-v4-entry-gate-v1",
        "target_lot": 40,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.39.0",
        "gate_status": "GO_LOT40_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT40",
        "implementation_started": False,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "next_lot": 41,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected_fields.items():
        require(gate[field] == value, f"Lot 40 gate field changed: {field}")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "Lot 40 gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "Lot 40 gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "Lot 40 allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "Lot 40 forbidden scope changed")
    require(
        gate["quality_gates"]
        == {
            "line_coverage_min_percent": 95,
            "branch_coverage_min_percent": 90,
            "mutation_score_min_percent": 80,
            "anti_flake_repetitions": 3,
        },
        "Lot 40 quality gates changed",
    )


def validate_safety(gate: dict[str, Any]) -> None:
    safety = gate["safety"]
    require(safety["analysis_only"] is True, "Lot 40 analysis-only boundary changed")
    require(safety["approved_size"] == 0, "Lot 40 approved size changed")
    require(
        safety["participant_behavior_inference_explicitly_labeled"] is True,
        "Lot 40 participant-inference labeling changed",
    )
    for field in (
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "market_event_publication_allowed",
        "raw_data_mutation_allowed",
        "scenario_score_is_signal",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
        require(safety[field] is False, f"Lot 40 permission enabled: {field}")


def validate_preimplementation_boundary() -> None:
    for path in LOT40_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 40 implementation started before gate merge: {path}")
    for path in LOT41_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 41 implementation exists before Lot 40: {path}")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_gate_checksum(gate)
    validate_roadmap(gate)
    validate_previous_release()
    validate_lifecycle()
    validate_lot39_artifacts_and_quality()
    validate_prerequisites(gate)
    validate_scope(gate)
    validate_safety(gate)
    validate_preimplementation_boundary()
    result: dict[str, object] = {
        "schema_version": "lot40-v4-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": gate["gate_status"],
        "base_commit": gate["base_commit"],
        "current_version": gate["current_version"],
        "output_checksum": gate["output_checksum"],
        "target_lot": 40,
        "next_locked_lot": 41,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot40EntryGateError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT40 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
