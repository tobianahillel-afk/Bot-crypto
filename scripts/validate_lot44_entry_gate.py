#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_lot43_post_merge import validate as validate_lot43_post_merge  # noqa: E402

GATE_PATH = ROOT / "data/audit/lot44_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot44_v4_entry_gate_v1.schema.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot43.json"
DOC_PATH = ROOT / "docs/LOT_44_V4_ENTRY_GATE.md"
REPORT_PATH = ROOT / "reports/lot_44_v4_entry_gate_report.md"

EXPECTED_BASE = "7a207a16e7aa543f9f7c241828f8ea5ae9ed0407"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "100d21ea18cfd7d9fe275ac0bea162c76a0bb7e5f85e319b543b4053e3c4d5ef"
EXPECTED_POST_MERGE_CHECKSUM = "167c69b324377ceefd322d59fab7f42d9f7998efde94503d6d86ca4a51ed9c14"
EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
}
EXPECTED_OUTPUTS = {
    "TradesAggressorClassificationSchemaStateV1",
    "TradesAggressorClassificationSchemaAuditV1",
    "ClassifiedTradeV1",
    "AggressorConfidenceStateV1",
}
EXPECTED_ALLOWED = {
    "OFFLINE_TRADES_AGGRESSOR_CLASSIFICATION_SCHEMA",
    "TIMESTAMPED_TRADES_INPUT_CONTRACT",
    "QUOTE_TEST_PRIMARY_CLASSIFICATION",
    "TICK_RULE_POLICY_FALLBACK_WHEN_QUOTE_UNAVAILABLE",
    "BUY_AGGRESSOR_CLASSIFICATION",
    "SELL_AGGRESSOR_CLASSIFICATION",
    "UNKNOWN_AGGRESSOR_CLASSIFICATION",
    "CLASSIFICATION_METHOD_ATTRIBUTION",
    "VERSIONED_CLASSIFICATION_CONFIDENCE_FIELD",
    "UNKNOWN_VOLUME_RATIO_MEASUREMENT",
    "BUY_SELL_UNKNOWN_VOLUME_CONSERVATION",
    "STALE_QUOTE_TO_REDUCED_CONFIDENCE_OR_UNKNOWN",
    "LOCKED_QUOTE_TO_REDUCED_CONFIDENCE_OR_UNKNOWN",
    "EVENT_TIME_ORDERING_AND_NO_FUTURE_LEAKAGE",
    "CLASSIFIED_TRADE_V1",
    "AGGRESSOR_CONFIDENCE_STATE_V1",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT44",
    "NO_PARTICIPANT_INTENT_ASSERTION",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "NETWORK_INGESTION",
    "ORDER_FLOW_DELTA_CVD_ENGINE",
    "ORDER_FLOW_AGGREGATION",
    "CVD_COMPUTATION",
    "TRADE_CLASSIFICATION_CONFIDENCE_ENGINE",
    "ABSORPTION_HIDDEN_LIQUIDITY_INFERENCE",
    "VOLUME_CLUSTER_TIME_AT_LEVEL_ENGINE",
    "STOP_ZONE_LIQUIDITY_POOL_INFERENCE",
    "SWEEP_FAKEOUT_TRAP_FAILED_AUCTION_ENGINE",
    "DERIVATIVES_CONTEXT_ENGINE",
    "GAME_THEORY_SCENARIO_AGGREGATION",
    "CANCELLATION_INTENT_INFERENCE",
    "PARTICIPANT_INTENT_AS_FACT",
    "SCENARIO_TO_SIGNAL_CONVERSION",
    "FORECAST_GENERATION",
    "SIGNAL_GENERATION",
    "RISK_APPROVAL",
    "ORDER_ROUTING",
    "TRADING",
    "EXECUTION",
    "FUTURE_QUOTE_BACKFILL",
    "UNKNOWN_VOLUME_SUPPRESSION",
}
EXPECTED_PREREQUISITES: dict[str, object] = {
    "anti_flake_repetitions": 3,
    "branch_coverage_percent": 96.88,
    "latest_implemented_lot": 43,
    "line_coverage_percent": 98.07,
    "lot43_audit_checksum": "3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67",
    "lot43_resilience_checksum": "598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb",
    "lot43_state_checksum": "30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6",
    "lot43_evidence_head": "76c0670d7933f29965306993ff217647def0f0d4",
    "lot43_final_pr_head": "69667b5c46ac2ecf7b2a64656f84c374ee929dbf",
    "lot43_gate_merge": "ed8845e0e56151348fe57c0e9bceaf4646ea49aa",
    "lot43_implementation_merge": "0b524b1478272e0a69a06b50c68b1b2c3b092964",
    "lot43_post_merge_audit_merge_commit": "7a207a16e7aa543f9f7c241828f8ea5ae9ed0407",
    "lot43_post_merge_audit_checksum": EXPECTED_POST_MERGE_CHECKSUM,
    "lot43_post_merge_verdict": "GO_LOT43_POST_MERGE",
    "lot43_source_head": "d45f40aec90b26dd1278ec2f49b405fa5b2ed94e",
    "lot43_status": "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY",
    "lot44_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 82.13,
    "participant_intent_inferred": False,
    "reference_depletion_events_total": 1,
    "reference_history_sequence_ids": [1001, 1002, 1003],
    "reference_resilience_horizons_us": [10000, 25000],
    "reference_volatility_regime": "QUIET",
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

LOT44_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
    ROOT / "config/microstructure/trades_and_aggressor_classification_schema_v1.json",
    ROOT / "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "scripts/validate_lot44.py",
    ROOT / "tests/test_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json",
    ROOT / "reports/lot_44_trades_and_aggressor_classification_schema_report.md",
    ROOT / "docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_44.md",
)
LOT45_FORBIDDEN_IMPLEMENTATION_PATHS = (
    ROOT / "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
    ROOT / "config/microstructure/order_flow_delta_and_cvd_engine_v1.json",
    ROOT / "scripts/run_lot45_order_flow_delta_and_cvd_engine.py",
    ROOT / "scripts/validate_lot45.py",
    ROOT / "tests/test_lot45_order_flow_delta_and_cvd_engine.py",
    ROOT / "data/audit/order_flow_delta_and_cvd_engine_lot45.json",
    ROOT / "reports/lot_45_order_flow_delta_and_cvd_engine_report.md",
    ROOT / "docs/LOT_45_ORDER_FLOW_DELTA_AND_CVD_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_45.md",
)


class Lot44EntryGateError(RuntimeError):
    """Raised when the Lot 44 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot44EntryGateError(message)


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
    lot44 = roadmap_record(45)
    expected = {
        "lot_id": "Lot 44",
        "lot_number": 44,
        "title": "Trades & Aggressor Classification Schema",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(lot44.get(field) == value, f"canonical Lot 44 field changed: {field}")
    require(set(lot44.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 44 inputs changed")
    require(set(lot44.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 44 outputs changed")
    require(len(lot44.get("processing_sequence", [])) >= 7, "Lot 44 processing sequence incomplete")
    require(len(lot44.get("acceptance_tests", [])) >= 12, "Lot 44 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 45, "Lot 44 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 44", "Lot 44 roadmap lot binding changed")
    require(binding["title"] == expected["title"], "Lot 44 roadmap title binding changed")


def validate_next_roadmap_lock() -> None:
    lot45 = roadmap_record(46)
    expected45 = {
        "lot_id": "Lot 45",
        "lot_number": 45,
        "title": "Order Flow, Delta & CVD Engine",
        "status": "PLANNED_LOCKED",
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected45.items():
        require(lot45.get(field) == value, f"canonical Lot 45 field changed: {field}")

    lot46 = roadmap_record(47)
    expected46 = {
        "lot_id": "Lot 46",
        "lot_number": 46,
        "title": "Trade Classification Confidence Engine",
        "status": "PLANNED_LOCKED",
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected46.items():
        require(lot46.get(field) == value, f"canonical Lot 46 field changed: {field}")
    implementation_files = lot46.get("implementation_files")
    require(isinstance(implementation_files, list), "Lot 46 implementation file list missing")
    require(len(implementation_files) == 9, "Lot 46 implementation file list changed")
    require(all(isinstance(path, str) and path for path in implementation_files), "Lot 46 implementation file list invalid")


def validate_previous_release() -> None:
    previous = validate_lot43_post_merge()
    require(previous["status"] == "PASS", "Lot 43 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT43_POST_MERGE", "Lot 43 audit verdict changed")
    require(previous["release"] == "0.43.0", "Lot 43 audited release changed")
    require(previous["post_merge_audit_checksum"] == EXPECTED_POST_MERGE_CHECKSUM, "Lot 43 audit checksum changed")
    require(previous["lot44_status"] == "PLANNED_LOCKED", "Lot 44 prerequisite is not locked")
    require(previous["lot44_implementation_started"] is False, "Lot 44 already started")
    require(previous["trade_allowed"] is False, "Lot 43 audit enabled trading")
    require(previous["execution_allowed"] is False, "Lot 43 audit enabled execution")
    require(previous["approved_size"] == 0, "Lot 43 audit approved size changed")


def validate_lifecycle() -> None:
    lifecycle = load(LIFECYCLE_PATH)
    require(lifecycle["latest_implemented_lot"] == 43, "lifecycle latest lot must be 43")
    lot43 = lifecycle["lots"]["43"]
    require(lot43["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY", "Lot 43 lifecycle status changed")
    require(lot43["merged_commit"] == "0b524b1478272e0a69a06b50c68b1b2c3b092964", "Lot 43 merge changed")
    expected_lot44 = {"implementation_started": False, "status": "PLANNED_LOCKED"}
    require(lifecycle["lots"]["44"] == expected_lot44, "Lot 44 lifecycle must be locked before gate merge")


def validate_schema_contract() -> None:
    schema = load(SCHEMA_PATH)
    require(schema.get("additionalProperties") is False, "gate schema must be closed")
    props = schema["properties"]
    constants = {
        "schema_version": "lot44-v4-entry-gate-v1",
        "target_lot": 44,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.43.0",
        "gate_status": "GO_LOT44_IMPLEMENTATION_ENTRY",
        "next_lot": 45,
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
    require(actual == EXPECTED_GATE_CHECKSUM, "Lot 44 gate checksum value changed")
    require(canonical_checksum(body) == actual, "Lot 44 gate checksum mismatch")
    require(gate["base_commit"] == EXPECTED_BASE, "Lot 44 gate base changed")
    require(gate["implementation_started"] is False, "Lot 44 implementation already started")
    require(gate["owner"] == "MicrostructureDomain", "Lot 44 owner changed")
    require(gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "runtime changed")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "gate allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "gate forbidden scope changed")
    require(gate["prerequisites"] == EXPECTED_PREREQUISITES, "prerequisite evidence changed")
    require(gate["quality_gates"] == EXPECTED_QUALITY, "quality gates changed")
    require(gate["safety"] == EXPECTED_SAFETY, "safety boundary changed")
    require(gate["next_lot"] == 45, "next lot changed")
    require(gate["next_lot_status"] == "PLANNED_LOCKED", "Lot 45 lock changed")


def validate_governance_only() -> None:
    for path in LOT44_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 44 implementation must not exist before gate merge: {path}")
    for path in LOT45_FORBIDDEN_IMPLEMENTATION_PATHS:
        require(not path.exists(), f"Lot 45 implementation must remain locked: {path}")
    lot46_files = roadmap_record(47).get("implementation_files")
    require(isinstance(lot46_files, list), "Lot 46 implementation file list missing")
    for relative in lot46_files:
        require(isinstance(relative, str) and relative, "Lot 46 implementation file path invalid")
        path = ROOT / relative
        require(not path.exists(), f"Lot 46 implementation must remain locked: {path}")


def validate_docs() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")
    required_tokens = (
        EXPECTED_BASE,
        EXPECTED_GATE_CHECKSUM,
        "GO_LOT44_IMPLEMENTATION_ENTRY",
        "Trades & Aggressor Classification Schema",
        "0.43.0",
        "GO_LOT43_POST_MERGE",
        "Lot 45",
        "Lot 46",
        "PLANNED_LOCKED",
        "98.07",
        "96.88",
        "82.13",
    )
    for text in (doc, report):
        for token in required_tokens:
            require(token in text, f"gate documentation missing token: {token}")


def validate() -> dict[str, object]:
    validate_previous_release()
    validate_lifecycle()
    gate_payload = load(GATE_PATH)
    validate_gate_payload(gate_payload)
    validate_schema_contract()
    validate_roadmap(gate_payload)
    validate_next_roadmap_lock()
    validate_governance_only()
    validate_docs()
    result: dict[str, object] = {
        "schema_version": "lot44-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": gate_payload["gate_status"],
        "base_commit": gate_payload["base_commit"],
        "current_version": gate_payload["current_version"],
        "output_checksum": gate_payload["output_checksum"],
        "target_lot": 44,
        "next_locked_lot": 45,
        "future_locked_lot": 46,
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
    except (Lot44EntryGateError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT44 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
