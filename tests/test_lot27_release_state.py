from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot27_release_state_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot27.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (ROOT / "data/audit/global_market_context_aggregator_lot27.json").read_text(
            encoding="utf-8"
        )
    )
    report = (ROOT / "reports/lot_27_global_market_context_aggregator_report.md").read_text(
        encoding="utf-8"
    )
    worklog = (ROOT / "docs/LOT_27_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")

    assert project["version"] == "0.27.0"
    assert overlay["latest_implemented_lot"] == 27
    assert overlay["lots"]["27"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
    assert overlay["lots"]["27"]["trade_allowed"] is False
    assert overlay["lots"]["27"]["execution_allowed"] is False
    assert overlay["lots"]["28"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }
    assert state["dominant_state"] == "GLOBAL_CONTEXT_MIXED"
    assert state["aggregate_evidence_score"] == 0.5646
    assert state["weighted_coverage_ratio"] == 1.0
    assert state["trade_allowed"] is False
    assert state["execution_allowed"] is False
    assert "GO_LOT27_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`" in worklog


def test_lot27_release_tree_contains_no_temporary_finalization_files() -> None:
    forbidden = (
        ROOT / ".github/workflows/lot27-final-reconciliation.yml",
        ROOT / "scripts/finalize_lot27_release.py",
        ROOT / ".github/workflows/lot27-one-shot-bandit-fix.yml",
    )
    assert not [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
