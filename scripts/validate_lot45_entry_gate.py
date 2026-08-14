#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

GATE_PATH = ROOT / "data/audit/lot45_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot45_v4_entry_gate_v1.schema.json"
ROADMAP_PATH = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"

EXPECTED_BASE = "1fd85f26102f94d4c42a8f515b522c23028bac89"
EXPECTED_BASE_PARENT = "e390b6e5d76c53d9dd6d74724f3246b92e628079"
EXPECTED_AUDIT_PR_HEAD = "0ddf2c3150b339b8573fead8c942c4b1efa4b300"
EXPECTED_POST_MERGE_CHECKSUM = "b8b531b2fcb09a30728549cc480d54d9be71504356468704c102ff085c39ea9a"
EXPECTED_GATE_CHECKSUM = "15ca4d69e59a0898f32eb9cbe558571ecf00ae496ec5d41075da1124393d4468"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"

GATE_PATHS = {
    ".github/workflows/lot45-entry-gate.yml",
    "contracts/schemas/lot45_v4_entry_gate_v1.schema.json",
    "data/audit/lot45_v4_entry_gate.json",
    "docs/LOT_45_V4_ENTRY_GATE.md",
    "reports/lot_45_v4_entry_gate_report.md",
    "scripts/validate_lot45_entry_gate.py",
    "tests/test_lot45_v4_entry_gate.py",
}

EXPECTED_INPUTS = {
    "RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)",
    "LineageEnvelopeV1 des artefacts produits par les lots préalables",
}
EXPECTED_OUTPUTS = {
    "OrderFlowDeltaCVDEngineStateV1",
    "OrderFlowDeltaCVDEngineAuditV1",
    "OrderFlowStateV1",
    "CVDSeriesV1",
}
EXPECTED_IMPLEMENTATION_FILES = {
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
    "scripts/run_lot45_order_flow_delta_and_cvd_engine.py",
    "scripts/validate_lot45.py",
    "tests/test_lot45_order_flow_delta_and_cvd_engine.py",
    "data/audit/order_flow_delta_and_cvd_engine_lot45.json",
    "reports/lot_45_order_flow_delta_and_cvd_engine_report.md",
    "docs/LOT_45_ORDER_FLOW_DELTA_AND_CVD_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_45.md",
}
LOT45_FORBIDDEN_BEFORE_GATE = EXPECTED_IMPLEMENTATION_FILES | {
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_validation.py",
    "config/microstructure/order_flow_delta_and_cvd_engine_v1.json",
    "contracts/schemas/order_flow_delta_cvd_engine_audit_v1.schema.json",
    "contracts/schemas/order_flow_delta_cvd_engine_state_v1.schema.json",
    "contracts/schemas/order_flow_state_v1.schema.json",
    "contracts/schemas/cvd_series_v1.schema.json",
    "tests/test_lot45_schema_contracts.py",
}
LOT46_FORBIDDEN = {
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine_models.py",
    "scripts/run_lot46_trade_classification_confidence_engine.py",
    "scripts/validate_lot46.py",
    "tests/test_lot46_trade_classification_confidence_engine.py",
    "data/audit/trade_classification_confidence_engine_lot46.json",
    "reports/lot_46_trade_classification_confidence_engine_report.md",
    "docs/LOT_46_TRADE_CLASSIFICATION_CONFIDENCE_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_46.md",
}
EXPECTED_SAFETY = {
    "analysis_only": True,
    "trade_allowed": False,
    "execution_allowed": False,
    "approved_size": 0,
    "signal_generation_allowed": False,
    "risk_approval_allowed": False,
    "order_routing_allowed": False,
    "external_connectivity_allowed": False,
    "network_ingestion_allowed": False,
    "real_credentials_allowed": False,
    "participant_behavior_inference_explicitly_labeled": True,
    "scenario_score_is_signal": False,
}
EXPECTED_QUALITY = {
    "line_coverage_min_percent": 95,
    "branch_coverage_min_percent": 90,
    "mutation_score_min_percent": 80,
    "anti_flake_repetitions": 3,
}


class Lot45EntryGateError(RuntimeError):
    """Raised when the Lot 45 implementation entry gate is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot45EntryGateError(message)


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def changed_paths(base: str, head: str) -> set[str]:
    raw = git("diff", "--name-only", base, head)
    return {line for line in raw.splitlines() if line}


def validate_gate_payload(gate: dict[str, Any]) -> None:
    checksum = gate.get("gate_checksum")
    require(checksum == EXPECTED_GATE_CHECKSUM, "Lot45 gate checksum field changed")
    without_checksum = dict(gate)
    without_checksum.pop("gate_checksum", None)
    require(canonical_checksum(without_checksum) == EXPECTED_GATE_CHECKSUM, "Lot45 gate payload checksum mismatch")

    expected_scalars = {
        "schema_version": "lot45-v4-entry-gate-v1",
        "target_lot": 45,
        "base_commit": EXPECTED_BASE,
        "post_merge_audit_pr_head": EXPECTED_AUDIT_PR_HEAD,
        "post_merge_audit_merge": EXPECTED_BASE,
        "post_merge_verdict": "GO_LOT44_POST_MERGE",
        "post_merge_checksum": EXPECTED_POST_MERGE_CHECKSUM,
        "current_version": "0.44.0",
        "gate_status": "GO_LOT45_IMPLEMENTATION_ENTRY",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "responsible_component": "MicrostructureDomain",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "next_lot": 46,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for key, expected in expected_scalars.items():
        require(gate.get(key) == expected, f"Lot45 gate field changed: {key}")
    require(set(gate.get("input_contracts", [])) == EXPECTED_INPUTS, "Lot45 input contracts changed")
    require(set(gate.get("output_contracts", [])) == EXPECTED_OUTPUTS, "Lot45 output contracts changed")
    require(gate.get("safety") == EXPECTED_SAFETY, "Lot45 gate safety policy changed")
    require(gate.get("quality") == EXPECTED_QUALITY, "Lot45 quality thresholds changed")


def validate_schema_contract() -> None:
    schema = load(SCHEMA_PATH)
    require(schema.get("additionalProperties") is False, "Lot45 gate schema must be closed")
    props = schema.get("properties")
    require(isinstance(props, dict), "Lot45 gate schema properties missing")
    constants = {
        "schema_version": "lot45-v4-entry-gate-v1",
        "target_lot": 45,
        "base_commit": EXPECTED_BASE,
        "post_merge_audit_pr_head": EXPECTED_AUDIT_PR_HEAD,
        "post_merge_audit_merge": EXPECTED_BASE,
        "post_merge_verdict": "GO_LOT44_POST_MERGE",
        "post_merge_checksum": EXPECTED_POST_MERGE_CHECKSUM,
        "current_version": "0.44.0",
        "gate_status": "GO_LOT45_IMPLEMENTATION_ENTRY",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "responsible_component": "MicrostructureDomain",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "next_lot": 46,
        "next_lot_status": "PLANNED_LOCKED",
        "gate_checksum": EXPECTED_GATE_CHECKSUM,
    }
    for field, value in constants.items():
        require(props.get(field, {}).get("const") == value, f"Lot45 schema constant changed: {field}")


def roadmap_record(source_line: int) -> dict[str, Any]:
    raw = ROADMAP_PATH.read_bytes()
    require(git_blob_sha(raw) == EXPECTED_ROADMAP_BLOB, "canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) >= source_line, f"canonical roadmap line {source_line} missing")
    record = json.loads(lines[source_line - 1])
    require(isinstance(record, dict), "canonical roadmap record must be an object")
    return record


def validate_roadmap(gate: dict[str, Any]) -> None:
    lot45 = roadmap_record(46)
    expected = {
        "lot_id": "Lot 45",
        "lot_number": 45,
        "title": "Order Flow, Delta & CVD Engine",
        "version_id": "V4_MICROSTRUCTURE_LIQUIDITY",
        "version_number": 4,
        "responsible_component": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(lot45.get(field) == value, f"canonical Lot45 field changed: {field}")
    require(set(lot45.get("input_contracts", [])) == EXPECTED_INPUTS, "canonical Lot45 inputs changed")
    require(set(lot45.get("output_contracts", [])) == EXPECTED_OUTPUTS, "canonical Lot45 outputs changed")
    require(set(lot45.get("implementation_files", [])) == EXPECTED_IMPLEMENTATION_FILES, "canonical Lot45 implementation file set changed")
    require(len(lot45.get("processing_sequence", [])) >= 5, "canonical Lot45 processing sequence incomplete")
    require(len(lot45.get("acceptance_tests", [])) >= 8, "canonical Lot45 acceptance tests incomplete")

    binding = gate.get("canonical_roadmap")
    require(isinstance(binding, dict), "Lot45 canonical roadmap binding missing")
    require(binding.get("source_line") == 46, "Lot45 roadmap source line changed")
    require(binding.get("source_blob_sha") == EXPECTED_ROADMAP_BLOB, "Lot45 roadmap blob binding changed")
    require(binding.get("lot_id") == "Lot 45", "Lot45 roadmap lot binding changed")
    require(binding.get("title") == "Order Flow, Delta & CVD Engine", "Lot45 roadmap title binding changed")

    lot46 = roadmap_record(47)
    require(lot46.get("lot_id") == "Lot 46", "canonical Lot46 identity changed")
    require(lot46.get("title") == "Trade Classification Confidence Engine", "canonical Lot46 title changed")
    require(lot46.get("status") == "PLANNED_LOCKED", "Lot46 must remain locked")


def validate_git_transition() -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_BASE, "HEAD"],
        cwd=ROOT,
        check=True,
    )
    parents = set(git("show", "-s", "--format=%P", EXPECTED_BASE).split())
    require(parents == {EXPECTED_BASE_PARENT, EXPECTED_AUDIT_PR_HEAD}, "Lot44 audit merge parents changed")
    paths = changed_paths(EXPECTED_BASE, "HEAD")
    require(paths == GATE_PATHS, f"Lot45 gate branch path set changed: {sorted(paths)}")
    require(changed_paths(EXPECTED_AUDIT_PR_HEAD, EXPECTED_BASE) == set(), "Lot44 audit merge tree differs from certified audit PR head")


def validate_downstream_locks() -> None:
    for path in sorted(LOT45_FORBIDDEN_BEFORE_GATE | LOT46_FORBIDDEN):
        require(not (ROOT / path).exists(), f"implementation started before Lot45 gate: {path}")


def validate() -> dict[str, Any]:
    gate = load(GATE_PATH)
    validate_gate_payload(gate)
    validate_schema_contract()
    validate_roadmap(gate)
    validate_git_transition()
    validate_downstream_locks()
    return {
        "schema_version": "lot45-v4-entry-gate-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT45_IMPLEMENTATION_ENTRY",
        "base_commit": EXPECTED_BASE,
        "post_merge_verdict": "GO_LOT44_POST_MERGE",
        "post_merge_checksum": EXPECTED_POST_MERGE_CHECKSUM,
        "target_lot": 45,
        "lot46_status": "PLANNED_LOCKED",
        "gate_checksum": EXPECTED_GATE_CHECKSUM,
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
