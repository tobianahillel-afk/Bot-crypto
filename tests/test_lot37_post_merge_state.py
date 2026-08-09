from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_lot37_post_merge import (
    AUDIT_CHECKSUM,
    EVIDENCE_HEAD,
    MATRIX_CHECKSUM,
    MERGED_COMMIT,
    MUTATION_DIGEST,
    REGISTRY_CHECKSUM,
    SOURCE_HEAD,
    STATE_CHECKSUM,
    VALIDATION_DIGEST,
    canonical_checksum,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, object]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot37_post_merge_certification_is_exact_archival_evidence() -> None:
    overlay = _load("data/audit/roadmap_lifecycle_overlay_lot37.json")
    lot37 = overlay["lots"]["37"]
    assert overlay["latest_implemented_lot"] == 37
    assert lot37["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_SCOPE_CONTRACTS_ONLY"
    assert lot37["implementation_commit"] == SOURCE_HEAD
    assert lot37["evidence_commit"] == EVIDENCE_HEAD
    assert lot37["merged_commit"] == MERGED_COMMIT
    assert lot37["pull_request"] == 38
    assert lot37["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert lot37["analysis_only"] is True
    assert lot37["trade_allowed"] is False
    assert lot37["execution_allowed"] is False
    assert overlay["lots"]["38"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }


def test_lot37_frozen_artifacts_and_quality_remain_exact() -> None:
    state = _load("data/audit/microstructure_scope_and_offline_data_contracts_lot37.json")
    audit = _load("data/audit/microstructure_scope_and_offline_data_contracts_audit_lot37.json")
    registry = _load("data/audit/microstructure_contract_registry_lot37.json")
    matrix = _load("data/audit/microstructure_capability_matrix_lot37.json")
    coverage = _load("reports/lot37/coverage_summary.json")
    mutation = _load("reports/lot37/mutation_summary.json")

    state_body = dict(state)
    assert state_body.pop("output_checksum") == STATE_CHECKSUM
    assert canonical_checksum(state_body) == STATE_CHECKSUM
    audit_body = dict(audit)
    assert audit_body.pop("audit_checksum") == AUDIT_CHECKSUM
    assert canonical_checksum(audit_body) == AUDIT_CHECKSUM
    assert canonical_checksum(registry) == REGISTRY_CHECKSUM
    assert canonical_checksum(matrix) == MATRIX_CHECKSUM
    assert audit["state_output_checksum"] == STATE_CHECKSUM
    assert audit["contract_registry_checksum"] == REGISTRY_CHECKSUM
    assert audit["capability_matrix_checksum"] == MATRIX_CHECKSUM
    assert state["run_context"]["code_commit"] == SOURCE_HEAD
    assert audit["code_commit"] == SOURCE_HEAD

    assert coverage["status"] == "PASS"
    assert coverage["source_head_sha"] == SOURCE_HEAD
    assert coverage["line_coverage_percent"] == 100.0
    assert coverage["branch_coverage_percent"] == 100.0
    assert coverage["anti_flake_repetitions"] == 3
    assert mutation["status"] == "PASS"
    assert mutation["source_head_sha"] == SOURCE_HEAD
    assert mutation["killed_mutants"] == 1098
    assert mutation["evaluated_mutants"] == 1368
    assert mutation["survived_mutants"] == 270
    assert mutation["mutation_score_percent"] == 80.26


def test_lot37_frozen_ci_digests_and_stages_are_exact() -> None:
    assert VALIDATION_DIGEST == (
        "sha256:c163bd5855ddb6ce99b36fbd52834702ee8ea9706d162acc47fe0e474a37dab4"
    )
    assert MUTATION_DIGEST == (
        "sha256:1ce9b7ac4d87465a441403262e3764cb8bef824cdff0c3eae59bc6bf68dcef68"
    )
    assert len({SOURCE_HEAD, EVIDENCE_HEAD, MERGED_COMMIT}) == 3
    assert all(len(commit) == 40 for commit in (SOURCE_HEAD, EVIDENCE_HEAD, MERGED_COMMIT))
