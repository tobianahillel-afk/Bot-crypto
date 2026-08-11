#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_lot40_post_merge import validate as validate_lot40_post_merge  # noqa: E402

GATE_PATH = ROOT / "data/audit/lot41_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot41_v4_entry_gate_v1.schema.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot40.json"
DOC_PATH = ROOT / "docs/LOT_41_V4_ENTRY_GATE.md"
REPORT_PATH = ROOT / "reports/lot_41_v4_entry_gate_report.md"

EXPECTED_BASE = "20975b505c7f8b527751fb5d3bce034c6e55dcc2"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe"
EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
}
EXPECTED_OUTPUTS = {
    "SpreadDepthImbalanceEngineStateV1",
    "SpreadDepthImbalanceEngineAuditV1",
    "BookFeatureStateV1",
}
EXPECTED_ALLOWED = {
    "OFFLINE_SPREAD_DEPTH_IMBALANCE_ANALYSIS",
    "ABSOLUTE_SPREAD_CALCULATION",
    "SPREAD_BPS_CALCULATION",
    "MID_PRICE_CALCULATION",
    "MICROPRICE_CALCULATION",
    "DEPTH_BY_VERSIONED_BPS_BAND",
    "CUMULATIVE_DEPTH_CALCULATION",
    "SYMMETRIC_IMBALANCE_WITH_ZERO_DENOMINATOR_HANDLING",
    "FEATURE_PUBLICATION_BY_HORIZON_AND_LEVEL",
    "BOOK_QUALITY_BINDING",
    "NO_EXTRAPOLATION_BEYOND_OBSERVED_DEPTH",
    "BOOK_FEATURE_STATE_V1",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "NEGATIVE_AND_FORBIDDEN_CAPABILITY_VALIDATION",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT41",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "NETWORK_INGESTION",
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
EXPECTED_PREREQUISITES: dict[str, object] = {
    "anti_flake_repetitions": 3,
    "branch_coverage_percent": 91.24,
    "latest_implemented_lot": 40,
    "line_coverage_percent": 97.31,
    "lot40_audit_checksum": "978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c",
    "lot40_book_health_score": "100",
    "lot40_book_health_veto_checksum": "000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc",
    "lot40_book_integrity_checksum": "35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a",
    "lot40_evidence_head": "ea04fe826261eeed5a59eea60265b38b68404b6b",
    "lot40_final_pr_head": "1268772c07cbb76c18b3267aef12dad5ba58af31",
    "lot40_health_consequence": "NONE",
    "lot40_health_status": "HEALTHY",
    "lot40_implementation_merge": "88f0dac660e262a1c468d9cd75c5e7996ce4817b",
    "lot40_post_merge_audit_merge_commit": EXPECTED_BASE,
    "lot40_post_merge_verdict": "GO_LOT40_POST_MERGE",
    "lot40_source_head": "b9a18a8aaef858b985c3f75ef2aa8955ec521e9f",
    "lot40_state_checksum": "e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477",
    "lot40_status": "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY",
    "lot41_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 82.32,
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

LOT41_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_models.py",
    ROOT / "config/microstructure/spread_depth_and_imbalance_engine_v1.json",
    ROOT / "contracts/schemas/spread_depth_imbalance_engine_state_v1.schema.json",
    ROOT / "contracts/schemas/spread_depth_imbalance_engine_audit_v1.schema.json",
    ROOT / "contracts/schemas/book_feature_state_v1.schema.json",
    ROOT / "scripts/run_lot41_spread_depth_and_imbalance_engine.py",
    ROOT / "scripts/validate_lot41.py",
    ROOT / "tests/test_lot41_spread_depth_and_imbalance_engine.py",
    ROOT / "data/audit/spread_depth_and_imbalance_engine_lot41.json",
    ROOT / "reports/lot_41_spread_depth_and_imbalance_engine_report.md",
    ROOT / "docs/LOT_41_SPREAD_DEPTH_AND_IMBALANCE_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_41.md",
)
LOT42_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py",
    ROOT / "scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py",
    ROOT / "scripts/validate_lot42.py",
    ROOT / "docs/LOT_42_LIQUIDITY_ZONES_WALLS_AND_VOIDS_ENGINE.md",
)


class Lot41EntryGateError(RuntimeError):
    """Raised when the Lot 41 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot41EntryGateError(message)


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
    lot41 = roadmap_record(42)
    expected = {
        "lot_id": "Lot 41",
        "lot_number": 41,
        "title": "Spread, Depth & Imbalance Engine",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(lot41.get(field) == value, f"canonical Lot 41 field changed: {field}")
    require(set(lot41.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 41 inputs changed")
    require(set(lot41.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 41 outputs changed")
    require(len(lot41.get("processing_sequence", [])) >= 8, "Lot 41 processing sequence incomplete")
    require(len(lot41.get("acceptance_tests", [])) >= 10, "Lot 41 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 42, "Lot 41 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 41", "Lot 41 roadmap lot binding changed")
    require(binding["title"] == expected["title"], "Lot 41 roadmap title binding changed")


def validate_next_roadmap_lock() -> None:
    lot42 = roadmap_record(43)
    expected = {
        "lot_id": "Lot 42",
        "lot_number": 42,
        "title": "Liquidity Zones, Walls & Voids Engine",
        "status": "PLANNED_LOCKED",
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected.items():
        require(lot42.get(field) == value, f"canonical Lot 42 field changed: {field}")


def validate_previous_release() -> None:
    previous = validate_lot40_post_merge()
    require(previous["status"] == "PASS", "Lot 40 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT40_POST_MERGE", "Lot 40 audit verdict changed")
    require(previous["project_version"] == "0.40.0", "Lot 40 audited version changed")
    require(previous["latest_implemented_lot"] == 40, "latest implemented lot must be 40")
    require(previous["next_lot"] == 41, "Lot 40 audit next lot changed")
    require(previous["next_lot_status"] == "PLANNED_LOCKED", "Lot 41 is not locked")


def validate_lifecycle() -> None:
    lifecycle = load(LIFECYCLE_PATH)
    require(lifecycle["latest_implemented_lot"] == 40, "lifecycle latest lot must remain 40")
    require(
        lifecycle["lots"]["40"]["status"]
        == "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY",
        "Lot 40 lifecycle status changed",
    )
    require(
        lifecycle["lots"]["41"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 41 lifecycle must remain exactly locked before gate merge",
    )


def validate_schema_contract() -> None:
    schema = load(SCHEMA_PATH)
    require(schema.get("additionalProperties") is False, "gate schema must be closed")
    props = schema["properties"]
    constants = {
        "schema_version": "lot41-v4-entry-gate-v1",
        "target_lot": 41,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.40.0",
        "gate_status": "GO_LOT41_IMPLEMENTATION_ENTRY",
        "next_lot": 42,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in constants.items():
        require(props[field]["const"] == value, f"schema constant changed: {field}")
    require(props["prerequisites"]["additionalProperties"] is False, "prerequisites schema open")
    require(props["safety"]["additionalProperties"] is False, "safety schema open")
    require(props["safety"]["properties"]["trade_allowed"]["const"] is False, "trade schema open")
    require(props["safety"]["properties"]["execution_allowed"]["const"] is False, "execution schema open")


def validate_gate_payload(gate: dict[str, Any]) -> None:
    body = dict(gate)
    actual = body.pop("output_checksum", None)
    require(actual == EXPECTED_GATE_CHECKSUM, "Lot 41 gate checksum value changed")
    require(canonical_checksum(body) == actual, "Lot 41 gate checksum mismatch")
    require(gate["base_commit"] == EXPECTED_BASE, "Lot 41 gate base changed")
    require(gate["implementation_started"] is False, "Lot 41 implementation already started")
    require(gate["owner"] == "MicrostructureDomain", "Lot 41 owner changed")
    require(gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "runtime changed")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "Lot 41 gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "Lot 41 gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "Lot 41 allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "Lot 41 forbidden scope changed")
    require(gate["prerequisites"] == EXPECTED_PREREQUISITES, "Lot 40 prerequisite evidence changed")
    require(gate["quality_gates"] == EXPECTED_QUALITY, "Lot 41 quality gates changed")
    require(gate["safety"] == EXPECTED_SAFETY, "Lot 41 safety boundary changed")
    require(gate["next_lot"] == 42, "Lot 42 next-lot identity changed")
    require(gate["next_lot_status"] == "PLANNED_LOCKED", "Lot 42 must remain locked")


def validate_preimplementation_boundary() -> None:
    for path in LOT41_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 41 implementation present before gate merge: {path}")
    for path in LOT42_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 42 implementation present before Lot 41: {path}")


def validate_documentation() -> None:
    for path in (DOC_PATH, REPORT_PATH):
        text = path.read_text(encoding="utf-8")
        for value in (EXPECTED_BASE, EXPECTED_GATE_CHECKSUM, "Lot 41", "Lot 42", "PLANNED_LOCKED"):
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
        "schema_version": "lot41-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": gate["gate_status"],
        "base_commit": gate["base_commit"],
        "current_version": gate["current_version"],
        "output_checksum": gate["output_checksum"],
        "target_lot": 41,
        "next_locked_lot": 42,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot41EntryGateError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT41 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
