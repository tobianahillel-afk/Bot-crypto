from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot26_post_merge_release_state_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot26.json").read_text(
            encoding="utf-8"
        )
    )
    report = (ROOT / "reports/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_FINAL_REPORT.md").read_text(
        encoding="utf-8"
    )
    worklog = (ROOT / "docs/LOT_26_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")

    assert project["version"] == "0.26.0"
    assert overlay["latest_implemented_lot"] == 26
    assert overlay["lots"]["26"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
    assert overlay["lots"]["26"]["trade_allowed"] is False
    assert overlay["lots"]["26"]["execution_allowed"] is False
    assert overlay["lots"]["27"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }
    assert "GO_LOT26_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`" in worklog


def test_lot26_post_merge_tree_contains_no_reconciliation_scaffolding() -> None:
    forbidden = (
        ROOT / ".github/workflows/lot26-final-reconciliation.yml",
        ROOT / "scripts/finalize_lot26_release.py",
        ROOT / ".github/workflows/lot26-ruff-autofix.yml",
        ROOT / ".github/workflows/lot26-mypy-fix.yml",
        ROOT / ".github/workflows/lot26-test-import-fix.yml",
    )
    assert not [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
