from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_COMMIT = "689079bb5f348aa1cf62059498fcaddf760665bd"


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(relative: str) -> dict[str, Any]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot31_release_artifacts_are_independently_linked() -> None:
    state = load_json("data/audit/market_data_governance_scope_and_source_registry_lot31.json")
    audit = load_json(
        "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )
    registry = load_json("data/audit/source_registry_lot31.json")

    state_payload = dict(state)
    state_checksum = state_payload.pop("output_checksum")
    audit_payload = dict(audit)
    audit_checksum = audit_payload.pop("audit_checksum")

    assert canonical_checksum(state_payload) == state_checksum
    assert canonical_checksum(audit_payload) == audit_checksum
    assert state["source_registry"] == registry
    assert audit["state_output_checksum"] == state_checksum
    assert audit["code_commit"] == state["run_context"]["code_commit"]
    assert COMMIT_PATTERN.fullmatch(audit["code_commit"])
    assert state["validation_state"] == "VALIDATED_METADATA_ONLY"
    assert audit["validation_state"] == "VALIDATED_METADATA_ONLY"


def test_lot31_release_registry_and_capabilities_remain_metadata_only() -> None:
    state = load_json("data/audit/market_data_governance_scope_and_source_registry_lot31.json")
    registry = state["source_registry"]
    sources = registry["sources"]

    assert registry["source_of_truth_id"] == "kraken-public-spot-metadata"
    assert len(sources) == 3
    assert sum(source["source_of_truth"] is True for source in sources) == 1
    assert all(source["auth_mode"] == "NONE" for source in sources)
    assert all(source["enabled"] is False for source in sources)
    assert all(source["connection_status"] == "DISABLED" for source in sources)

    statuses = {item["capability"]: item["status"] for item in state["capability_matrix"]}
    assert statuses["source_registry"] == "REQUIRED"
    assert statuses["instrument_normalization"] == "DISABLED"
    assert statuses["canonical_time"] == "DISABLED"
    assert statuses["data_quality"] == "DISABLED"
    assert statuses["continuous_market_data"] == "DISABLED"
    assert statuses["external_connectivity"] == "FORBIDDEN"
    assert statuses["forecast_generation"] == "FORBIDDEN"
    assert statuses["signal_generation"] == "FORBIDDEN"
    assert statuses["trade_execution"] == "FORBIDDEN"


def test_lot31_release_safety_and_reason_codes_are_exact() -> None:
    state = load_json("data/audit/market_data_governance_scope_and_source_registry_lot31.json")
    audit = load_json(
        "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )
    expected_safety = {
        "analysis_only": True,
        "used_for_decision": False,
        "external_connectivity_allowed": False,
        "network_ingestion_allowed": False,
        "real_credentials_allowed": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected_safety.items():
        assert state[field] == value
        assert audit[field] == value
    assert state["reason_codes"] == [
        "LOT31_ENTRY_GATE_VERIFIED",
        "SOURCE_REGISTRY_METADATA_VALIDATED",
        "SOURCE_OF_TRUTH_AND_BACKUPS_DECLARED",
        "EXTERNAL_CONNECTIVITY_DISABLED",
        "LOT32_REMAINS_LOCKED",
    ]


def test_lot31_release_quality_summaries_pass_thresholds() -> None:
    coverage = load_json("reports/lot31/coverage_summary.json")
    mutation = load_json("reports/lot31/mutation_summary.json")

    assert coverage["evidence_commit"] == EVIDENCE_COMMIT
    assert coverage["status"] == "PASS"
    assert coverage["line_coverage_percent"] >= coverage["minimum_line_coverage_percent"]
    assert coverage["branch_coverage_percent"] >= coverage["minimum_branch_coverage_percent"]

    assert mutation["evidence_commit"] == EVIDENCE_COMMIT
    assert mutation["status"] == "PASS"
    assert mutation["score_percent"] >= mutation["minimum_score_percent"]
    assert mutation["killed"] + mutation["timeout"] + mutation["survived"] == mutation["total"]
