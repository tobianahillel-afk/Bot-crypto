from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_lot33_post_merge import (
    AUDIT_CHECKSUM,
    MERGED_COMMIT,
    STATE_CHECKSUM,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict[str, object]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot33_post_merge_validator_passes() -> None:
    assert validate() == {
        "schema_version": "lot33-post-merge-validation-v1",
        "status": "PASS",
        "project_version": "0.33.0",
        "latest_implemented_lot": 33,
        "next_locked_lot": 34,
        "state_output_checksum": STATE_CHECKSUM,
        "audit_checksum": AUDIT_CHECKSUM,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def test_lot33_post_merge_overlay_keeps_history_and_lot34_locked() -> None:
    overlay = load("data/audit/roadmap_lifecycle_overlay_lot33.json")
    assert overlay["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot32.json"
    lots = overlay["lots"]
    assert isinstance(lots, dict)
    assert lots["31"]["status"] == "IMPLEMENTED_VALIDATED_METADATA_ONLY"
    assert lots["32"]["status"] == "IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY"
    assert lots["33"]["status"] == "IMPLEMENTED_VALIDATED_TEMPORAL_ONLY"
    assert lots["33"]["merged_commit"] == MERGED_COMMIT
    assert lots["34"] == {"implementation_started": False, "status": "PLANNED_LOCKED"}


def test_lot33_post_merge_docs_preserve_scope_and_safety() -> None:
    document = (ROOT / "docs/LOT_33_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    assert "GO_LOT33_POST_MERGE_AUDIT" in document
    assert "latest_implemented_lot=33" in document
    assert "lot34_status=PLANNED_LOCKED" in document
    assert "external_connectivity_allowed=false" in document
    assert "trade_allowed=false" in document
    assert "execution_allowed=false" in document
