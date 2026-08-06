from __future__ import annotations

import hashlib
import json
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


def test_lot27_post_merge_release_state_is_consistent() -> None:
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
    audit = json.loads(
        (ROOT / "data/audit/global_market_context_aggregator_audit_lot27.json").read_text(
            encoding="utf-8"
        )
    )
    report = (ROOT / "reports/lot_27_global_market_context_aggregator_report.md").read_text(
        encoding="utf-8"
    )
    worklog = (ROOT / "docs/LOT_27_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")

    assert overlay["latest_implemented_lot"] == 27
    assert overlay["lots"]["27"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
    assert overlay["lots"]["27"]["implementation_commit"] == "bae0633d1fb28a77eb91111796d35549a5a365c8"
    assert overlay["lots"]["27"]["trade_allowed"] is False
    assert overlay["lots"]["27"]["execution_allowed"] is False
    assert overlay["lots"]["28"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert output_checksum == canonical_checksum(payload)
    assert audit["output_checksum"] == output_checksum
    assert audit["replay_status"] == "MATCH"
    assert audit["code_commit"] == state["code_commit"]
    assert state["dominant_state"] == "GLOBAL_CONTEXT_MIXED"
    assert state["aggregate_evidence_score"] == 0.5646
    assert state["weighted_coverage_ratio"] == 1.0
    assert state["conflict_states"] == ["MTF_DIVERGENT"]
    assert state["trade_allowed"] is False
    assert state["execution_allowed"] is False
    assert state["used_for_decision"] is False

    assert "GO_LOT27_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`" in worklog


def test_lot27_post_merge_tree_has_no_temporary_scaffolding() -> None:
    forbidden = (
        ROOT / ".github/workflows/lot27-final-reconciliation.yml",
        ROOT / "scripts/finalize_lot27_release.py",
        ROOT / ".github/workflows/lot27-one-shot-bandit-fix.yml",
    )
    assert not [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
