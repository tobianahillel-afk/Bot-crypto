#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MERGED_COMMIT = "87da195283797247505e4fc650214e33e759e21a"
IMPLEMENTATION_COMMIT = "c21b8f242270bd87eebbf7279635ab8bb51b8666"
EVIDENCE_COMMIT = "b3680f5da0a3fd98fdedc31599c829dc60808290"
EXACT_CI_COMMIT = "16f3454c6f912f3f00f79836950047b15687abce"
STATE_CHECKSUM = "635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592"
AUDIT_CHECKSUM = "ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42"
MANIFEST_CHECKSUM = "6a9935e728a93a23a3804106dc54aa216f4f9fedad3635b5507139f4ccbfc37f"
REPLAY_CHECKSUM = "cef50b5191c1f3c78baaa3906c4c5ded59f1dd45dad0271a0071b7056b6af91d"
VALIDATION_DIGEST = "sha256:3a8e53827df279b06837f447c941ef51b14672fb9b7c1d1fae9f8f55582d7a38"
MUTATION_DIGEST = "sha256:5b44d075e13ae9569514914689a4427f5898835d475a4d8a351e0fcb626a41ef"
FAIL_CLOSED = (
    "external_connectivity_allowed",
    "network_ingestion_allowed",
    "real_credentials_allowed",
    "signal_generation_allowed",
    "risk_approval_allowed",
    "order_routing_allowed",
    "trade_allowed",
    "execution_allowed",
    "raw_data_mutation_allowed",
    "market_event_publication_allowed",
)


class Lot36PostMergeError(RuntimeError):
    """Raised when independent Lot 36 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot36PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_checksum(
    path: str, checksum_field: str, expected: str
) -> dict[str, Any]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(checksum_field, None)
    require(checksum == expected, f"{path}: certified checksum changed")
    require(canonical_checksum(body) == checksum, f"{path}: checksum mismatch")
    return payload


def validate_version_and_lifecycle() -> dict[str, Any]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["version"] == "0.36.0", "project version must be 0.36.0")
    require("Lot 36" in project["description"], "project description must identify Lot 36")

    previous = load("data/audit/roadmap_lifecycle_overlay_lot35.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    require(
        current["previous_overlay"]
        == "data/audit/roadmap_lifecycle_overlay_lot35.json",
        "Lot 36 lifecycle predecessor mismatch",
    )
    require(current["latest_implemented_lot"] == 36, "latest implemented lot must be 36")
    for lot in range(26, 36):
        require(
            current["lots"][str(lot)] == previous["lots"][str(lot)],
            f"Lot {lot} lifecycle was rewritten",
        )

    lot36 = current["lots"]["36"]
    expected_lineage = {
        "status": "IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY",
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "evidence_commit": EVIDENCE_COMMIT,
        "exact_ci_commit": EXACT_CI_COMMIT,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 34,
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "v3_closed": True,
    }
    for field, expected in expected_lineage.items():
        require(lot36.get(field) == expected, f"Lot 36 lifecycle mismatch: {field}")
    for field in (
        "trade_allowed",
        "execution_allowed",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "raw_data_mutation_allowed",
    ):
        require(lot36.get(field) is False, f"Lot 36 permission enabled: {field}")
    require(
        current["lots"]["37"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 37 must remain exactly locked",
    )
    return current


def validate_fail_closed(payload: dict[str, Any], label: str) -> None:
    require(payload.get("analysis_only") is True, f"{label}: analysis_only changed")
    require(payload.get("approved_size") == 0, f"{label}: approved_size changed")
    for field in FAIL_CLOSED:
        require(payload.get(field) is False, f"{label}: permission enabled: {field}")


def validate_certified_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    state = verify_checksum(
        "data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json",
        "output_checksum",
        STATE_CHECKSUM,
    )
    audit = verify_checksum(
        "data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json",
        "audit_checksum",
        AUDIT_CHECKSUM,
    )
    manifest = load("data/audit/closure_manifest_lot36.json")
    replay = load("data/audit/replay_evidence_lot36.json")
    quality_states = load("data/audit/data_quality_states_lot36.json")
    anomalies = load("data/audit/data_anomalies_lot36.json")
    quality_veto = load("data/audit/data_quality_veto_lot36.json")

    require(state["run_context"]["code_commit"] == IMPLEMENTATION_COMMIT, "state code commit changed")
    require(audit["code_commit"] == IMPLEMENTATION_COMMIT, "audit code commit changed")
    require(audit["state_output_checksum"] == STATE_CHECKSUM, "state/audit link changed")
    require(state["closure_manifest"] == manifest, "manifest artifact differs from state")

    manifest_body = dict(manifest)
    manifest_value = manifest_body.pop("manifest_checksum", None)
    require(manifest_value == MANIFEST_CHECKSUM, "manifest certified checksum changed")
    require(canonical_checksum(manifest_body) == manifest_value, "manifest checksum mismatch")
    require(
        manifest["closure_status"] == "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT",
        "historical implementation closure stage changed",
    )
    require(manifest["v3_closed"] is False, "historical candidate manifest was rewritten")
    require(manifest["next_lot"] == 37, "historical manifest next lot changed")
    require(manifest["next_lot_status"] == "PLANNED_LOCKED", "historical Lot 37 lock changed")

    replay_body = dict(replay)
    replay_value = replay_body.pop("replay_checksum", None)
    require(replay_value == REPLAY_CHECKSUM, "replay certified checksum changed")
    require(canonical_checksum(replay_body) == replay_value, "replay checksum mismatch")
    require(replay["replay_status"] == "REPLAY_MATCH", "replay status changed")
    require(replay["match"] is True, "replay match changed")
    require(replay["run1_checksum"] == STATE_CHECKSUM, "replay run1 checksum changed")
    require(replay["run2_checksum"] == STATE_CHECKSUM, "replay run2 checksum changed")

    require(quality_states["records"] == state["quality_states"], "quality states changed")
    require(anomalies["records"] == state["anomalies"] == [], "anomaly collection changed")
    require(quality_veto == state["data_quality_veto"], "quality veto artifact changed")
    require(state["data_quality_veto"]["action"] == "ALLOW_ANALYSIS", "quality veto changed")
    require(state["reconciliation_veto"]["action"] == "ALLOW_ANALYSIS", "reconciliation veto changed")
    require(state["validation_state"] == "VALIDATED_V3_CLOSURE_CANDIDATE", "state validation changed")
    require(audit["validation_state"] == "VALIDATED_V3_CLOSURE_CANDIDATE", "audit validation changed")

    expected_metrics = {
        "lot_36_records_processed_total": 3,
        "lot_36_validation_failures_total": 0,
        "lot_36_gap_total": 0,
        "lot_36_outage_total": 0,
        "lot_36_stale_record_total": 0,
        "lot_36_anomaly_total": 0,
        "lot_36_processing_latency_us": 50000,
    }
    for field, expected in expected_metrics.items():
        require(state["metrics"].get(field) == expected, f"Lot 36 metric changed: {field}")
    require(len(state["freshness_audits"]) == 1, "freshness audit count changed")
    freshness = state["freshness_audits"][0]
    require(freshness["status"] == "PASS", "freshness audit changed")
    require(freshness["freshness_bps"] == 10000, "freshness score changed")

    validate_fail_closed(state, "Lot 36 state")
    validate_fail_closed(audit, "Lot 36 audit")
    return state, audit


def validate_quality_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load("reports/lot36/coverage_summary.json")
    mutation = load("reports/lot36/mutation_summary.json")
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_commit"] == IMPLEMENTATION_COMMIT, "coverage source changed")
    require(coverage["workflow_run_id"] == 31308763595, "coverage run changed")
    require(coverage["artifact_id"] == 9036759073, "coverage artifact changed")
    require(coverage["artifact_digest"] == VALIDATION_DIGEST, "coverage digest changed")
    require(coverage["line_coverage_percent"] == 100.0, "line coverage changed")
    require(coverage["covered_lines"] == coverage["total_lines"] == 552, "line counts changed")
    require(coverage["branch_coverage_percent"] == 100.0, "branch coverage changed")
    require(coverage["covered_branches"] == coverage["total_branches"] == 136, "branch counts changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below gate")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below gate")

    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == IMPLEMENTATION_COMMIT, "mutation source changed")
    require(mutation["workflow_run_id"] == 31308763592, "mutation run changed")
    require(mutation["artifact_id"] == 9036765419, "mutation artifact changed")
    require(mutation["artifact_digest"] == MUTATION_DIGEST, "mutation digest changed")
    require(mutation["mutation_score_percent"] == 83.48, "mutation score changed")
    require(mutation["killed_mutants"] == 1289, "killed mutants changed")
    require(mutation["evaluated_mutants"] == 1544, "evaluated mutants changed")
    require(mutation["survived_mutants"] == 255, "survived mutants changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutant count changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below gate")
    return coverage, mutation


def validate_documents() -> None:
    audit_doc = (ROOT / "docs/LOT_36_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/LOT36_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")
    for text in (audit_doc, matrix):
        for commit in (IMPLEMENTATION_COMMIT, EVIDENCE_COMMIT, EXACT_CI_COMMIT, MERGED_COMMIT):
            require(commit in text, "audit document missing exact lineage commit")
    require("GO_LOT36_POST_MERGE_V3_CLOSED" in audit_doc, "audit verdict missing")
    require("0.36.0" in readme and "Lot 36" in readme, "README release state mismatch")
    require("IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY" in roadmap, "roadmap Lot 36 status missing")
    require("Lot 37" in roadmap and "PLANNED_LOCKED" in roadmap, "roadmap Lot 37 lock missing")


def validate() -> dict[str, Any]:
    lifecycle = validate_version_and_lifecycle()
    state, audit = validate_certified_artifacts()
    coverage, mutation = validate_quality_evidence()
    validate_documents()
    result: dict[str, Any] = {
        "schema_version": "lot36-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT36_POST_MERGE_V3_CLOSED",
        "project_version": "0.36.0",
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "evidence_commit": EVIDENCE_COMMIT,
        "exact_ci_commit": EXACT_CI_COMMIT,
        "merged_commit": MERGED_COMMIT,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "manifest_checksum": MANIFEST_CHECKSUM,
        "replay_checksum": REPLAY_CHECKSUM,
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "v3_closed": True,
        "next_lot": 37,
        "next_lot_status": lifecycle["lots"]["37"]["status"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot36PostMergeError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT36 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
