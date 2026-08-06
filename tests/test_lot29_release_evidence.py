from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_EVIDENCE_COMMIT = "271e913514eb2edeee6e6a50208b0686004a2ca5"
EXPECTED_CHAIN_CHECKSUM = "06826f423e3e9f3a1f7f6090a781eddbcd2dffd667815ee1d4d71df08393ffdd"
COMMIT_PATTERN = re.compile(r"^[a-f0-9]{40}$")


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


def test_lot29_committed_release_evidence_is_linked_and_deterministic() -> None:
    state = load_json("data/audit/v2_deterministic_replay_and_audit_lot29.json")
    audit = load_json("data/audit/v2_deterministic_replay_and_audit_audit_lot29.json")
    closure = load_json("data/audit/v2_replay_closure_manifest_lot29.json")

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert isinstance(output_checksum, str)
    assert canonical_checksum(payload) == output_checksum

    code_commit = state["code_commit"]
    assert isinstance(code_commit, str)
    assert COMMIT_PATTERN.fullmatch(code_commit)
    assert audit["code_commit"] == code_commit
    assert audit["output_checksum"] == output_checksum

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

    assert audit["chain_checksum"] == EXPECTED_CHAIN_CHECKSUM
    assert audit["replay_status"] == "MATCH"
    assert audit["artifact_count"] == 8
    assert audit["validator_count"] == 8


def test_lot29_committed_release_evidence_remains_fail_closed() -> None:
    state = load_json("data/audit/v2_deterministic_replay_and_audit_lot29.json")
    audit = load_json("data/audit/v2_deterministic_replay_and_audit_audit_lot29.json")

    for document in (state, audit):
        assert document["analysis_only"] is True
        assert document["used_for_decision"] is False
        assert document["trade_allowed"] is False
        assert document["execution_allowed"] is False
        assert document["approved_size"] == 0


def test_lot29_worklog_and_report_certify_only_offline_replay() -> None:
    worklog = (ROOT / "docs/LOT_29_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")
    report = (ROOT / "reports/lot_29_v2_deterministic_replay_and_audit_report.md").read_text(
        encoding="utf-8"
    )

    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY`" in worklog
    assert IMPLEMENTATION_EVIDENCE_COMMIT in worklog
    assert "GO_LOT29_V2_REPLAY_VALIDATED_OFFLINE_ONLY" in worklog
    assert "GO_LOT29_V2_REPLAY_VALIDATED_OFFLINE_ONLY" in report
    assert "Lot 30 remains `PLANNED_LOCKED`" in worklog

    for token in (
        "analysis_only=true",
        "used_for_decision=false",
        "trade_allowed=false",
        "execution_allowed=false",
        "approved_size=0",
    ):
        assert token in report
