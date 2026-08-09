from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_lot36_post_merge import (
    AUDIT_CHECKSUM,
    EVIDENCE_COMMIT,
    EXACT_CI_COMMIT,
    MERGED_COMMIT,
    STATE_CHECKSUM,
    canonical_checksum,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, object]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot36_historical_post_merge_closure_is_exact() -> None:
    overlay = _load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    lot36 = overlay["lots"]["36"]
    assert overlay["latest_implemented_lot"] == 36
    assert lot36["status"] == "IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY"
    assert lot36["merged_commit"] == MERGED_COMMIT
    assert lot36["evidence_commit"] == EVIDENCE_COMMIT
    assert lot36["exact_ci_commit"] == EXACT_CI_COMMIT
    assert lot36["v3_closed"] is True
    assert overlay["lots"]["37"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot36_certified_artifact_checksums_remain_exact() -> None:
    state = _load("data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json")
    audit = _load("data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json")
    state_body = dict(state)
    audit_body = dict(audit)
    state_checksum = state_body.pop("output_checksum")
    audit_checksum = audit_body.pop("audit_checksum")
    assert state_checksum == STATE_CHECKSUM
    assert audit_checksum == AUDIT_CHECKSUM
    assert canonical_checksum(state_body) == STATE_CHECKSUM
    assert canonical_checksum(audit_body) == AUDIT_CHECKSUM
    assert audit["state_output_checksum"] == STATE_CHECKSUM


def test_lot36_overlay_preserves_all_prior_lifecycle_entries() -> None:
    previous = _load("data/audit/roadmap_lifecycle_overlay_lot35.json")
    current = _load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    for lot in range(26, 36):
        assert current["lots"][str(lot)] == previous["lots"][str(lot)]


def test_historical_candidate_manifest_is_not_rewritten_by_final_audit() -> None:
    manifest = _load("data/audit/closure_manifest_lot36.json")
    overlay = _load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    assert manifest["v3_closed"] is False
    assert manifest["closure_status"] == "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT"
    assert overlay["lots"]["36"]["v3_closed"] is True


def test_lot36_historical_post_merge_keeps_execution_fail_closed() -> None:
    overlay = _load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    lot36 = overlay["lots"]["36"]
    for field in (
        "trade_allowed",
        "execution_allowed",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "raw_data_mutation_allowed",
    ):
        assert lot36[field] is False
