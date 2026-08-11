#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_lot42_post_merge import validate as validate_lot42_post_merge  # noqa: E402

GATE_PATH = ROOT / "data/audit/lot43_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot43_v4_entry_gate_v1.schema.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot42.json"
DOC_PATH = ROOT / "docs/LOT_43_V4_ENTRY_GATE.md"
REPORT_PATH = ROOT / "reports/lot_43_v4_entry_gate_report.md"

EXPECTED_BASE = "2438622734e597cdcbada6b926e3c05d9e4cf8bc"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d"
EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
}
EXPECTED_OUTPUTS = {
    "BookResilienceReplenishmentEngineStateV1",
    "BookResilienceReplenishmentEngineAuditV1",
    "BookResilienceStateV1",
}
EXPECTED_ALLOWED = {
    "ADJACENT_PRICE_REPLENISHMENT_CLASSIFICATION",
    "BOOK_RESILIENCE_STATE_V1",
    "DEPLETION_EVENT_DETECTION",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "EXPIRED_REPLENISHMENT_WINDOW_REJECTION",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT43",
    "HORIZON_SPECIFIC_RESILIENCE_MEASUREMENT",
    "MID_SHIFT_REPLENISHMENT_CLASSIFICATION",
    "NO_PARTICIPANT_INTENT_ASSERTION",
    "OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ANALYSIS",
    "REPLENISHMENT_QUANTITY_MEASUREMENT",
    "REPLENISHMENT_TIME_MEASUREMENT",
    "SAME_PRICE_REPLENISHMENT_CLASSIFICATION",
    "SIDE_SPECIFIC_RESILIENCE_MEASUREMENT",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "VOLATILITY_REGIME_CONDITIONING",
}
EXPECTED_FORBIDDEN = {
    "ABSORPTION_HIDDEN_LIQUIDITY_INFERENCE",
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
    "branch_coverage_percent": 93.07,
    "latest_implemented_lot": 42,
    "line_coverage_percent": 98.17,
    "lot42_audit_checksum": "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f",
    "lot42_evidence_head": "3655b18a24cafb3383dfeb2709904af59044535f",
    "lot42_final_pr_head": "85f0a141d52d448a452ff1493050a3bf31a23dce",
    "lot42_gate_merge": "7456c5b80b609ee5958d8b6da0effd489faa308c",
    "lot42_implementation_merge": "3a7226b4beeb23bfeee976243efc0057cac69e0e",
    "lot42_post_merge_audit_merge_commit": "2438622734e597cdcbada6b926e3c05d9e4cf8bc",
    "lot42_post_merge_verdict": "GO_LOT42_POST_MERGE",
    "lot42_source_head": "2d91da1777f1ccbd7f81563dbc74fd3b89eecdf2",
    "lot42_state_checksum": "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0",
    "lot42_status": "IMPLEMENTED_VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY",
    "lot42_zone_set_checksum": "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89",
    "lot43_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 80.1,
    "participant_intent_inferred": False,
    "reference_active_zones_total": 3,
    "reference_book_mid": "50025",
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

LOT43_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py",
    ROOT / "config/microstructure/book_resilience_and_replenishment_engine_v1.json",
    ROOT / "contracts/schemas/book_resilience_and_replenishment_engine_state_v1.schema.json",
    ROOT / "contracts/schemas/book_resilience_and_replenishment_engine_audit_v1.schema.json",
    ROOT / "contracts/schemas/book_resilience_state_v1.schema.json",
    ROOT / "scripts/run_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "scripts/validate_lot43.py",
    ROOT / "scripts/validate_lot43_no_connectivity.py",
    ROOT / "tests/test_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "data/audit/book_resilience_and_replenishment_engine_lot43.json",
    ROOT / "data/audit/book_resilience_and_replenishment_engine_audit_lot43.json",
    ROOT / "data/audit/book_resilience_state_lot43.json",
    ROOT / "reports/lot_43_book_resilience_and_replenishment_engine_report.md",
    ROOT / "docs/LOT_43_BOOK_RESILIENCE_AND_REPLENISHMENT_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_43.md",
)
LOT44_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    ROOT / "config/microstructure/trades_and_aggressor_classification_schema_v1.json",
    ROOT / "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "scripts/validate_lot44.py",
    ROOT / "tests/test_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_44.md",
)


class Lot43EntryGateError(RuntimeError):
    """Raised when the Lot 43 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot43EntryGateError(message)


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
    lot43 = roadmap_record(44)
    expected = {
        "lot_id": "Lot 43",
        "lot_number": 43,
        "title": "Book Resilience & Replenishment Engine",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(lot43.get(field) == value, f"canonical Lot 43 field changed: {field}")
    require(set(lot43.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 43 inputs changed")
    require(set(lot43.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 43 outputs changed")
    require(len(lot43.get("processing_sequence", [])) >= 7, "Lot 43 processing sequence incomplete")
    require(len(lot43.get("acceptance_tests", [])) >= 10, "Lot 43 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 44, "Lot 43 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 43", "Lot 43 roadmap lot binding changed")
    require(binding["title"] == expected["title"], "Lot 43 roadmap title binding changed")


def validate_next_roadmap_lock() -> None:
    lot44 = roadmap_record(45)
    expected = {
        "lot_id": "Lot 44",
        "lot_number": 44,
        "title": "Trades & Aggressor Classification Schema",
        "status": "PLANNED_LOCKED",
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected.items():
        require(lot44.get(field) == value, f"canonical Lot 44 field changed: {field}")


def validate_previous_release() -> None:
    previous = validate_lot42_post_merge()
    require(previous["status"] == "PASS", "Lot 42 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT42_POST_MERGE", "Lot 42 audit verdict changed")
    require(previous["project_version"] == "0.42.0", "Lot 42 audited version changed")
    require(previous["latest_implemented_lot"] == 42, "latest implemented lot must be 42")
    require(previous["next_lot"] == 43, "Lot 42 audit next lot changed")
    require(previous["next_lot_status"] == "PLANNED_LOCKED", "Lot 43 is not locked")


def validate_lifecycle() -> None:
    lifecycle = load(LIFECYCLE_PATH)
    require(lifecycle["latest_implemented_lot"] == 42, "lifecycle latest lot must remain 42")
    require(
        lifecycle["lots"]["42"]["status"]
        == "IMPLEMENTED_VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY",
        "Lot 42 lifecycle status changed",
    )
    require(
        lifecycle["lots"]["43"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 43 lifecycle must remain exactly locked before gate merge",
    )


def validate_schema_contract() -> None:
    schema = load(SCHEMA_PATH)
    require(schema.get("additionalProperties") is False, "gate schema must be closed")
    props = schema["properties"]
    constants = {
        "schema_version": "lot43-v4-entry-gate-v1",
        "target_lot": 43,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.42.0",
        "gate_status": "GO_LOT43_IMPLEMENTATION_ENTRY",
        "next_lot": 44,
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
    require(actual == EXPECTED_GATE_CHECKSUM, "Lot 43 gate checksum value changed")
    require(canonical_checksum(body) == actual, "Lot 43 gate checksum mismatch")
    require(gate["base_commit"] == EXPECTED_BASE, "Lot 43 gate base changed")
    require(gate["implementation_started"] is False, "Lot 43 implementation already started")
    require(gate["owner"] == "MicrostructureDomain", "Lot 43 owner changed")
    require(gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "runtime changed")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "gate allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "gate forbidden scope changed")
    require(gate["prerequisites"] == EXPECTED_PREREQUISITES, "prerequisite evidence changed")
    require(gate["quality_gates"] == EXPECTED_QUALITY, "quality gates changed")
    require(gate["safety"] == EXPECTED_SAFETY, "safety boundary changed")
    require(gate["next_lot"] == 44, "next lot changed")
    require(gate["next_lot_status"] == "PLANNED_LOCKED", "Lot 44 lock changed")


def validate_governance_only() -> None:
    for path in LOT43_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 43 implementation must not exist before gate merge: {path}")
    for path in LOT44_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 44 implementation must remain locked: {path}")


def validate_docs() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")
    required_tokens = (
        EXPECTED_BASE,
        EXPECTED_GATE_CHECKSUM,
        "GO_LOT43_IMPLEMENTATION_ENTRY",
        "Book Resilience & Replenishment Engine",
        "0.42.0",
        "Lot 44",
        "PLANNED_LOCKED",
        "98.17",
        "93.07",
        "80.10",
    )
    for text in (doc, report):
        for token in required_tokens:
            require(token in text, f"gate documentation missing token: {token}")


def validate() -> dict[str, object]:
    validate_previous_release()
    validate_lifecycle()
    gate = load(GATE_PATH)
    validate_gate_payload(gate)
    validate_schema_contract()
    validate_roadmap(gate)
    validate_next_roadmap_lock()
    validate_governance_only()
    validate_docs()
    result: dict[str, object] = {
        "schema_version": "lot43-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": gate["gate_status"],
        "base_commit": gate["base_commit"],
        "current_version": gate["current_version"],
        "output_checksum": gate["output_checksum"],
        "target_lot": 43,
        "next_locked_lot": 44,
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
    except (Lot43EntryGateError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT43 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
