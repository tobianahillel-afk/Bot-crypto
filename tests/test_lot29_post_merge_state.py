from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGED_IMPLEMENTATION_COMMIT = "89d5b01f4bc49b30660c46babfb837f3bcc0a276"
IMPLEMENTATION_EVIDENCE_COMMIT = "271e913514eb2edeee6e6a50208b0686004a2ca5"
EXPECTED_CHAIN_CHECKSUM = "06826f423e3e9f3a1f7f6090a781eddbcd2dffd667815ee1d4d71df08393ffdd"
EXPECTED_OUTPUT_CHECKSUM = "e98a3334097bba1e7d354b65357cb6cad5a500c5e5efb2122096cb3cb2c0608c"


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(relative: str) -> dict[str, object]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot29_post_merge_release_and_lifecycle_are_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = load_json("data/audit/roadmap_lifecycle_overlay_lot29.json")

    assert project["version"] == "0.29.0"
    assert overlay["latest_implemented_lot"] == 29
    lots = overlay["lots"]
    assert isinstance(lots, dict)
    assert lots["29"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY"
    assert lots["29"]["implementation_commit"] == IMPLEMENTATION_EVIDENCE_COMMIT
    assert lots["29"]["merged_commit"] == MERGED_IMPLEMENTATION_COMMIT
    assert lots["29"]["pull_request"] == 12
    assert lots["29"]["trade_allowed"] is False
    assert lots["29"]["execution_allowed"] is False
    assert lots["30"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot29_post_merge_evidence_is_independently_linked() -> None:
    state = load_json("data/audit/v2_deterministic_replay_and_audit_lot29.json")
    audit = load_json("data/audit/v2_deterministic_replay_and_audit_audit_lot29.json")
    closure = load_json("data/audit/v2_replay_closure_manifest_lot29.json")

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert output_checksum == EXPECTED_OUTPUT_CHECKSUM
    assert canonical_checksum(payload) == EXPECTED_OUTPUT_CHECKSUM

    assert state["code_commit"] == IMPLEMENTATION_EVIDENCE_COMMIT
    assert state["closure_manifest"] == closure
    assert state["replay_status"] == "MATCH"
    assert state["reason_codes"] == [
        "V2_ARTIFACT_CHAIN_MATCH",
        "V2_VALIDATORS_PASS",
        "V2_OFFLINE_ONLY",
    ]
    assert closure["lot_sequence"] == list(range(21, 29))
    assert closure["artifact_count"] == 8
    assert closure["validator_count"] == 8
    assert closure["chain_checksum"] == EXPECTED_CHAIN_CHECKSUM

    assert audit["code_commit"] == IMPLEMENTATION_EVIDENCE_COMMIT
    assert audit["output_checksum"] == EXPECTED_OUTPUT_CHECKSUM
    assert audit["chain_checksum"] == EXPECTED_CHAIN_CHECKSUM
    assert audit["replay_status"] == "MATCH"


def test_lot29_post_merge_safety_and_verdict_remain_fail_closed() -> None:
    state = load_json("data/audit/v2_deterministic_replay_and_audit_lot29.json")
    audit = load_json("data/audit/v2_deterministic_replay_and_audit_audit_lot29.json")
    worklog = (ROOT / "docs/LOT_29_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")
    report = (ROOT / "reports/lot_29_v2_deterministic_replay_and_audit_report.md").read_text(
        encoding="utf-8"
    )
    post_merge = (ROOT / "docs/LOT_29_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")

    for document in (state, audit):
        assert document["analysis_only"] is True
        assert document["used_for_decision"] is False
        assert document["trade_allowed"] is False
        assert document["execution_allowed"] is False
        assert document["approved_size"] == 0

    assert "GO_LOT29_V2_REPLAY_VALIDATED_OFFLINE_ONLY" in worklog
    assert "GO_LOT29_V2_REPLAY_VALIDATED_OFFLINE_ONLY" in report
    assert "GO_LOT29_POST_MERGE_AUDIT" in post_merge
    assert "Lot 30 remains `PLANNED_LOCKED`" in post_merge
