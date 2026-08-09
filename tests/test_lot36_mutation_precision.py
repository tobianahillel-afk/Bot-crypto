from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure as closure
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_validation import (
    duration_us,
    lot36_safety,
    require_basis_points,
    require_non_empty_string_tuple,
    validate_causal_times,
    validate_git_and_sha256,
    validate_lot36_safety,
    validate_reason_codes,
    validate_runtime_mode,
    validate_text_identity,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "6" * 40


def _expected_manifest(ready: bool) -> dict[str, object]:
    status = "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT" if ready else "BLOCKED"
    reason_codes = [
        "V3_CLOSURE_CANDIDATE_READY" if ready else "V3_CLOSURE_BLOCKED",
        "POST_MERGE_AUDIT_REQUIRED",
        "HUMAN_REVIEW_REQUIRED",
        "LOT37_REMAINS_LOCKED",
    ]
    payload: dict[str, object] = {
        "schema_version": "closure-manifest-v1",
        "version_id": "V3_MARKET_DATA_GOVERNANCE",
        "lots_included": list(range(31, 37)),
        "closure_status": status,
        "v3_closed": False,
        "post_merge_audit_required": True,
        "human_review_required": True,
        "next_lot": 37,
        "next_lot_status": "PLANNED_LOCKED",
        "reason_codes": reason_codes,
    }
    return {**payload, "manifest_checksum": canonical_checksum(payload)}


def test_manifest_ready_is_exact_and_still_locks_lot37() -> None:
    manifest = closure._build_manifest(True)
    assert manifest.to_dict() == _expected_manifest(True)


def test_manifest_blocked_is_exact_and_still_locks_lot37() -> None:
    manifest = closure._build_manifest(False)
    assert manifest.to_dict() == _expected_manifest(False)


def test_validation_report_is_exact_for_ready_and_blocked_states() -> None:
    ready = closure._build_validation_report(True)
    blocked = closure._build_validation_report(False)
    assert ready.to_dict() == {
        "schema_version": "lot-validation-report-v1",
        "validated_lots": [31, 32, 33, 34, 35, 36],
        "required_validator_count": 6,
        "closure_candidate_ready": True,
        "reason_codes": [
            "LOTS31_35_CERTIFIED_LINEAGE_VERIFIED",
            "LOT36_CLOSURE_INVARIANTS_PASS",
        ],
    }
    assert blocked.to_dict() == {
        "schema_version": "lot-validation-report-v1",
        "validated_lots": [31, 32, 33, 34, 35, 36],
        "required_validator_count": 6,
        "closure_candidate_ready": False,
        "reason_codes": [
            "LOTS31_35_CERTIFIED_LINEAGE_VERIFIED",
            "LOT36_CLOSURE_INVARIANTS_BLOCKED",
        ],
    }


def test_output_paths_are_exact_and_all_remain_under_audit_directory() -> None:
    paths = closure._output_paths(ROOT)
    assert {name: str(path.relative_to(ROOT)) for name, path in paths.items()} == {
        "state": "data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json",
        "audit": "data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json",
        "quality_states": "data/audit/data_quality_states_lot36.json",
        "anomalies": "data/audit/data_anomalies_lot36.json",
        "quality_veto": "data/audit/data_quality_veto_lot36.json",
        "replay": "data/audit/replay_evidence_lot36.json",
        "manifest": "data/audit/closure_manifest_lot36.json",
    }


def test_validation_primitives_accept_exact_boundaries() -> None:
    start = datetime(2026, 8, 9, tzinfo=UTC)
    assert duration_us(start, start) == 0
    assert duration_us(start, start + timedelta(microseconds=1)) == 1
    assert duration_us(start, start + timedelta(seconds=1)) == 1_000_000
    assert duration_us(start, start + timedelta(days=1, seconds=2, microseconds=3)) == 86_402_000_003

    safety = lot36_safety()
    assert safety == {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }
    validate_lot36_safety(safety)
    validate_reason_codes(("VALID_REASON", "SECOND_REASON"), "fixture")
    require_non_empty_string_tuple(("VALID_VALUE",), "fixture")
    assert require_basis_points(0, "basis") == 0
    assert require_basis_points(10_000, "basis") == 10_000
    validate_git_and_sha256("a" * 40, {"first": "b" * 64, "second": "c" * 64})
    validate_runtime_mode("DATA_GOVERNANCE_ONLY")
    assert validate_text_identity("EXACT", "fixture", "EXACT") == "EXACT"

    validate_causal_times(
        "2026-08-09T10:00:00.000000Z",
        "2026-08-09T10:00:00.000000Z",
        "2026-08-09T10:00:00.000000Z",
    )
    validate_causal_times(
        "2026-08-09T10:00:00.000000Z",
        "2026-08-09T10:00:00.000001Z",
        "2026-08-09T10:00:00.000002Z",
    )


def test_replay_evidence_matches_exact_reference_contract() -> None:
    state, _ = closure.build_lot36_artifacts(ROOT, CODE_COMMIT)
    replay = closure.build_replay_evidence(ROOT, CODE_COMMIT)
    payload: dict[str, object] = {
        "schema_version": "replay-evidence-v1",
        "run1_checksum": state.output_checksum,
        "run2_checksum": state.output_checksum,
        "replay_status": "REPLAY_MATCH",
        "match": True,
        "reason_codes": ["LOT36_DETERMINISTIC_REPLAY_MATCH"],
    }
    assert replay.to_dict() == {**payload, "replay_checksum": canonical_checksum(payload)}
