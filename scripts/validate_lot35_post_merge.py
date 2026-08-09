#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MERGED_COMMIT = "d083d4f27c89759ebed37b2ecacccbe88dccad11"
IMPLEMENTATION_COMMIT = "a4501bb0d400c6c1b5cf970fc5aa6456ad8c6ea8"
EVIDENCE_COMMIT = "09701c7d5ebefbeba41143a2838564b09ea5fb3a"
EXPECTED_STATE_CHECKSUM = "8fc7243beffdf985fd6947557b87ab7bd27f9191520eb2d5d9af25d1e7a886b4"
EXPECTED_AUDIT_CHECKSUM = "98a88396f5b2e5ffc1cde02435399540ad213f5ec361b33e8a19c08b0fedf1de"
EXPECTED_VALIDATION_ARTIFACT_DIGEST = (
    "sha256:64584097fe4d2136e497149ad6473ff8c9a6ce58ca7eb375187cd8ac5aa4c781"
)
EXPECTED_MUTATION_ARTIFACT_DIGEST = (
    "sha256:36a80853e7d3c3bbd4b0255e063ae4ecfe6314b82249f24eb736f8e1dc03bbfc"
)
FAIL_CLOSED_FIELDS = (
    "external_connectivity_allowed",
    "network_ingestion_allowed",
    "real_credentials_allowed",
    "signal_generation_allowed",
    "risk_approval_allowed",
    "order_routing_allowed",
    "trade_allowed",
    "execution_allowed",
)


class Lot35PostMergeError(RuntimeError):
    """Raised when the independent Lot 35 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot35PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
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
    require(project["version"] == "0.35.0", "project version must be 0.35.0")
    require("Lot 35" in project["description"], "project description must identify Lot 35")


def validate_lifecycle() -> dict[str, Any]:
    previous = load("data/audit/roadmap_lifecycle_overlay_lot34.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot35.json")
    require(
        current["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot34.json",
        "Lot 35 lifecycle predecessor mismatch",
    )
    require(current["latest_implemented_lot"] == 35, "latest implemented lot must be 35")
    for lot in range(26, 35):
        require(
            current["lots"][str(lot)] == previous["lots"][str(lot)],
            f"Lot {lot} lifecycle was rewritten",
        )
    validate_lot35_lifecycle_entry(current["lots"]["35"])
    require(
        current["lots"]["36"] == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 36 must remain locked",
    )
    return current


def validate_lot35_lifecycle_entry(lot35: dict[str, Any]) -> None:
    require(
        lot35["status"] == "IMPLEMENTED_VALIDATED_RECONCILIATION_ONLY",
        "Lot 35 lifecycle status mismatch",
    )
    require(lot35["implementation_commit"] == IMPLEMENTATION_COMMIT, "implementation commit mismatch")
    require(lot35["merged_commit"] == MERGED_COMMIT, "merged commit mismatch")
    require(lot35["pull_request"] == 31, "Lot 35 PR mismatch")
    require(lot35["runtime_mode"] == "DATA_GOVERNANCE_ONLY", "Lot 35 runtime mismatch")
    for field in (
        "trade_allowed",
        "execution_allowed",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "raw_data_mutation_allowed",
    ):
        require(lot35[field] is False, f"Lot 35 lifecycle permission enabled: {field}")


def validate_fail_closed(payload: dict[str, Any], label: str) -> None:
    require(payload["analysis_only"] is True, f"{label} analysis-only changed")
    require(payload["approved_size"] == 0, f"{label} approved size changed")
    for field in FAIL_CLOSED_FIELDS:
        require(payload[field] is False, f"{label} permission enabled: {field}")


def validate_certified_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    state = verified(
        "data/audit/candle_trade_book_reconciliation_lot35.json",
        "output_checksum",
        EXPECTED_STATE_CHECKSUM,
    )
    audit = verified(
        "data/audit/candle_trade_book_reconciliation_audit_lot35.json",
        "audit_checksum",
        EXPECTED_AUDIT_CHECKSUM,
    )
    require(state["run_context"]["code_commit"] == IMPLEMENTATION_COMMIT, "state code commit changed")
    require(audit["code_commit"] == IMPLEMENTATION_COMMIT, "audit code commit changed")
    require(audit["state_output_checksum"] == EXPECTED_STATE_CHECKSUM, "state/audit mismatch")
    require(state["validation_state"] == "VALIDATED_RECONCILIATION_ONLY", "state validation changed")
    require(audit["validation_state"] == "VALIDATED_RECONCILIATION_ONLY", "audit validation changed")
    validate_collections(state)
    validate_reference_metrics(state)
    validate_fail_closed(state, "Lot 35 state")
    validate_fail_closed(audit, "Lot 35 audit")
    return state, audit


def validate_collections(state: dict[str, Any]) -> None:
    reports = load("data/audit/reconciliation_reports_lot35.json")
    veto = load("data/audit/reconciliation_veto_lot35.json")
    require(reports["records"] == state["reports"], "report collection mismatch")
    require(veto == state["veto"], "veto artifact mismatch")


def validate_reference_metrics(state: dict[str, Any]) -> None:
    metrics = state["metrics"]
    expected = {
        "lot_35_records_processed_total": 3,
        "lot_35_match_total": 2,
        "lot_35_tolerated_diff_total": 1,
        "lot_35_minor_divergence_total": 0,
        "lot_35_critical_divergence_total": 0,
        "lot_35_validation_failures_total": 0,
    }
    for field, value in expected.items():
        require(metrics[field] == value, f"Lot 35 metric changed: {field}")
    require(state["veto"]["action"] == "ALLOW_ANALYSIS", "reference veto changed")


def validate_coverage_evidence() -> dict[str, Any]:
    coverage = load("reports/lot35/coverage_summary.json")
    require(coverage["status"] == "PASS", "coverage evidence is not PASS")
    require(coverage["evidence_commit"] == EVIDENCE_COMMIT, "coverage evidence commit changed")
    require(coverage["workflow_run_id"] == 31284931048, "coverage workflow run changed")
    require(coverage["artifact_id"] == 9029508289, "coverage artifact id changed")
    require(coverage["artifact_digest"] == EXPECTED_VALIDATION_ARTIFACT_DIGEST, "coverage digest changed")
    require(coverage["line_coverage_percent"] == 96.43, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 93.75, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below gate")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below gate")
    return coverage


def validate_mutation_evidence() -> dict[str, Any]:
    mutation = load("reports/lot35/mutation_summary.json")
    require(mutation["status"] == "PASS", "mutation evidence is not PASS")
    require(mutation["evidence_commit"] == EVIDENCE_COMMIT, "mutation evidence commit changed")
    require(mutation["workflow_run_id"] == 31284931041, "mutation workflow run changed")
    require(mutation["artifact_id"] == 9029508744, "mutation artifact id changed")
    require(mutation["artifact_digest"] == EXPECTED_MUTATION_ARTIFACT_DIGEST, "mutation digest changed")
    require(mutation["mutation_score_percent"] == 83.73, "mutation score changed")
    require(mutation["killed_mutants"] == 1029, "killed-mutant evidence changed")
    require(mutation["evaluated_mutants"] == 1229, "evaluated-mutant evidence changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below gate")
    return mutation


def validate_documents() -> None:
    audit_doc = (ROOT / "docs/LOT_35_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/LOT35_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")
    for text in (audit_doc, matrix):
        require(MERGED_COMMIT in text, "audit document missing exact merge commit")
        require(EVIDENCE_COMMIT in text, "audit document missing evidence commit")
    require("GO_LOT35_POST_MERGE" in audit_doc, "audit verdict missing")
    require("0.35.0" in readme, "README release version is not 0.35.0")
    require("Lot 35" in readme, "README current lot missing")
    require("Lot 36" in roadmap and "PLANNED_LOCKED" in roadmap, "roadmap Lot 36 lock missing")


def validate() -> dict[str, Any]:
    validate_version()
    lifecycle = validate_lifecycle()
    state, audit = validate_certified_evidence()
    coverage = validate_coverage_evidence()
    mutation = validate_mutation_evidence()
    validate_documents()
    result = {
        "schema_version": "lot35-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT35_POST_MERGE",
        "project_version": "0.35.0",
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "merged_commit": MERGED_COMMIT,
        "evidence_commit": EVIDENCE_COMMIT,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 36,
        "next_lot_status": lifecycle["lots"]["36"]["status"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot35PostMergeError, OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT35 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
