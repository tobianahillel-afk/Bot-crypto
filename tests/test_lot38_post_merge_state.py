from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.validate_lot38_post_merge import (
    EVIDENCE_HEAD,
    MERGED_COMMIT,
    SOURCE_HEAD,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
CERTIFIED_ARTIFACTS = (
    "data/audit/order_book_l2_snapshot_engine_lot38.json",
    "data/audit/order_book_l2_snapshot_engine_audit_lot38.json",
    "data/audit/order_book_snapshot_lot38.json",
    "data/audit/book_health_state_lot38.json",
)


def _restore_missing_certified_artifacts() -> None:
    for relative_path in CERTIFIED_ARTIFACTS:
        path = ROOT / relative_path
        if path.exists():
            continue
        result = subprocess.run(
            ["git", "show", f"{MERGED_COMMIT}:{relative_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(result.stdout)


@pytest.fixture(autouse=True)
def _certified_artifacts_available() -> None:
    _restore_missing_certified_artifacts()


def test_lot38_post_merge_validator_passes() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT38_POST_MERGE"
    assert result["project_version"] == "0.38.0"
    assert result["source_head"] == SOURCE_HEAD
    assert result["evidence_head"] == EVIDENCE_HEAD
    assert result["merged_commit"] == MERGED_COMMIT
    assert result["latest_implemented_lot"] == 38
    assert result["next_lot"] == 39
    assert result["next_lot_status"] == "PLANNED_LOCKED"
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0


def test_lot38_lifecycle_preserves_previous_lots_and_locks_lot39() -> None:
    previous = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot37.json").read_text(encoding="utf-8")
    )
    current = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot38.json").read_text(encoding="utf-8")
    )
    for lot in range(26, 38):
        assert current["lots"][str(lot)] == previous["lots"][str(lot)]
    assert current["latest_implemented_lot"] == 38
    assert current["lots"]["38"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY"
    assert current["lots"]["39"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot38_audit_does_not_modify_certified_source() -> None:
    state = json.loads(
        (ROOT / "data/audit/order_book_l2_snapshot_engine_lot38.json").read_text(encoding="utf-8")
    )
    assert state["run_context"]["code_commit"] == SOURCE_HEAD
    assert state["validation_state"] == "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY"
    assert state["safety"]["trade_allowed"] is False
    assert state["safety"]["execution_allowed"] is False
    assert state["safety"]["approved_size"] == 0
    assert "LOT39_REMAINS_LOCKED" in state["reason_codes"]
