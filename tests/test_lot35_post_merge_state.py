from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_lot35_post_merge import (
    EVIDENCE_COMMIT,
    EXPECTED_AUDIT_CHECKSUM,
    EXPECTED_STATE_CHECKSUM,
    MERGED_COMMIT,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_lot35_post_merge_validator_passes() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT35_POST_MERGE"
    assert result["merged_commit"] == MERGED_COMMIT
    assert result["evidence_commit"] == EVIDENCE_COMMIT
    assert result["state_output_checksum"] == EXPECTED_STATE_CHECKSUM
    assert result["audit_checksum"] == EXPECTED_AUDIT_CHECKSUM
    assert result["latest_implemented_lot"] == 35
    assert result["next_lot"] == 36
    assert result["next_lot_status"] == "PLANNED_LOCKED"


def test_lot36_remains_exactly_locked() -> None:
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot35.json").read_text(encoding="utf-8")
    )
    assert overlay["lots"]["36"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot35_post_merge_keeps_execution_fail_closed() -> None:
    result = validate()
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0
