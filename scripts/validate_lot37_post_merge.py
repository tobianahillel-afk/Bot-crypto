#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "59b189e9980772245993a9212b6c8ad5e9a88a00"
EVIDENCE_HEAD = "91c28f17acc2f66c906dddee96cbda369945f3ea"
MERGED_COMMIT = "f1da136ff956e40915fab42ae21748a6f2b1ebca"
CERTIFIED_RELEASE = "0.37.0"
STATE_CHECKSUM = "ea960217eb9a2159c4a99c56257a37c43869ffad0da86555fef24eb356e5f8e7"
AUDIT_CHECKSUM = "aa2df489e636860c119eb2ed54f7a5f03ede09838dfbd056dae0bb5a8a2a482f"
REGISTRY_CHECKSUM = "129140ffb7e812afd59d0174d318c5e3388d23bc49cc554168bde558bc0bf590"
MATRIX_CHECKSUM = "f7132fcfdab898af3f733b2715e0836d23e6284f8c0c1f3e7dd92ccf0070f1b4"
CONFIG_CHECKSUM = "a6e79dae8567aeafd5b25e3793a901097dd1714e9ec6c5f19a771417e78d6a78"
VALIDATION_DIGEST = "sha256:c163bd5855ddb6ce99b36fbd52834702ee8ea9706d162acc47fe0e474a37dab4"
MUTATION_DIGEST = "sha256:1ce9b7ac4d87465a441403262e3764cb8bef824cdff0c3eae59bc6bf68dcef68"


class Lot37PostMergeError(RuntimeError):
    """Raised when the independent Lot 37 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot37PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_checksum(path: str, field: str, expected: str) -> dict[str, Any]:
    payload = load(path)
    body = dict(payload)
    checksum = body.pop(field, None)
    require(checksum == expected, f"{path}: certified checksum changed")
    require(canonical_checksum(body) == checksum, f"{path}: checksum mismatch")
    return payload


def validate_version_and_lifecycle() -> dict[str, Any]:
    """Validate the frozen Lot 37 release, independent of the current project version.

    Lot 37 was certified as release 0.37.0. Later audited releases must not make the
    historical proof fail merely because ``pyproject.toml`` advances to 0.38.0+.
    The certified release identity remains bound by the immutable audit documents,
    lifecycle overlay, source/evidence heads and artifact checksums below.
    """
    previous = load("data/audit/roadmap_lifecycle_overlay_lot36.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot37.json")
    require(
        current["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot36.json",
        "Lot 37 lifecycle predecessor mismatch",
    )
    require(current["latest_implemented_lot"] == 37, "latest implemented lot must be 37")
    for lot in range(26, 37):
        require(
            current["lots"][str(lot)] == previous["lots"][str(lot)],
            f"Lot {lot} lifecycle was rewritten",
        )
    lot37 = current["lots"]["37"]
    expected = {
        "status": "IMPLEMENTED_VALIDATED_OFFLINE_SCOPE_CONTRACTS_ONLY",
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 38,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for field, value in expected.items():
        require(lot37.get(field) == value, f"Lot 37 lifecycle mismatch: {field}")
    require(lot37.get("analysis_only") is True, "Lot 37 analysis_only changed")
    require(
        lot37.get("participant_behavior_inference_explicitly_labeled") is True,
        "Lot 37 participant-inference labeling changed",
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
        require(lot37.get(field) is False, f"Lot 37 permission enabled: {field}")
    require(
        current["lots"]["38"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 38 historical lock changed",
    )
    return current


def validate_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    state = verify_checksum(
        "data/audit/microstructure_scope_and_offline_data_contracts_lot37.json",
        "output_checksum",
        STATE_CHECKSUM,
    )
    audit = verify_checksum(
        "data/audit/microstructure_scope_and_offline_data_contracts_audit_lot37.json",
        "audit_checksum",
        AUDIT_CHECKSUM,
    )
    registry = load("data/audit/microstructure_contract_registry_lot37.json")
    matrix = load("data/audit/microstructure_capability_matrix_lot37.json")
    require(canonical_checksum(registry) == REGISTRY_CHECKSUM, "Lot 37 registry checksum changed")
    require(canonical_checksum(matrix) == MATRIX_CHECKSUM, "Lot 37 matrix checksum changed")
    require(state["contract_registry"] == registry, "Lot 37 state/registry mismatch")
    require(state["capability_matrix"] == matrix, "Lot 37 state/matrix mismatch")
    require(audit["state_output_checksum"] == STATE_CHECKSUM, "Lot 37 state/audit link changed")
    require(audit["contract_registry_checksum"] == REGISTRY_CHECKSUM, "registry audit link changed")
    require(audit["capability_matrix_checksum"] == MATRIX_CHECKSUM, "matrix audit link changed")
    require(audit["config_checksum"] == CONFIG_CHECKSUM, "config checksum changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["validation_state"] == "VALIDATED_OFFLINE_CONTRACT_SCOPE", "state changed")
    require(audit["validation_state"] == "VALIDATED_OFFLINE_CONTRACT_SCOPE", "audit changed")
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
        require(safety[field] is False, f"Lot 37 state permission enabled: {field}")
    lot38 = next(
        item for item in matrix["entries"]
        if item["capability_id"] == "LOT38_ORDER_BOOK_L2_SNAPSHOT_ENGINE"
    )
    require(lot38["classification"] == "DISABLED", "Lot 38 historical classification changed")
    require(
        lot38["implementation_status"] == "PLANNED_LOCKED",
        "Lot 38 historical capability lock changed",
    )
    return state, audit


def validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load("reports/lot37/coverage_summary.json")
    mutation = load("reports/lot37/mutation_summary.json")
    require(coverage["status"] == "PASS", "Lot 37 coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["workflow_run_id"] == 31325582304, "coverage run changed")
    require(coverage["artifact_id"] == 9041433151, "coverage artifact changed")
    require(coverage["artifact_digest"] == VALIDATION_DIGEST, "coverage digest changed")
    require(coverage["line_coverage_percent"] == 100.0, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 100.0, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below gate")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below gate")
    require(mutation["status"] == "PASS", "Lot 37 mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["workflow_run_id"] == 31325582303, "mutation run changed")
    require(mutation["artifact_id"] == 9041434170, "mutation artifact changed")
    require(mutation["artifact_digest"] == MUTATION_DIGEST, "mutation digest changed")
    require(mutation["killed_mutants"] == 1098, "killed mutant count changed")
    require(mutation["evaluated_mutants"] == 1368, "evaluated mutant count changed")
    require(mutation["survived_mutants"] == 270, "survived mutant count changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutant count changed")
    require(mutation["mutation_score_percent"] == 80.26, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below gate")
    return coverage, mutation


def validate_documents() -> None:
    audit_doc = (ROOT / "docs/LOT_37_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix_doc = (ROOT / "docs/LOT37_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    for text in (audit_doc, matrix_doc):
        for commit in (SOURCE_HEAD, EVIDENCE_HEAD, MERGED_COMMIT):
            require(commit in text, "Lot 37 audit documentation missing exact lineage commit")
    require("GO_LOT37_POST_MERGE" in audit_doc, "Lot 37 post-merge verdict missing")
    require("Lot 38" in audit_doc and "PLANNED_LOCKED" in audit_doc, "Lot 38 historical lock missing")


def validate() -> dict[str, Any]:
    lifecycle = validate_version_and_lifecycle()
    state, audit = validate_artifacts()
    coverage, mutation = validate_quality()
    validate_documents()
    result: dict[str, Any] = {
        "schema_version": "lot37-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT37_POST_MERGE",
        "project_version": CERTIFIED_RELEASE,
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "merged_commit": MERGED_COMMIT,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "contract_registry_checksum": REGISTRY_CHECKSUM,
        "capability_matrix_checksum": MATRIX_CHECKSUM,
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 38,
        "next_lot_status": lifecycle["lots"]["38"]["status"],
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
        Lot37PostMergeError,
        OSError,
        KeyError,
        StopIteration,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT37 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

