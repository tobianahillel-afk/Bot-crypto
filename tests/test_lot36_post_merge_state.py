from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_lot36_post_merge import (
    AUDIT_CHECKSUM,
    EVIDENCE_COMMIT,
    EXACT_CI_COMMIT,
    MERGED_COMMIT,
    STATE_CHECKSUM,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_lot36_post_merge_validator_closes_v3() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT36_POST_MERGE_V3_CLOSED"
    assert result["merged_commit"] == MERGED_COMMIT
    assert result["evidence_commit"] == EVIDENCE_COMMIT
    assert result["exact_ci_commit"] == EXACT_CI_COMMIT
    assert result["state_output_checksum"] == STATE_CHECKSUM
    assert result["audit_checksum"] == AUDIT_CHECKSUM
    assert result["latest_implemented_lot"] == 36
    assert result["v3_closed"] is True
    assert result["next_lot"] == 37
    assert result["next_lot_status"] == "PLANNED_LOCKED"


def test_lot37_remains_exactly_locked() -> None:
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot36.json").read_text(
            encoding="utf-8"
        )
    )
    assert overlay["lots"]["37"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot36_overlay_preserves_all_prior_lifecycle_entries() -> None:
    previous = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot35.json").read_text(
            encoding="utf-8"
        )
    )
    current = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot36.json").read_text(
            encoding="utf-8"
        )
    )
    for lot in range(26, 36):
        assert current["lots"][str(lot)] == previous["lots"][str(lot)]


def test_historical_candidate_manifest_is_not_rewritten_by_final_audit() -> None:
    manifest = json.loads(
        (ROOT / "data/audit/closure_manifest_lot36.json").read_text(encoding="utf-8")
    )
    result = validate()
    assert manifest["v3_closed"] is False
    assert manifest["closure_status"] == "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT"
    assert result["v3_closed"] is True


def test_lot36_post_merge_keeps_execution_fail_closed() -> None:
    result = validate()
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0
