from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_lot28_post_merge_release_state_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot28.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (ROOT / "data/audit/explanation_core_and_why_not_trade_layer_lot28.json").read_text(
            encoding="utf-8"
        )
    )
    audit = json.loads(
        (ROOT / "data/audit/explanation_core_and_why_not_trade_layer_audit_lot28.json").read_text(
            encoding="utf-8"
        )
    )
    report = (
        ROOT / "reports/lot_28_explanation_core_and_why_not_trade_layer_report.md"
    ).read_text(encoding="utf-8")
    worklog = (ROOT / "docs/LOT_28_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")

    assert tuple(map(int, project["version"].split("."))) >= (0, 28, 0)
    assert overlay["latest_implemented_lot"] == 28
    assert overlay["lots"]["28"]["status"] == (
        "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
    )
    assert overlay["lots"]["28"]["trade_allowed"] is False
    assert overlay["lots"]["28"]["execution_allowed"] is False
    assert overlay["lots"]["29"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert output_checksum == canonical_checksum(payload)
    assert audit["output_checksum"] == output_checksum
    assert audit["replay_status"] == "MATCH"
    assert audit["code_commit"] == state["code_commit"]
    assert audit["statement_count"] == 14
    assert audit["why_not_reason_count"] == 3
    assert audit["dominant_reason_code"] == "WNT_PERMISSIONS_DISABLED"

    reasons = [
        reason["reason_code"] for reason in state["bundle"]["why_not_trade"]["reasons"]
    ]
    assert reasons == [
        "WNT_CONTEXT_MIXED",
        "WNT_MTF_DIVERGENCE",
        "WNT_PERMISSIONS_DISABLED",
    ]
    assert state["analysis_only"] is True
    assert state["used_for_decision"] is False
    assert state["trade_allowed"] is False
    assert state["execution_allowed"] is False
    assert state["approved_size"] == 0
    assert state["bundle"]["why_not_trade"]["no_order_intent_created"] is True

    assert "GO_LOT28_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`" in worklog


def test_lot28_post_merge_tree_has_no_temporary_scaffolding() -> None:
    forbidden = (
        ROOT / ".github/workflows/lot28-release-finalization.yml",
        ROOT / ".github/workflows/lot28-release-finalization-fix.yml",
        ROOT / ".github/workflows/lot28-release-finalization-fix-pr.yml",
        ROOT / "scripts/finalize_lot28_release.py",
    )
    assert not [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
