#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "b74bea4329d5e5cb7cf2452058b684ea5a5df13c"
EVIDENCE_HEAD = "ef197437d13012644e48a9044cf0883bd17700fb"
MERGED_COMMIT = "e4b44d27886ade86f9d1d05d480b89010b03700d"
STATE_CHECKSUM = "7610fc6ea73e49075a1b8611f8344c7b9c8fcf8ab02f55612d914eeac0ccda9b"
AUDIT_CHECKSUM = "0290637591e1a8c4cd7a9975868932b65afa28fb75d6843340dbeea67a682d20"
SNAPSHOT_CHECKSUM = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
HEALTH_CHECKSUM = "58b56f7cf21aa74dd67620b8dd6e19cad11b77412cdcc3103b6d60bd15703837"
CONFIG_CHECKSUM = "60899c1393e111315395dd0e149f3a468972e9e99ca5a1322b8a97ec786497db"
FIXTURE_SHA256 = "f3715a14e8f04395b9ca5b514ac01ff8fcf924b82812f3388fdf500d6ecf5ece"
VALIDATION_RUN = 31340658957
VALIDATION_ARTIFACT = 9045722209
VALIDATION_DIGEST = "sha256:6a37b268ceb2a544d65ccc018b676f7c9627cd4aaebac493422e0a29338ee498"
MUTATION_RUN = 31340658949
MUTATION_ARTIFACT = 9045730814
MUTATION_DIGEST = "sha256:d01f7a68fcf6598a4073659f126cb9b526f03e54e2f57c41a6308be9d535aa8b"


class Lot38PostMergeError(RuntimeError):
    """Raised when the independent Lot 38 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot38PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def verify_checksum(path: str, field: str, expected: str) -> dict[str, Any]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(field, None)
    require(checksum == expected, f"{path}: certified checksum changed")
    require(canonical_checksum(body) == checksum, f"{path}: checksum mismatch")
    return payload


def validate_version_and_lifecycle() -> dict[str, Any]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]
    try:
        version_tuple = tuple(int(part) for part in version.split("."))
    except (AttributeError, ValueError) as exc:
        raise Lot38PostMergeError("project version must be numeric semver") from exc
    require(len(version_tuple) == 3, "project version must be numeric semver")
    require(version_tuple >= (0, 38, 0), "project version cannot precede audited Lot 38")

    previous = load("data/audit/roadmap_lifecycle_overlay_lot37.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot38.json")
    require(
        current["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot37.json",
        "Lot 38 lifecycle predecessor mismatch",
    )
    require(current["latest_implemented_lot"] == 38, "latest implemented lot must be 38")
    for lot in range(26, 38):
        require(
            current["lots"][str(lot)] == previous["lots"][str(lot)],
            f"Lot {lot} lifecycle was rewritten",
        )

    lot38 = current["lots"]["38"]
    expected = {
        "status": "IMPLEMENTED_VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY",
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 41,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected.items():
        require(lot38.get(field) == value, f"Lot 38 lifecycle mismatch: {field}")
    require(lot38.get("analysis_only") is True, "Lot 38 analysis_only changed")
    require(
        lot38.get("participant_behavior_inference_explicitly_labeled") is True,
        "Lot 38 participant-inference labeling changed",
    )
    for field in (
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "market_event_publication_allowed",
        "raw_data_mutation_allowed",
        "scenario_score_is_signal",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
        require(lot38.get(field) is False, f"Lot 38 permission enabled: {field}")
    require(
        current["lots"]["39"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 39 must remain exactly locked",
    )
    return current


def validate_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = verify_checksum(
        "data/audit/order_book_l2_snapshot_engine_lot38.json",
        "output_checksum",
        STATE_CHECKSUM,
    )
    audit = verify_checksum(
        "data/audit/order_book_l2_snapshot_engine_audit_lot38.json",
        "audit_checksum",
        AUDIT_CHECKSUM,
    )
    snapshot = verify_checksum(
        "data/audit/order_book_snapshot_lot38.json",
        "snapshot_checksum",
        SNAPSHOT_CHECKSUM,
    )
    health = verify_checksum(
        "data/audit/book_health_state_lot38.json",
        "health_checksum",
        HEALTH_CHECKSUM,
    )

    require(state["snapshot"] == snapshot, "Lot 38 state/snapshot mismatch")
    require(state["book_health"] == health, "Lot 38 state/health mismatch")
    require(audit["state_output_checksum"] == STATE_CHECKSUM, "state/audit link changed")
    require(audit["snapshot_checksum"] == SNAPSHOT_CHECKSUM, "snapshot/audit link changed")
    require(audit["health_checksum"] == HEALTH_CHECKSUM, "health/audit link changed")
    require(audit["config_checksum"] == CONFIG_CHECKSUM, "config checksum changed")
    require(file_sha256("config/microstructure/order_book_l2_snapshot_engine_v1.json") == CONFIG_CHECKSUM, "config file changed")
    require(file_sha256("tests/fixtures/lot37/offline_l2_availability_fixture_v1.json") == FIXTURE_SHA256, "Lot 37 input fixture changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["validation_state"] == "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY", "state changed")
    require(audit["validation_state"] == "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY", "audit changed")

    expected_bids = [
        {"price": "50024.9", "quantity": "0.8"},
        {"price": "50024.8", "quantity": "1.25"},
    ]
    expected_asks = [
        {"price": "50025.1", "quantity": "0.7"},
        {"price": "50025.2", "quantity": "1.1"},
    ]
    require(snapshot["bids"] == expected_bids, "reference bids changed")
    require(snapshot["asks"] == expected_asks, "reference asks changed")
    require(snapshot["source_bid_depth"] == 3, "source bid depth changed")
    require(snapshot["source_ask_depth"] == 3, "source ask depth changed")
    require(snapshot["published_bid_depth"] == 2, "published bid depth changed")
    require(snapshot["published_ask_depth"] == 2, "published ask depth changed")
    require(snapshot["sequence_id"] == 1001, "sequence id changed")
    require(
        snapshot["sequence_anchor"]
        == "9d5b399044b6fcdbacd6e30e4a7c975638c039cf1afb6d5c7df3ee5515c6aa24",
        "sequence anchor changed",
    )
    require(health["health_status"] == "HEALTHY", "health status changed")
    require(health["crossed"] is False, "reference book crossed")
    require(health["locked"] is False, "reference book unexpectedly locked")
    require(health["sequence_present"] is True, "sequence presence changed")

    require(state["safety"] == audit["safety"], "state/audit safety mismatch")
    safety = state["safety"]
    require(safety["analysis_only"] is True, "analysis-only boundary changed")
    require(safety["approved_size"] == 0, "approved_size changed")
    require(
        safety["participant_behavior_inference_explicitly_labeled"] is True,
        "participant inference labeling changed",
    )
    for field in (
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "market_event_publication_allowed",
        "raw_data_mutation_allowed",
        "scenario_score_is_signal",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
        require(safety[field] is False, f"Lot 38 state permission enabled: {field}")
    require("LOT39_REMAINS_LOCKED" in state["reason_codes"], "Lot 39 lock reason missing")
    return state, audit, snapshot, health


def validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load("reports/lot38/coverage_summary.json")
    mutation = load("reports/lot38/mutation_summary.json")

    require(coverage["status"] == "PASS", "Lot 38 coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 99.61, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 99.35, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below gate")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below gate")

    require(mutation["status"] == "PASS", "Lot 38 mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["killed_mutants"] == 1006, "killed mutant count changed")
    require(mutation["evaluated_mutants"] == 1232, "evaluated mutant count changed")
    require(mutation["total_mutants"] == 1232, "total mutant count changed")
    require(mutation["survived_mutants"] == 226, "survived mutant count changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutant count changed")
    require(mutation["mutation_score_percent"] == 81.66, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below gate")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    return coverage, mutation


def validate_documents() -> None:
    audit_doc = (ROOT / "docs/LOT_38_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix_doc = (ROOT / "docs/LOT38_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    implementation_report = (ROOT / "reports/lot_38_order_book_l2_snapshot_engine_report.md").read_text(encoding="utf-8")
    for text in (audit_doc, matrix_doc):
        for commit in (SOURCE_HEAD, EVIDENCE_HEAD, MERGED_COMMIT):
            require(commit in text, "Lot 38 audit documentation missing exact lineage commit")
        for evidence in (
            str(VALIDATION_RUN),
            str(VALIDATION_ARTIFACT),
            VALIDATION_DIGEST,
            str(MUTATION_RUN),
            str(MUTATION_ARTIFACT),
            MUTATION_DIGEST,
        ):
            require(evidence in text, "Lot 38 audit documentation missing final workflow evidence")
    require("GO_LOT38_POST_MERGE" in audit_doc, "Lot 38 post-merge verdict missing")
    require("Lot 39" in audit_doc and "PLANNED_LOCKED" in audit_doc, "Lot 39 lock missing")
    require("PASS_FROZEN_IMPLEMENTATION_EVIDENCE" in implementation_report, "implementation report not frozen PASS")


def validate() -> dict[str, Any]:
    lifecycle = validate_version_and_lifecycle()
    state, audit, snapshot, health = validate_artifacts()
    coverage, mutation = validate_quality()
    validate_documents()
    result: dict[str, Any] = {
        "schema_version": "lot38-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT38_POST_MERGE",
        "project_version": "0.38.0",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "merged_commit": MERGED_COMMIT,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "snapshot_checksum": snapshot["snapshot_checksum"],
        "health_checksum": health["health_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 39,
        "next_lot_status": lifecycle["lots"]["39"]["status"],
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
        Lot38PostMergeError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT38 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
