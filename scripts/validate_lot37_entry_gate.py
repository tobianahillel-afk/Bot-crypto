#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot37_v4_entry_gate.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
OVERLAY_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot36.json"
STATE_PATH = ROOT / "data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json"
AUDIT_PATH = ROOT / "data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json"
MANIFEST_PATH = ROOT / "data/audit/closure_manifest_lot36.json"
REPLAY_PATH = ROOT / "data/audit/replay_evidence_lot36.json"
COVERAGE_PATH = ROOT / "reports/lot36/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot36/mutation_summary.json"

EXPECTED_BASE_COMMIT = "33fba0abf7463fc54a36282476ee51655ff09919"
EXPECTED_LOT36_IMPLEMENTATION = "c21b8f242270bd87eebbf7279635ab8bb51b8666"
EXPECTED_LOT36_EVIDENCE = "b3680f5da0a3fd98fdedc31599c829dc60808290"
EXPECTED_LOT36_EXACT_CI = "16f3454c6f912f3f00f79836950047b15687abce"
EXPECTED_LOT36_MERGE = "87da195283797247505e4fc650214e33e759e21a"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_STATE_CHECKSUM = "635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592"
EXPECTED_AUDIT_CHECKSUM = "ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42"
EXPECTED_MANIFEST_CHECKSUM = "6a9935e728a93a23a3804106dc54aa216f4f9fedad3635b5507139f4ccbfc37f"
EXPECTED_REPLAY_CHECKSUM = "cef50b5191c1f3c78baaa3906c4c5ded59f1dd45dad0271a0071b7056b6af91d"
EXPECTED_GATE_CHECKSUM = "37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d"
EXPECTED_L2_SHA256 = "f3715a14e8f04395b9ca5b514ac01ff8fcf924b82812f3388fdf500d6ecf5ece"
EXPECTED_TRADE_SHA256 = "b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8"

EXPECTED_OUTPUTS = {
    "MicrostructureScopeOfflineDataContractsStateV1",
    "MicrostructureScopeOfflineDataContractsAuditV1",
    "MicrostructureScopeOfflineDataContractsContractRegistryV1",
    "MicrostructureScopeOfflineDataContractsCapabilityMatrixV1",
}
EXPECTED_ALLOWED = {
    "V4_SCOPE_AND_DOMAIN_BOUNDARY_DEFINITION",
    "OFFLINE_MICROSTRUCTURE_DATA_CONTRACT_REGISTRY",
    "CAPABILITY_MATRIX_CLASSIFICATION",
    "PUBLIC_API_AND_DEPENDENCY_BOUNDARY_DEFINITION",
    "VERSIONED_CONFIG_AND_LINEAGE_BINDING",
    "INPUT_DATA_AVAILABILITY_PREREQUISITE_VALIDATION",
    "DETERMINISTIC_STATE_AUDIT_PERSISTENCE",
    "NEGATIVE_AND_FORBIDDEN_CAPABILITY_VALIDATION",
    "FULL_CHAIN_VALIDATION_UNTIL_LOT37",
}
EXPECTED_FORBIDDEN = {
    "EXTERNAL_NETWORK_ACCESS",
    "LIVE_EXCHANGE_DATA",
    "REAL_CREDENTIALS",
    "NETWORK_INGESTION",
    "CANONICAL_L2_SNAPSHOT_ENGINE_IMPLEMENTATION",
    "ORDER_BOOK_DELTA_SEQUENCE_RECONSTRUCTION",
    "BOOK_INTEGRITY_DESYNC_ENGINE",
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
EXPECTED_QUALITY = {
    "line_coverage_min_percent": 95,
    "branch_coverage_min_percent": 90,
    "mutation_score_min_percent": 80,
    "anti_flake_repetitions": 3,
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


class Lot37EntryGateError(RuntimeError):
    """Raised when the Lot 37 V4 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot37EntryGateError(message)


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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_payload_checksum(
    payload: dict[str, Any], field: str, expected: str, label: str
) -> None:
    body = dict(payload)
    checksum = body.pop(field, None)
    require(checksum == expected, f"{label} checksum value changed")
    require(canonical_checksum(body) == checksum, f"{label} checksum mismatch")


def parse_utc(value: object, field: str) -> datetime:
    require(isinstance(value, str) and value.endswith("Z"), f"{field} must be UTC Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    require(parsed.utcoffset() is not None, f"{field} must be timezone-aware")
    return parsed


def decimal_positive(value: object, field: str) -> Decimal:
    require(isinstance(value, str), f"{field} must be decimal text")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise Lot37EntryGateError(f"{field} invalid decimal") from exc
    require(result > 0, f"{field} must be positive")
    return result


def canonical_roadmap_record() -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= 38, "canonical roadmap Lot 37 line missing")
    record = json.loads(lines[37])
    require(isinstance(record, dict), "canonical Lot 37 roadmap record must be object")
    return record


def validate_roadmap(gate: dict[str, Any]) -> None:
    record = canonical_roadmap_record()
    expected_identity = {
        "lot_id": "Lot 37",
        "lot_number": 37,
        "title": "Microstructure Scope & Offline Data Contracts",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, expected in expected_identity.items():
        require(record.get(field) == expected, f"canonical Lot 37 field changed: {field}")
    require(set(record.get("output_contracts", [])) == EXPECTED_OUTPUTS, "canonical Lot 37 outputs changed")
    require(
        gate["canonical_roadmap"]
        == {
            "source_path": "data/audit/product_scope_roadmap_lot21.jsonl",
            "source_line": 38,
            "source_blob_sha": EXPECTED_ROADMAP_BLOB,
            "lot_id": "Lot 37",
            "title": "Microstructure Scope & Offline Data Contracts",
            "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        },
        "Lot 37 canonical roadmap binding changed",
    )


def validate_v3_closure() -> dict[str, Any]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["version"] == "0.36.0", "Lot 37 gate requires audited V3 release 0.36.0")
    overlay = load(OVERLAY_PATH)
    require(overlay["latest_implemented_lot"] == 36, "lifecycle latest lot must be 36")
    lot36 = overlay["lots"]["36"]
    require(lot36["status"] == "IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY", "Lot 36 status changed")
    require(lot36["v3_closed"] is True, "V3 is not post-merge closed")
    require(lot36["implementation_commit"] == EXPECTED_LOT36_IMPLEMENTATION, "Lot 36 implementation changed")
    require(lot36["evidence_commit"] == EXPECTED_LOT36_EVIDENCE, "Lot 36 evidence changed")
    require(lot36["exact_ci_commit"] == EXPECTED_LOT36_EXACT_CI, "Lot 36 exact CI changed")
    require(lot36["merged_commit"] == EXPECTED_LOT36_MERGE, "Lot 36 implementation merge changed")
    require(
        overlay["lots"]["37"] == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 37 must still be locked before gate merge",
    )
    for field in (
        "trade_allowed",
        "execution_allowed",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "raw_data_mutation_allowed",
    ):
        require(lot36[field] is False, f"Lot 36 permission enabled: {field}")
    return lot36


def validate_lot36_evidence() -> dict[str, object]:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    manifest = load(MANIFEST_PATH)
    replay = load(REPLAY_PATH)
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    validate_payload_checksum(state, "output_checksum", EXPECTED_STATE_CHECKSUM, "Lot 36 state")
    validate_payload_checksum(audit, "audit_checksum", EXPECTED_AUDIT_CHECKSUM, "Lot 36 audit")
    require(audit["state_output_checksum"] == EXPECTED_STATE_CHECKSUM, "Lot 36 state/audit link changed")
    require(state["closure_manifest"] == manifest, "Lot 36 manifest collection changed")
    require(manifest["manifest_checksum"] == EXPECTED_MANIFEST_CHECKSUM, "Lot 36 manifest checksum changed")
    require(replay["replay_checksum"] == EXPECTED_REPLAY_CHECKSUM, "Lot 36 replay checksum changed")
    require(replay["replay_status"] == "REPLAY_MATCH" and replay["match"] is True, "Lot 36 replay changed")
    require(state["validation_state"] == "VALIDATED_V3_CLOSURE_CANDIDATE", "Lot 36 state validation changed")
    require(state["data_quality_veto"]["action"] == "ALLOW_ANALYSIS", "Lot 36 quality veto changed")
    require(state["reconciliation_veto"]["action"] == "ALLOW_ANALYSIS", "Lot 36 reconciliation veto changed")
    require(coverage["status"] == "PASS", "Lot 36 coverage not PASS")
    require(coverage["line_coverage_percent"] == 100.0, "Lot 36 line coverage changed")
    require(coverage["branch_coverage_percent"] == 100.0, "Lot 36 branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "Lot 36 anti-flake changed")
    require(mutation["status"] == "PASS", "Lot 36 mutation not PASS")
    require(mutation["mutation_score_percent"] == 83.48, "Lot 36 mutation score changed")
    return {
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "anti_flake_repetitions": coverage["anti_flake_repetitions"],
    }


def validate_l2_fixture(path: Path) -> None:
    require(file_sha256(path) == EXPECTED_L2_SHA256, "Lot 37 L2 fixture bytes changed")
    fixture = load(path)
    require(fixture["schema_version"] == "lot37-offline-l2-availability-fixture-v1", "L2 fixture schema changed")
    require(fixture["fixture_only"] is True, "L2 fixture must remain fixture-only")
    require(fixture["canonical_contract"] is False, "L2 fixture cannot predefine Lot 37 canonical contract")
    require(fixture["used_for_decision"] is False, "L2 fixture cannot be decision data")
    event = parse_utc(fixture["event_time"], "L2 event_time")
    available = parse_utc(fixture["available_at"], "L2 available_at")
    require(event <= available, "L2 fixture violates causal availability")
    bids = fixture["bids"]
    asks = fixture["asks"]
    require(isinstance(bids, list) and bids, "L2 bids missing")
    require(isinstance(asks, list) and asks, "L2 asks missing")
    bid_prices = [decimal_positive(level["price"], "bid price") for level in bids]
    ask_prices = [decimal_positive(level["price"], "ask price") for level in asks]
    for level in (*bids, *asks):
        decimal_positive(level["quantity"], "book quantity")
    require(max(bid_prices) < min(ask_prices), "L2 availability fixture is crossed or locked")


def validate_trade_fixture(path: Path) -> None:
    require(file_sha256(path) == EXPECTED_TRADE_SHA256, "Lot 37 trade fixture bytes changed")
    fixture = load(path)
    require(fixture["schema_version"] == "lot37-offline-trade-availability-fixture-v1", "trade fixture schema changed")
    require(fixture["fixture_only"] is True, "trade fixture must remain fixture-only")
    require(fixture["canonical_contract"] is False, "trade fixture cannot predefine Lot 37 canonical contract")
    require(fixture["used_for_decision"] is False, "trade fixture cannot be decision data")
    event = parse_utc(fixture["event_time"], "trade event_time")
    available = parse_utc(fixture["available_at"], "trade available_at")
    require(event <= available, "trade fixture violates causal availability")
    trades = fixture["trades"]
    require(isinstance(trades, list) and trades, "trade availability records missing")
    ids: set[str] = set()
    for trade in trades:
        require(trade["trade_id"] not in ids, "duplicate trade fixture id")
        ids.add(trade["trade_id"])
        decimal_positive(trade["price"], "trade price")
        decimal_positive(trade["quantity"], "trade quantity")
        require(trade["side"] == "UNKNOWN", "gate fixture must not classify aggressor side")


def validate_prerequisites(gate: dict[str, Any], lot36: dict[str, Any], quality: dict[str, object]) -> None:
    expected = {
        "latest_implemented_lot": 36,
        "v3_closed": True,
        "lot36_status": lot36["status"],
        "lot36_post_merge_audit_merge_commit": EXPECTED_BASE_COMMIT,
        "lot36_implementation_commit": EXPECTED_LOT36_IMPLEMENTATION,
        "lot36_evidence_commit": EXPECTED_LOT36_EVIDENCE,
        "lot36_exact_ci_commit": EXPECTED_LOT36_EXACT_CI,
        "lot36_implementation_merged_commit": EXPECTED_LOT36_MERGE,
        "lot36_state_checksum": EXPECTED_STATE_CHECKSUM,
        "lot36_audit_checksum": EXPECTED_AUDIT_CHECKSUM,
        "lot36_manifest_checksum": EXPECTED_MANIFEST_CHECKSUM,
        "lot36_replay_checksum": EXPECTED_REPLAY_CHECKSUM,
        "line_coverage_percent": quality["line_coverage_percent"],
        "branch_coverage_percent": quality["branch_coverage_percent"],
        "mutation_score_percent": quality["mutation_score_percent"],
        "anti_flake_repetitions": quality["anti_flake_repetitions"],
        "offline_l2_fixture_path": "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json",
        "offline_l2_fixture_sha256": EXPECTED_L2_SHA256,
        "offline_trade_fixture_path": "tests/fixtures/lot37/offline_trade_availability_fixture_v1.json",
        "offline_trade_fixture_sha256": EXPECTED_TRADE_SHA256,
        "offline_input_availability_status": "AVAILABLE_FIXTURE_ONLY_NON_CANONICAL",
    }
    require(gate["prerequisites"] == expected, "Lot 37 prerequisites changed")
    validate_l2_fixture(ROOT / expected["offline_l2_fixture_path"])
    validate_trade_fixture(ROOT / expected["offline_trade_fixture_path"])


def validate_scope(gate: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version": "lot37-v4-entry-gate-v1",
        "target_lot": 37,
        "base_commit": EXPECTED_BASE_COMMIT,
        "current_version": "0.36.0",
        "gate_status": "GO_LOT37_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT37",
        "implementation_started": False,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "next_lot": 38,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, expected in expected_fields.items():
        require(gate[field] == expected, f"Lot 37 gate field changed: {field}")
    require(set(gate["allowed_scope"]) == EXPECTED_ALLOWED, "Lot 37 allowed scope changed")
    require(set(gate["required_outputs"]) == EXPECTED_OUTPUTS, "Lot 37 required outputs changed")
    require(set(gate["forbidden_scope"]) == EXPECTED_FORBIDDEN, "Lot 37 forbidden scope changed")
    require(gate["quality_gates"] == EXPECTED_QUALITY, "Lot 37 quality gates changed")
    require(gate["safety"] == EXPECTED_SAFETY, "Lot 37 safety boundary changed")


def validate() -> dict[str, object]:
    gate = load(GATE_PATH)
    validate_payload_checksum(gate, "output_checksum", EXPECTED_GATE_CHECKSUM, "Lot 37 gate")
    validate_roadmap(gate)
    lot36 = validate_v3_closure()
    quality = validate_lot36_evidence()
    validate_prerequisites(gate, lot36, quality)
    validate_scope(gate)
    return {
        "schema_version": "lot37-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT37_IMPLEMENTATION_ENTRY",
        "canonical_title": "Microstructure Scope & Offline Data Contracts",
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "output_checksum": EXPECTED_GATE_CHECKSUM,
        "v3_closed": True,
        "offline_l2_available": True,
        "offline_trades_available": True,
        "next_locked_lot": 38,
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot37EntryGateError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT37 ENTRY GATE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
