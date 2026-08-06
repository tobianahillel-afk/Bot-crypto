from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MERGED_COMMIT = "235ee2e3a4eabd98e8a59241396f07fc4c29e39e"
EVIDENCE_COMMIT = "689079bb5f348aa1cf62059498fcaddf760665bd"
STATE_CHECKSUM = "c25c159fa3857eba9d08c7a8ddbd15a5c61e2b1d5b2aa78eae6cbf7e13dcdf05"
AUDIT_CHECKSUM = "e06ac07872ba51a1ca21af88f5298d08a362608bc7fe69b15e4d71afbbd60b6f"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


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


def version_tuple(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    assert len(parts) == 3
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def test_lot31_post_merge_release_and_lifecycle_are_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    historical = load_json("data/audit/roadmap_lifecycle_overlay_lot31.json")
    current = load_json("data/audit/roadmap_lifecycle_overlay_lot32.json")

    assert version_tuple(project["version"]) >= (0, 31, 0)
    assert historical["latest_implemented_lot"] == 31
    assert historical["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot30.json"
    lots = historical["lots"]
    assert lots["31"]["status"] == "IMPLEMENTED_VALIDATED_METADATA_ONLY"
    assert lots["31"]["implementation_commit"] == EVIDENCE_COMMIT
    assert lots["31"]["merged_commit"] == MERGED_COMMIT
    assert lots["31"]["pull_request"] == 18
    assert lots["31"]["runtime_mode"] == "DATA_GOVERNANCE_ONLY"
    assert lots["31"]["external_connectivity_allowed"] is False
    assert lots["31"]["network_ingestion_allowed"] is False
    assert lots["31"]["trade_allowed"] is False
    assert lots["31"]["execution_allowed"] is False
    assert lots["32"] == {"implementation_started": False, "status": "PLANNED_LOCKED"}
    assert current["lots"]["31"]["historical_overlay"] == (
        "data/audit/roadmap_lifecycle_overlay_lot31.json"
    )
    assert current["lots"]["31"]["status"] == "IMPLEMENTED_VALIDATED_METADATA_ONLY"


def test_lot31_post_merge_artifacts_are_independently_linked() -> None:
    state = load_json("data/audit/market_data_governance_scope_and_source_registry_lot31.json")
    audit = load_json(
        "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )
    registry = load_json("data/audit/source_registry_lot31.json")

    state_payload = dict(state)
    state_checksum = state_payload.pop("output_checksum")
    audit_payload = dict(audit)
    audit_checksum = audit_payload.pop("audit_checksum")

    assert canonical_checksum(state_payload) == state_checksum == STATE_CHECKSUM
    assert canonical_checksum(audit_payload) == audit_checksum == AUDIT_CHECKSUM
    assert state["source_registry"] == registry
    assert audit["state_output_checksum"] == state_checksum
    assert audit["code_commit"] == state["run_context"]["code_commit"] == EVIDENCE_COMMIT
    assert COMMIT_PATTERN.fullmatch(audit["code_commit"])


def test_lot31_post_merge_quality_and_safety_remain_certified() -> None:
    state = load_json("data/audit/market_data_governance_scope_and_source_registry_lot31.json")
    audit = load_json(
        "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )
    coverage = load_json("reports/lot31/coverage_summary.json")
    mutation = load_json("reports/lot31/mutation_summary.json")
    post_merge = (ROOT / "docs/LOT_31_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")

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

    assert coverage["status"] == "PASS"
    assert coverage["line_coverage_percent"] >= 95.0
    assert coverage["branch_coverage_percent"] >= 90.0
    assert mutation["status"] == "PASS"
    assert mutation["score_percent"] >= 80.0
    assert "GO_LOT31_POST_MERGE_AUDIT" in post_merge
    assert "Lot 32 remains locked" in post_merge
