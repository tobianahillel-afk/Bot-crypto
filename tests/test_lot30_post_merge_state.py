from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGED_IMPLEMENTATION_COMMIT = "4551f4973ce535a6f2733ea4d92833d84ae298f7"
IMPLEMENTATION_EVIDENCE_COMMIT = "602bc91b2d4c886f654840294fa740474515e0a0"
EXPECTED_FINAL_CHAIN_CHECKSUM = (
    "2a598990adaec7ebc1368f30295a0130d4d8bd8f89c9610772347f25ba6c17cf"
)


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


def test_lot30_post_merge_release_and_lifecycle_are_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = load_json("data/audit/roadmap_lifecycle_overlay_lot30.json")

    assert project["version"] == "0.30.0"
    assert project["description"].endswith("Lot 30 validated V2 market-analysis closure")
    assert overlay["latest_implemented_lot"] == 30
    assert overlay["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot29.json"
    lots = overlay["lots"]
    assert isinstance(lots, dict)
    assert lots["30"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY"
    assert lots["30"]["implementation_commit"] == IMPLEMENTATION_EVIDENCE_COMMIT
    assert lots["30"]["merged_commit"] == MERGED_IMPLEMENTATION_COMMIT
    assert lots["30"]["pull_request"] == 15
    assert lots["30"]["trade_allowed"] is False
    assert lots["30"]["execution_allowed"] is False
    assert lots["31"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot30_post_merge_evidence_is_independently_linked() -> None:
    state = load_json("data/audit/v2_market_analysis_closure_lot30.json")
    audit = load_json("data/audit/v2_market_analysis_closure_audit_lot30.json")
    manifest = load_json("data/audit/closure_manifest_lot30.json")

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert isinstance(output_checksum, str)
    assert canonical_checksum(payload) == output_checksum
    assert audit["output_checksum"] == output_checksum
    assert state["closure_manifest"] == manifest
    assert audit["final_chain_checksum"] == EXPECTED_FINAL_CHAIN_CHECKSUM
    assert manifest["final_chain_checksum"] == EXPECTED_FINAL_CHAIN_CHECKSUM
    assert manifest["covered_lot_sequence"] == list(range(21, 31))
    assert manifest["upstream_lot_sequence"] == list(range(21, 29))
    assert manifest["direct_validated_lot"] == 29
    assert manifest["closure_lot"] == 30
    assert manifest["negative_control_count"] == 5
    assert len(manifest["upstream_artifact_checksums"]) == 8
    assert [item["run_index"] for item in state["validator_replays"]] == [1, 2]
    assert state["validator_replays"][0]["stdout_checksum"] == (
        state["validator_replays"][1]["stdout_checksum"]
    )


def test_lot30_post_merge_safety_and_verdict_remain_fail_closed() -> None:
    state = load_json("data/audit/v2_market_analysis_closure_lot30.json")
    audit = load_json("data/audit/v2_market_analysis_closure_audit_lot30.json")
    post_merge = (ROOT / "docs/LOT_30_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for document in (state, audit):
        assert document["analysis_only"] is True
        assert document["used_for_decision"] is False
        assert document["signal_generation_allowed"] is False
        assert document["risk_approval_allowed"] is False
        assert document["order_routing_allowed"] is False
        assert document["trade_allowed"] is False
        assert document["execution_allowed"] is False
        assert document["approved_size"] == 0

    assert "GO_LOT30_POST_MERGE_AUDIT" in post_merge
    assert "Lot 31 remains `PLANNED_LOCKED`" in post_merge
    assert "Dernier lot dont l'implémentation est terminée : **Lot 30**" in roadmap
    assert "Dernier lot implémenté et validé | **Lot 30" in readme
    assert "Lot 31 — Market Data Source Registry" in readme
