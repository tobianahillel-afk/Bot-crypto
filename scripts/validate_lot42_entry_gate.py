#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_lot41_post_merge import validate as validate_lot41_post_merge  # noqa: E402

GATE_PATH = ROOT / "data/audit/lot42_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot42_v4_entry_gate_v1.schema.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot41.json"
DOC_PATH = ROOT / "docs/LOT_42_V4_ENTRY_GATE.md"
REPORT_PATH = ROOT / "reports/lot_42_v4_entry_gate_report.md"

EXPECTED_BASE = "2b4186aa0bac2f60819361958e6eff215699ab53"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "7ab3b17a74d30866fbec4ec15acfe608a9545e8831d80dcb39db2d059e293924"
EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
}
EXPECTED_OUTPUTS = {
    "LiquidityZonesWallsVoidsEngineStateV1",
    "LiquidityZonesWallsVoidsEngineAuditV1",
    "LiquidityZoneSetV1",
}
EXPECTED_ALLOWED = {
    "ADJACENT_LEVEL_CLUSTERING_BY_VERSIONED_BPS_DISTANCE",
    "BILATERAL_LIQUIDITY_VOID_DETECTION",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "DISPLAYED_WALL_CLASSIFICATION",
    "DISTANCE_TO_MID_MEASUREMENT",
    "FRESHNESS_AND_PERSISTENCE_EXPIRY",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT42",
    "LIQUIDITY_VOID_CLASSIFICATION",
    "LIQUIDITY_ZONE_SET_V1",
    "NO_PARTICIPANT_INTENT_ASSERTION",
    "OFFLINE_LIQUIDITY_ZONE_WALL_VOID_ANALYSIS",
    "PERSISTENT_ZONE_CLASSIFICATION",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "ZONE_CANCELLATION_RATE_MEASUREMENT",
    "ZONE_NOTIONAL_MEASUREMENT",
    "ZONE_PERSISTENCE_MEASUREMENT",
    "ZONE_REPLENISHMENT_MEASUREMENT",
}
EXPECTED_FORBIDDEN = {
    "ABSORPTION_HIDDEN_LIQUIDITY_INFERENCE",
    "BOOK_RESILIENCE_REPLENISHMENT_ENGINE",
    "CANCELLATION_INTENT_INFERENCE",
    "CLASSIFICATION_CONFIDENCE_ENGINE",
    "DERIVATIVES_CONTEXT_ENGINE",
    "EXECUTION",
    "EXTERNAL_NETWORK_ACCESS",
    "FORECAST_GENERATION",
    "GAME_THEORY_SCENARIO_AGGREGATION",
    "LIVE_EXCHANGE_DATA",
    "NETWORK_INGESTION",
    "ORDER_FLOW_DELTA_CVD_ENGINE",
    "ORDER_ROUTING",
    "PARTICIPANT_INTENT_AS_FACT",
    "REAL_CREDENTIALS",
    "RISK_APPROVAL",
    "SCENARIO_TO_SIGNAL_CONVERSION",
    "SIGNAL_GENERATION",
    "STOP_ZONE_LIQUIDITY_POOL_INFERENCE",
    "SWEEP_FAKEOUT_TRAP_FAILED_AUCTION_ENGINE",
    "TRADE_AGGRESSOR_CLASSIFICATION",
    "TRADING",
    "VOLUME_CLUSTER_TIME_AT_LEVEL_ENGINE",
}
EXPECTED_PREREQUISITES: dict[str, object] = {
    "anti_flake_repetitions": 3,
    "branch_coverage_percent": 100.0,
    "latest_implemented_lot": 41,
    "line_coverage_percent": 100.0,
    "lot41_audit_checksum": "af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd",
    "lot41_evidence_head": "7ada0ca6c4d439505ef453b988dedd4aa96c1a32",
    "lot41_feature_checksum": "77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5",
    "lot41_final_pr_head": "89ae244db77f16f31d226a7494d78b65b904dcd9",
    "lot41_gate_merge": "75822f8ea7c6f67f73649d2f43be6efba840ab67",
    "lot41_implementation_merge": "a253ce35c97303e8b8c65707c07597e996b3a832",
    "lot41_post_merge_audit_merge_commit": "2b4186aa0bac2f60819361958e6eff215699ab53",
    "lot41_post_merge_verdict": "GO_LOT41_POST_MERGE",
    "lot41_source_head": "14c0d8da1b02d076b3c43a07a34ac96c673018b0",
    "lot41_state_checksum": "23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573",
    "lot41_status": "IMPLEMENTED_VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY",
    "lot42_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 81.93,
    "reference_book_health_consequence": "NONE",
    "reference_book_health_score": "100",
    "reference_book_health_status": "HEALTHY",
    "reference_reconstructed_sequence_id": 1003,
}
EXPECTED_QUALITY = {
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
    "participant_behavior_inference_explicitly_labeled": True,
    "raw_data_mutation_allowed": False,
    "real_credentials_allowed": False,
    "risk_approval_allowed": False,
    "scenario_score_is_signal": False,
    "signal_generation_allowed": False,
    "trade_allowed": False,
    "used_for_decision": False,
}

LOT42_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py",
    ROOT
    / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_validation.py",
    ROOT / "config/microstructure/liquidity_zones_walls_and_voids_engine_v1.json",
    ROOT / "contracts/schemas/liquidity_zones_walls_voids_engine_state_v1.schema.json",
    ROOT / "contracts/schemas/liquidity_zones_walls_voids_engine_audit_v1.schema.json",
    ROOT / "contracts/schemas/liquidity_zone_set_v1.schema.json",
    ROOT / "scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py",
    ROOT / "scripts/validate_lot42.py",
    ROOT / "scripts/validate_lot42_frozen_evidence.py",
    ROOT / "scripts/validate_lot42_no_connectivity.py",
    ROOT / "tests/test_lot42_liquidity_zones_walls_and_voids_engine.py",
    ROOT / "tests/test_lot42_schema_contracts.py",
    ROOT / "tests/test_lot42_validation_contracts.py",
    ROOT / "data/audit/liquidity_zones_walls_and_voids_engine_lot42.json",
    ROOT / "data/audit/liquidity_zones_walls_and_voids_engine_audit_lot42.json",
    ROOT / "data/audit/liquidity_zone_set_lot42.json",
    ROOT / "reports/lot42/coverage_summary.json",
    ROOT / "reports/lot42/mutation_summary.json",
    ROOT / "reports/lot_42_liquidity_zones_walls_and_voids_engine_report.md",
    ROOT / "docs/LOT_42_LIQUIDITY_ZONES_WALLS_AND_VOIDS_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_42.md",
)
LOT43_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    ROOT / "config/microstructure/book_resilience_and_replenishment_engine_v1.json",
    ROOT / "scripts/run_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "scripts/validate_lot43.py",
    ROOT / "tests/test_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "docs/LOT_43_BOOK_RESILIENCE_AND_REPLENISHMENT_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_43.md",
)


class Lot42EntryGateError(RuntimeError):
    """Raised when the Lot 42 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot42EntryGateError(message)


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


def roadmap_record(source_line: int) -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= source_line, f"canonical roadmap line {source_line} missing")
    record = json.loads(lines[source_line - 1])
    require(isinstance(record, dict), f"canonical roadmap line {source_line} must be object")
    return record


def validate_roadmap(gate: dict[str, Any]) -> None:
    lot42 = roadmap_record(43)
    expected = {
        "lot_id": "Lot 42",
        "lot_number": 42,
        "title": "Liquidity Zones, Walls & Voids Engine",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(lot42.get(field) == value, f"canonical Lot 42 field changed: {field}")
    require(set(lot42.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 42 inputs changed")
    require(set(lot42.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 42 outputs changed")
    require(len(lot42.get("processing_sequence", [])) >= 8, "Lot 42 processing sequence incomplete")
    require(len(lot42.get("acceptance_tests", [])) >= 10, "Lot 42 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 43, "Lot 42 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 42", "Lot 42 roadmap lot binding changed")
    require(binding["title"] == expected["title"], "Lot 42 roadmap title binding changed")


def validate_next_roadmap_lock() -> None:
    lot43 = roadmap_record(44)
    expected = {
        "lot_id": "Lot 43",
        "lot_number": 43,
        "title": "Book Resilience & Replenishment Engine",
        "status": "PLANNED_LOCKED",
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected.items():
        require(lot43.get(field) == value, f"canonical Lot 43 field changed: {field}")


def validate_previous_release() -> None:
    previous = validate_lot41_post_merge()
    require(previous["status"] == "PASS", "Lot 41 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT41_POST_MERGE", "Lot 41 audit verdict changed")
    require(previous["project_version"] == "0.41.0", "Lot 41 audited version changed")
    require(previous["latest_implemented_lot"] == 41, "latest implemented lot must be 41")
    require(previous["next_lot"] == 42, "Lot 41 audit next lot changed")
    require(previous["next_lot_status"] == "PLANNED_LOCKED", "Lot 42 is not locked")


def validate_lifecycle() -> None:
    lifecycle = load(LIFECYCLE_PATH)
    require(lifecycle["latest_implemented_lot"] == 41, "lifecycle latest lot must remain 41")
    require(
        lifecycle["lots"]["41"]["status"]
        == "IMPLEMENTED_VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY",
        "Lot 41 lifecycle status changed",
    )
    require(
        lifecycle["lots"]["42"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 42 lifecycle must remain exactly locked before gate merge",
    )


def validate_schema_contract() -> None:
    schema = load(SCHEMA_PATH)
    require(schema.get("additionalProperties") is False, "gate schema must be closed")
    props = schema["properties"]
    constants = {
        "schema_version": "lot42-v4-entry-gate-v1",
        "target_lot": 42,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.41.0",
        "gate_status": "GO_LOT42_IMPLEMENTATION_ENTRY",
        "next_lot": 43,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in constants.items():
        require(props[field]["const"] == value, f"schema constant changed: {field}")
    require(props["prerequisites"]["additionalProperties"] is False, "prerequisites schema open")
    require(props["safety"]["additionalProperties"] is False, "safety schema open")
    require(props["safety"]["properties"]["trade_allowed"]["const"] is False, "trade schema open")
    require(
        props["safety"]["properties"]["execution_allowed"]["const"] is False,
        "execution schema open",
    )


def validate_gate_payload(gate: dict[str, Any]) -> None:
    body = dict(gate)
    actual = body.pop("output_checksum", None)
    require(actual == EXPECTED_GATE_CHECKSUM, "Lot 42 gate checksum value changed")
    require(canonical_checksum(body) == actual, "Lot 42 gate checksum mismatch")
    require(gate["base_commit"] == EXPECTED_BASE, "Lot 42 gate base changed")
    require(gate["implementation_started"] is False, "Lot 42 implementation already started")
    require(gate["owner"] == "MicrostructureDomain", "Lot 42 owner changed")
    require(gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "runtime changed")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "Lot 42 gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "Lot 42 gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "Lot 42 allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "Lot 42 forbidden scope changed")
    require(gate["prerequisites"] == EXPECTED_PREREQUISITES, "Lot 41 prerequisite evidence changed")
    require(gate["quality_gates"] == EXPECTED_QUALITY, "Lot 42 quality gates changed")
    require(gate["safety"] == EXPECTED_SAFETY, "Lot 42 safety boundary changed")
    require(gate["next_lot"] == 43, "Lot 43 next-lot identity changed")
    require(gate["next_lot_status"] == "PLANNED_LOCKED", "Lot 43 must remain locked")


def validate_preimplementation_boundary() -> None:
    for path in LOT42_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 42 implementation present before gate merge: {path}")
    for path in LOT43_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 43 implementation present before Lot 42: {path}")


def validate_documentation() -> None:
    for path in (DOC_PATH, REPORT_PATH):
        text = path.read_text(encoding="utf-8")
        for value in (EXPECTED_BASE, EXPECTED_GATE_CHECKSUM, "Lot 42", "Lot 43", "PLANNED_LOCKED"):
            require(value in text, f"gate documentation missing {value}: {path.name}")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_previous_release()
    validate_lifecycle()
    validate_schema_contract()
    validate_gate_payload(gate)
    validate_roadmap(gate)
    validate_next_roadmap_lock()
    validate_preimplementation_boundary()
    validate_documentation()
    return {
        "schema_version": "lot42-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": gate["gate_status"],
        "base_commit": gate["base_commit"],
        "current_version": gate["current_version"],
        "output_checksum": gate["output_checksum"],
        "target_lot": 42,
        "next_locked_lot": 43,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot42EntryGateError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT42 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
