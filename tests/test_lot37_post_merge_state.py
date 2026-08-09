from __future__ import annotations

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
    validate,
)


def test_lot37_post_merge_certification_is_exact() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT37_POST_MERGE"
    assert result["project_version"] == "0.37.0"
    assert result["source_head"] == SOURCE_HEAD
    assert result["evidence_head"] == EVIDENCE_HEAD
    assert result["merged_commit"] == MERGED_COMMIT
    assert result["state_output_checksum"] == STATE_CHECKSUM
    assert result["audit_checksum"] == AUDIT_CHECKSUM
    assert result["contract_registry_checksum"] == REGISTRY_CHECKSUM
    assert result["capability_matrix_checksum"] == MATRIX_CHECKSUM
    assert result["line_coverage_percent"] == 100.0
    assert result["branch_coverage_percent"] == 100.0
    assert result["mutation_score_percent"] == 80.26
    assert result["latest_implemented_lot"] == 37
    assert result["next_lot"] == 38
    assert result["next_lot_status"] == "PLANNED_LOCKED"
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0
    assert len(result["validation_checksum"]) == 64


def test_lot37_frozen_ci_digests_are_exact() -> None:
    assert VALIDATION_DIGEST == (
        "sha256:c163bd5855ddb6ce99b36fbd52834702ee8ea9706d162acc47fe0e474a37dab4"
    )
    assert MUTATION_DIGEST == (
        "sha256:1ce9b7ac4d87465a441403262e3764cb8bef824cdff0c3eae59bc6bf68dcef68"
    )


def test_lot37_certified_commits_are_distinct_stages() -> None:
    assert len({SOURCE_HEAD, EVIDENCE_HEAD, MERGED_COMMIT}) == 3
    assert all(len(commit) == 40 for commit in (SOURCE_HEAD, EVIDENCE_HEAD, MERGED_COMMIT))
