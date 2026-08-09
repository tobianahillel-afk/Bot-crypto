#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from scripts.validate_lot38_post_merge import validate as validate_lot38_post_merge

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot39_v4_entry_gate.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot38.json"
STATE_PATH = ROOT / "data/audit/order_book_l2_snapshot_engine_lot38.json"
AUDIT_PATH = ROOT / "data/audit/order_book_l2_snapshot_engine_audit_lot38.json"
SNAPSHOT_PATH = ROOT / "data/audit/order_book_snapshot_lot38.json"
HEALTH_PATH = ROOT / "data/audit/book_health_state_lot38.json"
COVERAGE_PATH = ROOT / "reports/lot38/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot38/mutation_summary.json"
SNAPSHOT_SCHEMA_PATH = ROOT / "contracts/schemas/order_book_snapshot_v1.schema.json"
PLANNED_DELTA_SCHEMA_PATH = ROOT / "contracts/schemas/order_book_delta_v1.schema.json"

EXPECTED_BASE = "5d0695f248b1bd4e6af5621f8a3d448cc0430050"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "250c67574a8add382915c1b8f0b104f801bd91757c829c3d7d336f8e2e22e0ab"
EXPECTED_STATE_CHECKSUM = "7610fc6ea73e49075a1b8611f8344c7b9c8fcf8ab02f55612d914eeac0ccda9b"
EXPECTED_AUDIT_CHECKSUM = "0290637591e1a8c4cd7a9975868932b65afa28fb75d6843340dbeea67a682d20"
EXPECTED_SNAPSHOT_CHECKSUM = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
EXPECTED_HEALTH_CHECKSUM = "58b56f7cf21aa74dd67620b8dd6e19cad11b77412cdcc3103b6d60bd15703837"
EXPECTED_CONFIG_CHECKSUM = "60899c1393e111315395dd0e149f3a468972e9e99ca5a1322b8a97ec786497db"

EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
    "OrderBookSnapshotV1",
    "OrderBookDeltaV1",
}
EXPECTED_OUTPUTS = {
    "OrderBookDeltaSequenceReconstructorStateV1",
    "OrderBookDeltaSequenceReconstructorAuditV1",
    "ReconstructedOrderBookV1",
    "SequenceGapEventV1",
}
EXPECTED_ALLOWED = {
    "ORDER_BOOK_DELTA_V1_CONTRACT_DEFINITION",
    "OFFLINE_SNAPSHOT_DELTA_SEQUENCE_RECONSTRUCTION",
    "STRICT_SEQUENCE_AND_PREV_SEQUENCE_VALIDATION",
    "ZERO_QUANTITY_LEVEL_DELETION",
    "NEGATIVE_QUANTITY_REJECTION",
    "GAP_DUPLICATE_REORDER_DETECTION",
    "RESYNC_REQUIRED_ON_GAP_AMBIGUOUS_DUPLICATE_OR_CHECKSUM_MISMATCH",
    "SYNCED_ONLY_RECONSTRUCTED_BOOK_PUBLICATION",
    "RECONSTRUCTED_BOOK_CHECKSUM",
    "SEQUENCE_GAP_EVENT",
    "EXACT_SNAPSHOT_PLUS_DELTA_REPLAY",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "NEGATIVE_AND_FORBIDDEN_CAPABILITY_VALIDATION",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT39",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "NETWORK_INGESTION",
    "BOOK_INTEGRITY_DESYNCHRONIZATION_ENGINE",
    "SPREAD_DEPTH_IMBALANCE_ANALYTICS",
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
    "branch_coverage_percent": 99.35,
    "latest_implemented_lot": 38,
    "line_coverage_percent": 99.61,
    "lot38_audit_checksum": EXPECTED_AUDIT_CHECKSUM,
    "lot38_book_health_checksum": EXPECTED_HEALTH_CHECKSUM,
    "lot38_config_checksum": EXPECTED_CONFIG_CHECKSUM,
    "lot38_evidence_head": "ef197437d13012644e48a9044cf0883bd17700fb",
    "lot38_implementation_merge": "e4b44d27886ade86f9d1d05d480b89010b03700d",
    "lot38_post_merge_audit_merge_commit": EXPECTED_BASE,
    "lot38_snapshot_checksum": EXPECTED_SNAPSHOT_CHECKSUM,
    "lot38_source_head": "b74bea4329d5e5cb7cf2452058b684ea5a5df13c",
    "lot38_state_checksum": EXPECTED_STATE_CHECKSUM,
    "lot38_status": "IMPLEMENTED_VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY",
    "lot39_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 81.66,
    "order_book_snapshot_contract_name": "OrderBookSnapshotV1",
    "order_book_snapshot_schema": "contracts/schemas/order_book_snapshot_v1.schema.json",
    "planned_delta_contract_name": "OrderBookDeltaV1",
    "planned_delta_contract_schema": "contracts/schemas/order_book_delta_v1.schema.json",
    "reference_book_health_status": "HEALTHY",
    "reference_book_sequence_present": True,
}

LOT39_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor.py",
    ROOT / "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor_validation.py",
    ROOT / "scripts/run_lot39_order_book_delta_and_sequence_reconstructor.py",
    ROOT / "scripts/validate_lot39.py",
    ROOT / "data/audit/order_book_delta_and_sequence_reconstructor_lot39.json",
    ROOT / "docs/LOT_39_ORDER_BOOK_DELTA_AND_SEQUENCE_RECONSTRUCTOR.md",
)
LOT40_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/book_integrity_and_desynchronization_detector.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector.py",
    ROOT / "scripts/run_lot40_book_integrity_and_desynchronization_detector.py",
    ROOT / "scripts/validate_lot40.py",
)


class Lot39EntryGateError(RuntimeError):
    """Raised when the Lot 39 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot39EntryGateError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def verify_checksum(path: Path, field: str, expected: str, label: str) -> dict[str, Any]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(field, None)
    require(checksum == expected, f"{label} checksum value changed")
    require(canonical_checksum(body) == checksum, f"{label} checksum mismatch")
    return payload


def validate_gate_checksum(gate: dict[str, Any]) -> None:
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    require(checksum == EXPECTED_GATE_CHECKSUM, "Lot 39 gate checksum value changed")
    require(canonical_checksum(body) == checksum, "Lot 39 gate checksum mismatch")


def canonical_roadmap_record() -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= 40, "canonical roadmap Lot 39 line missing")
    record = json.loads(lines[39])
    require(isinstance(record, dict), "canonical Lot 39 roadmap record must be object")
    return record


def validate_roadmap(gate: dict[str, Any]) -> None:
    record = canonical_roadmap_record()
    expected = {
        "lot_id": "Lot 39",
        "lot_number": 39,
        "title": "Order Book Delta & Sequence Reconstructor",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(record.get(field) == value, f"canonical Lot 39 field changed: {field}")
    require(set(record.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 39 inputs changed")
    require(set(record.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 39 outputs changed")
    require(len(record.get("processing_sequence", [])) >= 8, "Lot 39 sequence incomplete")
    require(len(record.get("acceptance_tests", [])) >= 10, "Lot 39 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 40, "Lot 39 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 39", "Lot 39 roadmap lot binding changed")
    require(binding["title"] == expected["title"], "Lot 39 roadmap title binding changed")


def validate_previous_release() -> dict[str, Any]:
    previous = validate_lot38_post_merge()
    require(previous["status"] == "PASS", "Lot 38 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT38_POST_MERGE", "Lot 38 audit verdict changed")
    require(previous["project_version"] == "0.38.0", "Lot 38 audited version changed")
    require(previous["latest_implemented_lot"] == 38, "latest implemented lot must be 38")
    require(previous["next_lot"] == 39, "Lot 38 audit next lot changed")
    require(previous["next_lot_status"] == "PLANNED_LOCKED", "Lot 39 is not locked")
    return previous


def validate_lifecycle() -> None:
    lifecycle = load(LIFECYCLE_PATH)
    require(lifecycle["latest_implemented_lot"] == 38, "lifecycle latest lot must remain 38")
    require(
        lifecycle["lots"]["38"]["status"]
        == "IMPLEMENTED_VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY",
        "Lot 38 lifecycle status changed",
    )
    require(
        lifecycle["lots"]["39"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 39 lifecycle must remain exactly locked before gate merge",
    )


def validate_lot38_artifacts_and_quality() -> None:
    state = verify_checksum(STATE_PATH, "output_checksum", EXPECTED_STATE_CHECKSUM, "Lot 38 state")
    audit = verify_checksum(AUDIT_PATH, "audit_checksum", EXPECTED_AUDIT_CHECKSUM, "Lot 38 audit")
    snapshot = verify_checksum(
        SNAPSHOT_PATH, "snapshot_checksum", EXPECTED_SNAPSHOT_CHECKSUM, "Lot 38 snapshot"
    )
    health = verify_checksum(
        HEALTH_PATH, "health_checksum", EXPECTED_HEALTH_CHECKSUM, "Lot 38 health"
    )
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)

    require(state["snapshot"] == snapshot, "Lot 38 state/snapshot mismatch")
    require(state["book_health"] == health, "Lot 38 state/health mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE_CHECKSUM, "Lot 38 audit/state link changed")
    require(audit["snapshot_checksum"] == EXPECTED_SNAPSHOT_CHECKSUM, "Lot 38 audit/snapshot link changed")
    require(audit["health_checksum"] == EXPECTED_HEALTH_CHECKSUM, "Lot 38 audit/health link changed")
    require(audit["config_checksum"] == EXPECTED_CONFIG_CHECKSUM, "Lot 38 config binding changed")
    require(snapshot["venue_state"] == "OPEN", "Lot 38 reference venue must be OPEN")
    require(snapshot["sequence_id"] == 1001, "Lot 38 reference sequence changed")
    require(bool(snapshot["sequence_anchor"]), "Lot 38 sequence anchor missing")
    require(health["health_status"] == "HEALTHY", "Lot 38 reference book is not healthy")
    require(health["crossed"] is False, "Lot 38 reference book is crossed")
    require(health["locked"] is False, "Lot 38 reference book is locked")
    require(health["sequence_present"] is True, "Lot 38 reference sequence missing")
    require(coverage["status"] == "PASS", "Lot 38 coverage evidence not PASS")
    require(coverage["line_coverage_percent"] == 99.61, "Lot 38 line coverage changed")
    require(coverage["branch_coverage_percent"] == 99.35, "Lot 38 branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "Lot 38 anti-flake evidence changed")
    require(mutation["status"] == "PASS", "Lot 38 mutation evidence not PASS")
    require(mutation["mutation_score_percent"] == 81.66, "Lot 38 mutation score changed")
    require(mutation["killed_mutants"] == 1006, "Lot 38 killed mutant count changed")
    require(mutation["total_mutants"] == 1232, "Lot 38 total mutant count changed")
    require(mutation["timeout_mutants"] == 0, "Lot 38 mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "Lot 38 suspicious mutant count changed")
    require(SNAPSHOT_SCHEMA_PATH.exists(), "OrderBookSnapshotV1 schema missing")


def validate_prerequisites(gate: dict[str, Any]) -> None:
    require(gate["prerequisites"] == EXPECTED_PREREQUISITES, "Lot 39 prerequisite evidence changed")


def validate_scope(gate: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version": "lot39-v4-entry-gate-v1",
        "target_lot": 39,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.38.0",
        "gate_status": "GO_LOT39_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT39",
        "implementation_started": False,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "next_lot": 40,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected_fields.items():
        require(gate[field] == value, f"Lot 39 gate field changed: {field}")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "Lot 39 gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "Lot 39 gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "Lot 39 allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "Lot 39 forbidden scope changed")
    require(
        gate["quality_gates"]
        == {
            "line_coverage_min_percent": 95,
            "branch_coverage_min_percent": 90,
            "mutation_score_min_percent": 80,
            "anti_flake_repetitions": 3,
        },
        "Lot 39 quality gates changed",
    )


def validate_safety(gate: dict[str, Any]) -> None:
    safety = gate["safety"]
    require(safety["analysis_only"] is True, "Lot 39 analysis-only boundary changed")
    require(safety["approved_size"] == 0, "Lot 39 approved size changed")
    require(
        safety["participant_behavior_inference_explicitly_labeled"] is True,
        "Lot 39 participant-inference labeling changed",
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
        require(safety[field] is False, f"Lot 39 permission enabled: {field}")


def validate_preimplementation_boundary() -> None:
    for path in LOT39_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 39 implementation started before gate merge: {path}")
    require(not PLANNED_DELTA_SCHEMA_PATH.exists(), "OrderBookDeltaV1 schema exists before Lot 39 gate merge")
    for path in LOT40_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 40 implementation exists before Lot 39: {path}")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_gate_checksum(gate)
    validate_roadmap(gate)
    validate_previous_release()
    validate_lifecycle()
    validate_lot38_artifacts_and_quality()
    validate_prerequisites(gate)
    validate_scope(gate)
    validate_safety(gate)
    validate_preimplementation_boundary()
    result: dict[str, object] = {
        "schema_version": "lot39-v4-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": gate["gate_status"],
        "base_commit": gate["base_commit"],
        "current_version": gate["current_version"],
        "output_checksum": gate["output_checksum"],
        "target_lot": 39,
        "next_locked_lot": 40,
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
        Lot39EntryGateError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT39 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
