#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from validate_lot44_frozen_evidence import validate as validate_frozen  # noqa: E402

GATE_MERGE = "6bbf4fcc5543f2599378bcab93263e2c8cebcec6"
SOURCE_HEAD = "d3cc4cf916ecea5166716746143a593f01b1d051"
CERTIFICATION_ANCHOR = "720b6f895672b650a7c7df96cdf68524479ae3f4"
EVIDENCE_HEAD = "8ca3edadb7e811bad428575cfe236b20dd5ed62f"
VALIDATOR_HEAD = "888fbf696432bec1a5f9d3e4f9c09279ed569325"
FINAL_PR_HEAD = "8287155273e87f3c6d27a74ad373ac6a9ba0b026"
IMPLEMENTATION_MERGE = "5c5d3c388abaf10e2e81593a6a3918375a0c0e19"
CI_REMEDIATION_1_PR_HEAD = "251aa7f5c35f8468e7b933552a6c235c80a6ea1b"
CI_REMEDIATION_MERGE_1 = "80ea86b0a015a35d27c57e444e1ee7874eedbe53"
CI_REMEDIATION_2_PR_HEAD = "59daee501f3f6c471e850683036092a70aa959a0"
CI_REMEDIATION_MERGE_2 = "e390b6e5d76c53d9dd6d74724f3246b92e628079"
FROZEN_RUN = 31737462959
FROZEN_ARTIFACT = 9196052857
FROZEN_ARTIFACT_DIGEST = (
    "sha256:0445eb4cba2c8539352cd67b899b7ee7566325cc73adea7c63fa705772762381"
)
POST_MERGE_LOT29_REPLAY_RUN = 31796447075
POST_MERGE_QUALITY_RUN = 31796447157

CERTIFICATION_PATHS = {
    ".github/workflows/lot44-mutation-assurance.yml",
    ".github/workflows/lot44-trades-aggressor-classification.yml",
}
EVIDENCE_PATHS = {
    "data/audit/trades_and_aggressor_classification_schema_audit_lot44.json",
    "data/audit/trades_and_aggressor_classification_schema_lot44.json",
    "reports/lot44/coverage_summary.json",
    "reports/lot44/mutation_summary.json",
}
CI_REMEDIATION_1_PATHS = {
    ".github/workflows/lot35-post-merge-audit.yml",
    "scripts/run_lot18_no_trading_compliance.py",
    "tests/test_lot18_network_surface_regression.py",
}
CI_REMEDIATION_2_PATHS = {
    "scripts/run_lot19_release_candidate.py",
    "tests/test_lot18_network_surface_regression.py",
}
AUDIT_BRANCH_PATHS = {
    ".github/workflows/lot44-post-merge-audit.yml",
    "scripts/validate_lot44_post_merge.py",
}
SOURCE_IMMUTABLE_PATHS = (
    "config/microstructure/trades_and_aggressor_classification_schema_v1.json",
    "contracts/schemas/classified_trade_v1.schema.json",
    "contracts/schemas/aggressor_confidence_state_v1.schema.json",
    "contracts/schemas/trades_aggressor_classification_schema_state_v1.schema.json",
    "contracts/schemas/trades_aggressor_classification_schema_audit_v1.schema.json",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
    "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    "scripts/validate_lot44.py",
    "scripts/validate_lot44_no_connectivity.py",
    "tests/test_lot44_trades_and_aggressor_classification_schema.py",
    "tests/test_lot44_schema_contracts.py",
    "tests/test_lot44_causal_guards.py",
    "tests/test_lot44_runtime_confidence_version.py",
    "docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_44.md",
    "reports/lot_44_trades_and_aggressor_classification_schema_report.md",
)
DOWNSTREAM_FORBIDDEN = (
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
    "scripts/run_lot45_order_flow_delta_and_cvd_engine.py",
    "scripts/validate_lot45.py",
    "tests/test_lot45_order_flow_delta_and_cvd_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine_models.py",
    "scripts/run_lot46_trade_classification_confidence_engine.py",
    "scripts/validate_lot46.py",
    "tests/test_lot46_trade_classification_confidence_engine.py",
)


class Lot44PostMergeAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot44PostMergeAuditError(message)


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def is_ancestor(older: str, newer: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def changed_paths(base: str, head: str) -> set[str]:
    raw = git("diff", "--name-only", base, head)
    return {line for line in raw.splitlines() if line}


def rev_count(base: str, head: str) -> int:
    return int(git("rev-list", "--count", f"{base}..{head}"))


def merge_parents(commit: str) -> set[str]:
    return set(git("show", "-s", "--format=%P", commit).split())


def canonical_checksum(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_git_chain() -> None:
    head = git("rev-parse", "HEAD")
    for older, newer, label in (
        (GATE_MERGE, SOURCE_HEAD, "gate/source"),
        (SOURCE_HEAD, CERTIFICATION_ANCHOR, "source/certification"),
        (CERTIFICATION_ANCHOR, EVIDENCE_HEAD, "certification/evidence"),
        (EVIDENCE_HEAD, VALIDATOR_HEAD, "evidence/validator"),
        (VALIDATOR_HEAD, FINAL_PR_HEAD, "validator/final-pr-head"),
        (FINAL_PR_HEAD, IMPLEMENTATION_MERGE, "final-pr-head/implementation-merge"),
        (IMPLEMENTATION_MERGE, CI_REMEDIATION_MERGE_1, "implementation/remediation-1"),
        (CI_REMEDIATION_MERGE_1, CI_REMEDIATION_MERGE_2, "remediation-1/remediation-2"),
        (CI_REMEDIATION_MERGE_2, head, "remediation-2/audit-head"),
    ):
        require(is_ancestor(older, newer), f"Lot44 ancestry failed: {label}")

    implementation_parents = merge_parents(IMPLEMENTATION_MERGE)
    require(FINAL_PR_HEAD in implementation_parents, "implementation merge does not contain final PR head")
    require(len(implementation_parents) >= 2, "implementation merge must remain a merge commit")

    require(
        merge_parents(CI_REMEDIATION_MERGE_1)
        == {IMPLEMENTATION_MERGE, CI_REMEDIATION_1_PR_HEAD},
        "CI remediation merge 1 parents changed",
    )
    require(
        merge_parents(CI_REMEDIATION_MERGE_2)
        == {CI_REMEDIATION_MERGE_1, CI_REMEDIATION_2_PR_HEAD},
        "CI remediation merge 2 parents changed",
    )

    require(rev_count(SOURCE_HEAD, CERTIFICATION_ANCHOR) == 2, "certification commit count changed")
    require(
        changed_paths(SOURCE_HEAD, CERTIFICATION_ANCHOR) == CERTIFICATION_PATHS,
        "certification path set changed",
    )
    require(rev_count(CERTIFICATION_ANCHOR, EVIDENCE_HEAD) == 4, "evidence commit count changed")
    require(
        changed_paths(CERTIFICATION_ANCHOR, EVIDENCE_HEAD) == EVIDENCE_PATHS,
        "evidence path set changed",
    )
    require(rev_count(EVIDENCE_HEAD, VALIDATOR_HEAD) == 1, "validator commit count changed")
    require(
        changed_paths(EVIDENCE_HEAD, VALIDATOR_HEAD)
        == {"scripts/validate_lot44_frozen_evidence.py"},
        "validator path set changed",
    )
    require(rev_count(VALIDATOR_HEAD, FINAL_PR_HEAD) == 1, "final frozen workflow commit count changed")
    require(
        changed_paths(VALIDATOR_HEAD, FINAL_PR_HEAD)
        == {".github/workflows/lot44-frozen-evidence.yml"},
        "final frozen workflow path set changed",
    )
    require(
        rev_count(IMPLEMENTATION_MERGE, CI_REMEDIATION_MERGE_1) == 10,
        "CI remediation 1 commit count changed",
    )
    require(
        changed_paths(IMPLEMENTATION_MERGE, CI_REMEDIATION_MERGE_1)
        == CI_REMEDIATION_1_PATHS,
        "CI remediation 1 path set changed",
    )
    require(
        rev_count(CI_REMEDIATION_MERGE_1, CI_REMEDIATION_MERGE_2) == 3,
        "CI remediation 2 commit count changed",
    )
    require(
        changed_paths(CI_REMEDIATION_MERGE_1, CI_REMEDIATION_MERGE_2)
        == CI_REMEDIATION_2_PATHS,
        "CI remediation 2 path set changed",
    )
    audit_paths = changed_paths(CI_REMEDIATION_MERGE_2, head)
    require(
        audit_paths == AUDIT_BRANCH_PATHS,
        f"unexpected post-merge audit branch paths: {sorted(audit_paths)}",
    )


def validate_immutability() -> None:
    head = git("rev-parse", "HEAD")
    source_drift = changed_paths(SOURCE_HEAD, head)
    for path in SOURCE_IMMUTABLE_PATHS:
        require(path not in source_drift, f"Lot44 source/test/doc drift after source freeze: {path}")
    require(
        not changed_paths(CERTIFICATION_ANCHOR, head).intersection(CERTIFICATION_PATHS),
        "Lot44 certification workflows drifted after certification anchor",
    )
    require(
        not changed_paths(EVIDENCE_HEAD, head).intersection(EVIDENCE_PATHS),
        "Lot44 evidence drifted after evidence head",
    )
    require(
        "scripts/validate_lot44_frozen_evidence.py"
        not in changed_paths(VALIDATOR_HEAD, head),
        "Lot44 frozen validator drifted after validator head",
    )
    require(
        ".github/workflows/lot44-frozen-evidence.yml"
        not in changed_paths(FINAL_PR_HEAD, head),
        "Lot44 frozen evidence workflow drifted after final PR head",
    )


def validate_downstream_lock() -> None:
    for path in DOWNSTREAM_FORBIDDEN:
        require(not (ROOT / path).exists(), f"downstream lot unexpectedly exists: {path}")


def validate() -> dict[str, Any]:
    validate_git_chain()
    validate_immutability()
    frozen = validate_frozen()
    require(frozen["status"] == "PASS", "frozen v7 validator not PASS")
    require(frozen["source_head"] == SOURCE_HEAD, "frozen source mismatch")
    require(frozen["evidence_head"] == EVIDENCE_HEAD, "frozen evidence mismatch")
    require(
        frozen["review_hardening"]["classified_trades_defensively_frozen"] is True,
        "defensive classified-trades freeze not proven",
    )
    validate_downstream_lock()

    payload: dict[str, Any] = {
        "schema_version": "lot44-post-merge-audit-v2",
        "status": "PASS",
        "verdict": "GO_LOT44_POST_MERGE",
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
        "validator_head": VALIDATOR_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "implementation_merge": IMPLEMENTATION_MERGE,
        "ci_remediation_merge_1": CI_REMEDIATION_MERGE_1,
        "ci_remediation_merge_2": CI_REMEDIATION_MERGE_2,
        "audit_head": git("rev-parse", "HEAD"),
        "frozen_run": FROZEN_RUN,
        "frozen_artifact": FROZEN_ARTIFACT,
        "frozen_artifact_digest": FROZEN_ARTIFACT_DIGEST,
        "post_merge_lot29_replay_run": POST_MERGE_LOT29_REPLAY_RUN,
        "post_merge_quality_run": POST_MERGE_QUALITY_RUN,
        "state_output_checksum": frozen["state_output_checksum"],
        "audit_checksum": frozen["audit_checksum"],
        "confidence_checksum": frozen["confidence_checksum"],
        "line_coverage_percent": frozen["line_coverage_percent"],
        "branch_coverage_percent": frozen["branch_coverage_percent"],
        "mutation_score_percent": frozen["mutation_score_percent"],
        "lot45_status_before_gate": "PLANNED_LOCKED",
        "lot46_status": "PLANNED_LOCKED",
    }
    payload["post_merge_checksum"] = canonical_checksum(payload)
    return payload


def main() -> None:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    print(result["verdict"])


if __name__ == "__main__":
    main()
