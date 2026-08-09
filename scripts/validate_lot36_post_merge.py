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
EXPECTED_STATE_CHECKSUM = "635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592"
EXPECTED_AUDIT_CHECKSUM = "ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42"
EXPECTED_MANIFEST_CHECKSUM = "6a9935e728a93a23a3804106dc54aa216f4f9fedad3635b5507139f4ccbfc37f"
EXPECTED_REPLAY_CHECKSUM = "cef50b5191c1f3c78baaa3906c4c5ded59f1dd45dad0271a0071b7056b6af91d"
EXPECTED_VALIDATION_ARTIFACT_DIGEST = "sha256:3a8e53827df279b06837f447c941ef51b14672fb9b7c1d1fae9f8f55582d7a38"
EXPECTED_MUTATION_ARTIFACT_DIGEST = "sha256:5b44d075e13ae9569514914689a4427f5898835d475a4d8a351e0fcb626a41ef"
FAIL_CLOSED_FIELDS = (
    "external_connectivity_allowed", "network_ingestion_allowed",
    "real_credentials_allowed", "signal_generation_allowed",
    "risk_approval_allowed", "order_routing_allowed", "trade_allowed",
    "execution_allowed",
)


class Lot36PostMergeError(RuntimeError):
    """Raised when the independent Lot 36 V3 closure certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot36PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verified(path: str, checksum_field: str, expected: str) -> dict[str, Any]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(checksum_field, None)
    require(checksum == expected, f"{path} certified checksum changed")
    require(canonical_checksum(body) == checksum, f"{path} checksum mismatch")
    return payload


def validate_version() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["version"] == "0.36.0", "project version must be 0.36.0")
    require("Lot 36" in project["description"], "project description must identify Lot 36")


def validate_lifecycle() -> dict[str, Any]:
    previous = load("data/audit/roadmap_lifecycle_overlay_lot35.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    require(current["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot35.json", "Lot 36 lifecycle predecessor mismatch")
    require(current["latest_implemented_lot"] == 36, "latest implemented lot must be 36")
    for lot in range(26, 36):
        require(current["lots"][str(lot)] == previous["lots"][str(lot)], f"Lot {lot} lifecycle was rewritten")
    lot36 = current["lots"]["36"]
    require(lot36["status"] == "IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY", "Lot 36 lifecycle status mismatch")
    require(lot36["implementation_commit"] == IMPLEMENTATION_COMMIT, "implementation commit mismatch")
    require(lot36["evidence_commit"] == EVIDENCE_COMMIT, "evidence commit mismatch")
    require(lot36["exact_ci_commit"] == EXACT_CI_COMMIT, "exact CI commit mismatch")
    require(lot36["merged_commit"] == MERGED_COMMIT, "merged commit mismatch")
    require(lot36["pull_request"] == 34, "Lot 36 PR mismatch")
    require(lot36["runtime_mode"] == "DATA_GOVERNANCE_ONLY", "Lot 36 runtime mismatch")
    require(lot36["v3_closed"] is True, "V3 must be closed by post-merge audit")
    for field in ("trade_allowed", "execution_allowed", "external_connectivity_allowed", "network_ingestion_allowed", "raw_data_mutation_allowed"):
        require(lot36[field] is False, f"Lot 36 lifecycle permission enabled: {field}")
    require(current["lots"]["37"] == {"implementation_started": False, "status": "PLANNED_LOCKED"}, "Lot 37 must remain locked")
    return current


def validate_fail_closed(payload: dict[str, Any], label: str) -> None:
    require(payload["analysis_only"] is True, f"{label} analysis-only changed")
    require(payload["approved_size"] == 0, f"{label} approved size changed")
    for field in FAIL_CLOSED_FIELDS:
        require(payload[field] is False, f"{label} permission enabled: {field}")
    require(payload["raw_data_mutation_allowed"] is False, f"{label} raw mutation enabled")
    require(payload["market_event_publication_allowed"] is False, f"{label} market publication enabled")


def validate_certified_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    state = verified("data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json", "output_checksum", EXPECTED_STATE_CHECKSUM)
    audit = verified("data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json", "audit_checksum", EXPECTED_AUDIT_CHECKSUM)
    manifest = load("data/audit/closure_manifest_lot36.json")
    replay = load("data/audit/replay_evidence_lot36.json")
    quality_states = load("data/audit/data_quality_states_lot36.json")
    anomalies = load("data/audit/data_anomalies_lot36.json")
    quality_veto = load("data/audit/data_quality_veto_lot36.json")
    require(state["run_context"]["code_commit"] == IMPLEMENTATION_COMMIT, "state implementation commit changed")
    require(audit["code_commit"] == IMPLEMENTATION_COMMIT, "audit implementation commit changed")
    require(audit["state_output_checksum"] == EXPECTED_STATE_CHECKSUM, "state/audit mismatch")
    require(state["closure_manifest"] == manifest, "closure manifest artifact mismatch")
    require(manifest["manifest_checksum"] == EXPECTED_MANIFEST_CHECKSUM, "manifest checksum changed")
    manifest_body = dict(manifest)
    manifest_checksum = manifest_body.pop("manifest_checksum")
    require(canonical_checksum(manifest_body) == manifest_checksum, "manifest checksum mismatch")
    require(manifest["closure_status"] == "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT", "historical closure stage changed")
    require(manifest["v3_closed"] is False, "implementation manifest must remain historical candidate")
    require(manifest["next_lot"] == 37 and manifest["next_lot_status"] == "PLANNED_LOCKED", "implementation manifest Lot37 lock changed")
    require(replay["replay_checksum"] == EXPECTED_REPLAY_CHECKSUM, "replay checksum changed")
    replay_body = dict(replay)
    replay_checksum = replay_body.pop("replay_checksum")
    require(canonical_checksum(replay_body) == replay_checksum, "replay checksum mismatch")
    require(replay["replay_status"] == "REPLAY_MATCH" and replay["match"] is True, "deterministic replay changed")
    require(replay["run1_checksum"] == replay["run2_checksum"] == EXPECTED_STATE_CHECKSUM, "replay state checksum changed")
    require(quality_states["records"] == state["quality_states"], "quality-state collection mismatch")
    require(anomalies["records"] == state["anomalies"] == [], "anomaly collection changed")
    require(quality_veto == state["data_quality_veto"], "quality veto artifact mismatch")
    require(state["data_quality_veto"]["action"] == "ALLOW_ANALYSIS", "quality veto changed")
    require(state["reconciliation_veto"]["action"] == "ALLOW_ANALYSIS", "reconciliation veto changed")
    require(state["validation_state"] == "VALIDATED_V3_CLOSURE_CANDIDATE", "state validation changed")
    require(audit["validation_state"] == "VALIDATED_V3_CLOSURE_CANDIDATE", "audit validation changed")
    metrics = state["metrics"]
    expected = {
        "lot_36_records_processed_total": 3,
        "lot_36_validation_failures_total": 0,
        "lot_36_gap_total": 0,
        "lot_36_outage_total": 0,
        "lot_36_stale_record_total": 0,
        "lot_36_anomaly_total": 0,
        "lot_36_processing_latency_us": 50000,
    }
    for field, value in expected.items():
        require(metrics[field] == value, f"Lot 36 metric changed: {field}")
    freshness = state["freshness_audits"]
    require(len(freshness) == 1, "freshness audit count changed")
    require(freshness[0]["status"] == "PASS", "freshness status changed")
    require(freshness[0]["freshness_bps"] == 10000, "freshness score changed")
    validate_fail_closed(state, "Lot 36 state")
    validate_fail_closed(audit, "Lot 36 audit")
    return state, audit


def validate_coverage_evidence() -> dict[str, Any]:
    coverage = load("reports/lot36/coverage_summary.json")
    require(coverage["status"] == "PASS", "coverage evidence is not PASS")
    require(coverage["source_commit"] == IMPLEMENTATION_COMMIT, "coverage source commit changed")
    require(coverage["workflow_run_id"] == 31308763595, "coverage workflow run changed")
    require(coverage["artifact_id"] == 9036759073, "coverage artifact id changed")
    require(coverage["artifact_digest"] == EXPECTED_VALIDATION_ARTIFACT_DIGEST, "coverage digest changed")
    require(coverage["line_coverage_percent"] == 100.0 and coverage["covered_lines"] == coverage["total_lines"] == 552, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 100.0 and coverage["covered_branches"] == coverage["total_branches"] == 136, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below gate")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below gate")
    return coverage


def validate_mutation_evidence() -> dict[str, Any]:
    mutation = load("reports/lot36/mutation_summary.json")
    require(mutation["status"] == "PASS", "mutation evidence is not PASS")
    require(mutation["source_head_sha"] == IMPLEMENTATION_COMMIT, "mutation source commit changed")
    require(mutation["workflow_run_id"] == 31308763592, "mutation workflow run changed")
    require(mutation["artifact_id"] == 9036765419, "mutation artifact id changed")
    require(mutation["artifact_digest"] == EXPECTED_MUTATION_ARTIFACT_DIGEST, "mutation digest changed")
    require(mutation["mutation_score_percent"] == 83.48, "mutation score changed")
    require(mutation["killed_mutants"] == 1289, "killed-mutant evidence changed")
    require(mutation["evaluated_mutants"] == 1544, "evaluated-mutant evidence changed")
    require(mutation["survived_mutants"] == 255, "survived-mutant evidence changed")
    require(mutation["timeout_mutants"] == 0 and mutation["suspicious_mutants"] == 0, "mutation terminal states changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below gate")
    return mutation


def validate_documents() -> None:
    audit_doc = (ROOT / "docs/LOT_36_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/LOT36_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")
    for text in (audit_doc, matrix):
        for commit in (IMPLEMENTATION_COMMIT, EVIDENCE_COMMIT, EXACT_CI_COMMIT, MERGED_COMMIT):
  require(commit in text, "audit document missing exact lineage commit")
    require("GO_LOT36_POST_MERGE_V3_CLOSED" in audit_doc, "audit verdict missing")
    require("0.36.0" in readme and "Lot 36" in readme, "README release state is not Lot 36 / 0.36.0")
    require("IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY" in roadmap, "roadmap Lot 36 status missing")
    require("Lot 37" in roadmap and "PLANNED_LOCKED" in roadmap, "roadmap Lot 37 lock missing")


def validate() -> dict[str, Any]:
    validate_version()
    lifecycle = validate_lifecycle()
    state, audit = validate_certified_evidence()
    coverage = validate_coverage_evidence()
    mutation = validate_mutation_evidence()
    validate_documents()
    result = {
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
        "manifest_checksum": EXPECTED_MANIFEST_CHECKSUM,
        "replay_checksum": EXPECTED_REPLAY_CHECKSUM,
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
    except (Lot36PostMergeError, OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT36 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
