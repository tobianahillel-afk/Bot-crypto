#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from scripts.validate_lot37_post_merge import validate as validate_lot37_post_merge

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot38_v4_entry_gate.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
REGISTRY_PATH = ROOT / "data/audit/microstructure_contract_registry_lot37.json"
MATRIX_PATH = ROOT / "data/audit/microstructure_capability_matrix_lot37.json"
L2_FIXTURE_PATH = ROOT / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"

EXPECTED_BASE = "c7ff8eecafd5f34196e9383013e97548b1a0ba02"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_GATE_CHECKSUM = "29fe4a5fd14b3bce95e3016fce67e10f94edcca1c2aad60c9fda382f3eb9d6a0"
EXPECTED_L2_SHA256 = "f3715a14e8f04395b9ca5b514ac01ff8fcf924b82812f3388fdf500d6ecf5ece"
EXPECTED_REGISTRY_CHECKSUM = "129140ffb7e812afd59d0174d318c5e3388d23bc49cc554168bde558bc0bf590"
EXPECTED_MATRIX_CHECKSUM = "f7132fcfdab898af3f733b2715e0836d23e6284f8c0c1f3e7dd92ccf0070f1b4"

EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
    "OrderBookSnapshotRawV1",
}
EXPECTED_OUTPUTS = {
    "OrderBookL2SnapshotEngineStateV1",
    "OrderBookL2SnapshotEngineAuditV1",
    "OrderBookSnapshotV1",
    "BookHealthStateV1",
}
EXPECTED_ALLOWED = {
    "ORDER_BOOK_SNAPSHOT_RAW_V1_CONTRACT_DEFINITION",
    "OFFLINE_L2_SNAPSHOT_NORMALIZATION",
    "CANONICAL_BID_ASK_ORDERING",
    "IDENTICAL_PRICE_LEVEL_AGGREGATION",
    "NEGATIVE_QUANTITY_REJECTION",
    "CROSSED_LOCKED_BOOK_VALIDATION",
    "CONFIGURED_DEPTH_CAP",
    "SOURCE_DEPTH_PRESERVATION",
    "SNAPSHOT_CHECKSUM",
    "SEQUENCE_ANCHOR_BINDING",
    "BOOK_HEALTH_STATE",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "NEGATIVE_AND_FORBIDDEN_CAPABILITY_VALIDATION",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT38",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "NETWORK_INGESTION",
    "ORDER_BOOK_DELTA_SEQUENCE_RECONSTRUCTION",
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
    "branch_coverage_percent": 100.0,
    "latest_implemented_lot": 37,
    "line_coverage_percent": 100.0,
    "lot37_audit_checksum": (
        "aa2df489e636860c119eb2ed54f7a5f03ede09838dfbd056dae0bb5a8a2a482f"
    ),
    "lot37_capability_matrix_checksum": EXPECTED_MATRIX_CHECKSUM,
    "lot37_config_checksum": (
        "a6e79dae8567aeafd5b25e3793a901097dd1714e9ec6c5f19a771417e78d6a78"
    ),
    "lot37_contract_registry_checksum": EXPECTED_REGISTRY_CHECKSUM,
    "lot37_evidence_head": "91c28f17acc2f66c906dddee96cbda369945f3ea",
    "lot37_implementation_merge": "f1da136ff956e40915fab42ae21748a6f2b1ebca",
    "lot37_post_merge_audit_merge_commit": EXPECTED_BASE,
    "lot37_source_head": "59b189e9980772245993a9212b6c8ad5e9a88a00",
    "lot37_state_checksum": (
        "ea960217eb9a2159c4a99c56257a37c43869ffad0da86555fef24eb356e5f8e7"
    ),
    "lot37_status": "IMPLEMENTED_VALIDATED_OFFLINE_SCOPE_CONTRACTS_ONLY",
    "lot38_capability_status": "PLANNED_LOCKED",
    "mutation_score_percent": 80.26,
    "offline_input_availability_status": "AVAILABLE_FIXTURE_ONLY_NON_CANONICAL",
    "offline_l2_contract_name": "MicrostructureOfflineL2InputV1",
    "offline_l2_contract_schema": (
        "contracts/schemas/microstructure_offline_l2_input_v1.schema.json"
    ),
    "offline_l2_fixture_path": (
        "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"
    ),
    "offline_l2_fixture_sha256": EXPECTED_L2_SHA256,
}


class Lot38EntryGateError(RuntimeError):
    """Raised when the Lot 38 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot38EntryGateError(message)


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


def positive_decimal(value: object, field: str) -> Decimal:
    require(isinstance(value, str), f"{field} must be decimal text")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise Lot38EntryGateError(f"{field} invalid decimal") from exc
    require(number > 0, f"{field} must be positive")
    return number


def validate_gate_checksum(gate: dict[str, Any]) -> None:
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    require(checksum == EXPECTED_GATE_CHECKSUM, "Lot 38 gate checksum value changed")
    require(canonical_checksum(body) == checksum, "Lot 38 gate checksum mismatch")


def canonical_roadmap_record() -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= 39, "canonical roadmap Lot 38 line missing")
    record = json.loads(lines[38])
    require(isinstance(record, dict), "canonical Lot 38 roadmap record must be object")
    return record


def validate_roadmap(gate: dict[str, Any]) -> None:
    record = canonical_roadmap_record()
    expected = {
        "lot_id": "Lot 38",
        "lot_number": 38,
        "title": "Order Book L2 Snapshot Engine",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(record.get(field) == value, f"canonical Lot 38 field changed: {field}")
    require(set(record.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot 38 inputs changed")
    require(set(record.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot 38 outputs changed")
    require(len(record.get("processing_sequence", [])) >= 8, "Lot 38 sequence incomplete")
    require(len(record.get("acceptance_tests", [])) >= 10, "Lot 38 acceptance tests incomplete")
    binding = gate["canonical_roadmap"]
    require(binding["source_line"] == 39, "Lot 38 roadmap line binding changed")
    require(binding["source_blob_sha"] == EXPECTED_ROADMAP_BLOB, "roadmap blob binding changed")
    require(binding["lot_id"] == "Lot 38", "Lot 38 roadmap lot binding changed")


def validate_previous_release() -> dict[str, Any]:
    previous = validate_lot37_post_merge()
    require(previous["status"] == "PASS", "Lot 37 post-merge audit is not PASS")
    require(previous["verdict"] == "GO_LOT37_POST_MERGE", "Lot 37 audit verdict changed")
    require(previous["project_version"] == "0.37.0", "Lot 37 audited version changed")
    require(previous["latest_implemented_lot"] == 37, "latest implemented lot must be 37")
    require(previous["next_lot"] == 38, "Lot 37 audit next lot changed")
    require(previous["next_lot_status"] == "PLANNED_LOCKED", "Lot 38 is not locked")
    return previous


def validate_prerequisites(gate: dict[str, Any]) -> None:
    require(
        gate["prerequisites"] == EXPECTED_PREREQUISITES,
        "Lot 38 prerequisite evidence changed",
    )


def validate_lot37_registry_and_matrix() -> None:
    registry = load(REGISTRY_PATH)
    matrix = load(MATRIX_PATH)
    require(canonical_checksum(registry) == EXPECTED_REGISTRY_CHECKSUM, "registry changed")
    require(canonical_checksum(matrix) == EXPECTED_MATRIX_CHECKSUM, "capability matrix changed")
    l2 = next(
        item for item in registry["entries"]
        if item["contract_name"] == "MicrostructureOfflineL2InputV1"
    )
    require(l2["status"] == "ACTIVE_LOT37_CONTRACT", "offline L2 contract inactive")
    require(l2["contract_kind"] == "INPUT", "offline L2 contract kind changed")
    lot38 = next(
        item for item in matrix["entries"]
        if item["capability_id"] == "LOT38_ORDER_BOOK_L2_SNAPSHOT_ENGINE"
    )
    require(lot38["classification"] == "DISABLED", "Lot 38 was enabled before gate")
    require(lot38["implementation_status"] == "PLANNED_LOCKED", "Lot 38 status changed")
    lot39 = next(
        item for item in matrix["entries"]
        if item["capability_id"] == "LOT39_ORDER_BOOK_DELTA_SEQUENCE_RECONSTRUCTOR"
    )
    require(lot39["implementation_status"] == "PLANNED_LOCKED", "Lot 39 was unlocked")


def validate_offline_l2_fixture() -> None:
    require(
        file_sha256(L2_FIXTURE_PATH) == EXPECTED_L2_SHA256,
        "offline L2 fixture bytes changed",
    )
    fixture = load(L2_FIXTURE_PATH)
    require(fixture["fixture_only"] is True, "offline L2 input must remain fixture-only")
    require(fixture["canonical_contract"] is False, "fixture cannot become canonical contract")
    require(fixture["used_for_decision"] is False, "fixture cannot become decision data")
    bids = fixture["bids"]
    asks = fixture["asks"]
    require(isinstance(bids, list) and bids, "offline L2 bids missing")
    require(isinstance(asks, list) and asks, "offline L2 asks missing")
    bid_prices = [positive_decimal(level["price"], "bid price") for level in bids]
    ask_prices = [positive_decimal(level["price"], "ask price") for level in asks]
    for level in (*bids, *asks):
        positive_decimal(level["quantity"], "book quantity")
    require(max(bid_prices) < min(ask_prices), "offline L2 fixture is crossed or locked")


def validate_scope(gate: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version": "lot38-v4-entry-gate-v1",
        "target_lot": 38,
        "base_commit": EXPECTED_BASE,
        "current_version": "0.37.0",
        "gate_status": "GO_LOT38_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT38",
        "implementation_started": False,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "next_lot": 39,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected_fields.items():
        require(gate[field] == value, f"Lot 38 gate field changed: {field}")
    require(set(gate["required_inputs"]) == EXPECTED_INPUTS, "Lot 38 gate inputs changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "Lot 38 gate outputs changed")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "Lot 38 allowed scope changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "Lot 38 forbidden scope changed")
    require(
        gate["quality_gates"]
        == {
            "line_coverage_min_percent": 95,
            "branch_coverage_min_percent": 90,
            "mutation_score_min_percent": 80,
            "anti_flake_repetitions": 3,
        },
        "Lot 38 quality gates changed",
    )


def validate_safety(gate: dict[str, Any]) -> None:
    safety = gate["safety"]
    require(safety["analysis_only"] is True, "analysis-only boundary changed")
    require(safety["approved_size"] == 0, "approved size changed")
    require(
        safety["participant_behavior_inference_explicitly_labeled"] is True,
        "participant-inference labeling changed",
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
        require(safety[field] is False, f"Lot 38 permission enabled: {field}")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_gate_checksum(gate)
    validate_roadmap(gate)
    previous = validate_previous_release()
    validate_prerequisites(gate)
    validate_lot37_registry_and_matrix()
    validate_offline_l2_fixture()
    validate_scope(gate)
    validate_safety(gate)
    return {
        "schema_version": "lot38-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT38_IMPLEMENTATION_ENTRY",
        "base_commit": EXPECTED_BASE,
        "canonical_title": "Order Book L2 Snapshot Engine",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "output_checksum": EXPECTED_GATE_CHECKSUM,
        "previous_verdict": previous["verdict"],
        "offline_l2_available": True,
        "next_locked_lot": 39,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot38EntryGateError,
        OSError,
        KeyError,
        StopIteration,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT38 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
