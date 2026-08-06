from __future__ import annotations

import json
from pathlib import Path

from crypto_quant_bot.market_analysis.v2_market_analysis_closure import canonical_checksum

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FINAL_CHAIN_CHECKSUM = (
    "2a598990adaec7ebc1368f30295a0130d4d8bd8f89c9610772347f25ba6c17cf"
)
EXPECTED_REASON_CODES = [
    "V2_LOTS_21_30_COVERED",
    "V2_REPLAY_CHAIN_MATCH",
    "V2_NEGATIVE_CONTROLS_PASS",
    "V3_CAPABILITIES_LOCKED",
    "V2_OFFLINE_ONLY",
]
EXPECTED_NEGATIVE_CONTROLS = [
    "SCHEMA_MISMATCH_REJECTED",
    "UPSTREAM_CHECKSUM_TAMPER_REJECTED",
    "FORBIDDEN_CAPABILITY_REJECTED",
    "VALIDATOR_DIVERGENCE_REJECTED",
    "LIFECYCLE_UNLOCK_REJECTED",
]
EXPECTED_FUTURE_LOCKS = [
    "ContinuousMarketStateV1",
    "MultiHorizonForecastV1",
    "ParticipantBehaviorScenarioV1",
    "TradeIntent",
    "RiskDecisionV1",
    "RiskReservationV1",
    "OrderIntent",
]


def load_json(relative: str) -> dict[str, object]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot30_release_evidence_is_linked_and_deterministic() -> None:
    state = load_json("data/audit/v2_market_analysis_closure_lot30.json")
    audit = load_json("data/audit/v2_market_analysis_closure_audit_lot30.json")
    manifest = load_json("data/audit/closure_manifest_lot30.json")

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert isinstance(output_checksum, str)
    assert canonical_checksum(payload) == output_checksum

    code_commit = state["code_commit"]
    assert isinstance(code_commit, str)
    assert len(code_commit) == 40
    assert all(character in "0123456789abcdef" for character in code_commit)
    assert audit["code_commit"] == code_commit
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
    assert state["reason_codes"] == EXPECTED_REASON_CODES
    assert audit["reason_codes"] == EXPECTED_REASON_CODES
    assert [item["name"] for item in state["negative_controls"]] == EXPECTED_NEGATIVE_CONTROLS
    assert state["future_capabilities_locked"] == EXPECTED_FUTURE_LOCKS


def test_lot30_release_evidence_remains_fail_closed() -> None:
    state = load_json("data/audit/v2_market_analysis_closure_lot30.json")
    audit = load_json("data/audit/v2_market_analysis_closure_audit_lot30.json")

    for document in (state, audit):
        assert document["analysis_only"] is True
        assert document["used_for_decision"] is False
        assert document["signal_generation_allowed"] is False
        assert document["risk_approval_allowed"] is False
        assert document["order_routing_allowed"] is False
        assert document["trade_allowed"] is False
        assert document["execution_allowed"] is False
        assert document["approved_size"] == 0


def test_lot30_certified_quality_evidence_exceeds_gates() -> None:
    coverage = load_json("reports/lot30/coverage_summary.json")
    mutation = load_json("reports/lot30/mutation/score.json")

    assert coverage == {
        "branch_coverage_percent": 95.27,
        "covered_branches": 141,
        "covered_lines": 379,
        "line_coverage_percent": 97.93,
        "minimum_branch_coverage_percent": 90.0,
        "minimum_line_coverage_percent": 95.0,
        "missing_branches": 7,
        "missing_lines": 8,
        "num_branches": 148,
        "num_statements": 387,
        "schema_version": "lot30-critical-coverage-summary-v1",
        "status": "PASS",
    }
    assert mutation["schema_version"] == "lot30-critical-mutation-score-v1"
    assert mutation["scope"] == "v2_market_analysis_closure"
    assert mutation["completed"] == 1152
    assert mutation["evaluated"] == 1152
    assert mutation["killed"] == 991
    assert mutation["survived"] == 161
    assert mutation["timeout"] == 0
    assert mutation["suspicious"] == 0
    assert mutation["score_percent"] == 86.02
    assert mutation["minimum_score_percent"] == 80.0
    assert mutation["status"] == "PASS"


def test_lot30_documents_certify_only_offline_closure() -> None:
    specification = (ROOT / "docs/LOT_30_V2_MARKET_ANALYSIS_CLOSURE.md").read_text(
        encoding="utf-8"
    )
    worklog = (ROOT / "docs/LOT_30_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")
    report = (ROOT / "reports/lot_30_v2_market_analysis_closure_report.md").read_text(
        encoding="utf-8"
    )

    assert "IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY" in specification
    assert "IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY" in worklog
    assert "602bc91b2d4c886f654840294fa740474515e0a0" in worklog
    assert "97.93%" in worklog
    assert "95.27%" in worklog
    assert "86.02%" in worklog
    assert "GO_LOT30_V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY" in report
    assert "Lot 31 remains `PLANNED_LOCKED`" in report
