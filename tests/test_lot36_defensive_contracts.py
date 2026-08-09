from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

import crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure as closure
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure import (
    _closure_quality_veto,
    _freshness_reason_codes,
    _group_records,
    _interval_counts,
    _matching_quality_state,
    _quality_inputs,
    _validate_config,
    _verify_payload_checksum,
    build_lot36_artifacts,
    build_replay_evidence,
)
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_models import (
    ClosureManifestV1,
    FreshnessGapOutageEvidenceV1,
    Lot36LineageEnvelopeV1,
    Lot36MetricsV1,
    Lot36RunContextV1,
    LotValidationReportV1,
    ReplayEvidenceV1,
)
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_validation import (
    V3ClosureError,
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
    load_json_object,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "3" * 40
CONFIG_PATH = ROOT / "config/data_governance/freshness_gap_outage_v3_closure_v1.json"


def _state_and_replay():
    state, audit = build_lot36_artifacts(ROOT, CODE_COMMIT)
    replay = build_replay_evidence(ROOT, CODE_COMMIT)
    return state, audit, replay


def test_validation_primitives_reject_invalid_values() -> None:
    state, _, _ = _state_and_replay()
    event = closure.parse_utc_timestamp(state.event_time, "event_time")
    generated = closure.parse_utc_timestamp(state.generated_at, "generated_at")
    with pytest.raises(V3ClosureError, match="backwards"):
        duration_us(generated, event)
    with pytest.raises(V3ClosureError, match="safety"):
        validate_lot36_safety({})
    with pytest.raises(V3ClosureError, match="requires reason codes"):
        validate_reason_codes((), "test")
    with pytest.raises(ValueError):
        validate_reason_codes(("bad reason",), "test")
    with pytest.raises(V3ClosureError, match="causal"):
        validate_causal_times(state.generated_at, state.available_at, state.event_time)
    with pytest.raises(V3ClosureError, match="between 0 and 10000"):
        require_basis_points(10_001, "quality")
    with pytest.raises(V3ClosureError, match="cannot be empty"):
        require_non_empty_string_tuple((), "values")
    with pytest.raises(ValueError):
        require_non_empty_string_tuple(("bad value",), "values")
    with pytest.raises(ValueError):
        validate_git_and_sha256("not-a-sha", {})
    with pytest.raises(ValueError):
        validate_git_and_sha256(CODE_COMMIT, {"checksum": "bad"})
    with pytest.raises(V3ClosureError, match="runtime"):
        validate_runtime_mode("LIVE")
    assert validate_text_identity("expected", "field", "expected") == "expected"
    with pytest.raises(V3ClosureError, match="changed"):
        validate_text_identity("wrong", "field", "expected")


def test_run_context_and_lineage_reject_invalid_contracts() -> None:
    state, _, _ = _state_and_replay()
    with pytest.raises(V3ClosureError, match="runtime"):
        replace(state.run_context, runtime_mode="LIVE")
    with pytest.raises(ValueError):
        replace(state.run_context, code_commit="bad")
    with pytest.raises(ValueError):
        replace(state.lineage, entry_gate_checksum="bad")
    with pytest.raises(ValueError):
        replace(state.lineage, canonical_roadmap_blob_sha="bad")
    with pytest.raises(ValueError):
        replace(state.lineage, available_at="not-a-time")


def test_freshness_evidence_rejects_invalid_contracts() -> None:
    state, _, _ = _state_and_replay()
    evidence = state.freshness_audits[0]
    with pytest.raises(ValueError):
        replace(evidence, record_count=-1)
    with pytest.raises(V3ClosureError, match="causal"):
        replace(evidence, latest_available_at="2026-08-06T19:15:00.000000Z")
    with pytest.raises(V3ClosureError, match="between 0 and 10000"):
        replace(evidence, freshness_bps=10_001)
    with pytest.raises(V3ClosureError, match="unknown freshness"):
        replace(evidence, status="INVALID")
    with pytest.raises(V3ClosureError, match="requires reason codes"):
        replace(evidence, reason_codes=())


def test_lot_validation_report_rejects_incomplete_chain() -> None:
    state, _, _ = _state_and_replay()
    report = state.validation_report
    with pytest.raises(V3ClosureError, match="Lots 31-36"):
        replace(report, validated_lots=(31, 32, 33, 34, 35))
    with pytest.raises(ValueError):
        replace(report, required_validator_count=0)
    with pytest.raises(V3ClosureError, match="requires reason codes"):
        replace(report, reason_codes=())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("version_id", "V4_MICROSTRUCTURE", "version"),
        ("lots_included", (31, 32, 33, 34, 35), "Lots 31-36"),
        ("closure_status", "FINAL", "status"),
        ("v3_closed", True, "cannot finalize"),
        ("post_merge_audit_required", False, "requires post-merge"),
        ("human_review_required", False, "requires post-merge"),
        ("next_lot", 38, "Lot 37"),
        ("next_lot_status", "IMPLEMENTATION_STARTED", "Lot 37"),
        ("reason_codes", (), "requires reason codes"),
    ],
)
def test_closure_manifest_rejects_premature_or_invalid_promotion(
    field: str, value: object, message: str
) -> None:
    state, _, _ = _state_and_replay()
    with pytest.raises(V3ClosureError, match=message):
        replace(state.closure_manifest, **{field: value})


def test_replay_contract_rejects_inconsistent_evidence() -> None:
    _, _, replay = _state_and_replay()
    with pytest.raises(ValueError):
        replace(replay, run1_checksum="bad")
    with pytest.raises(V3ClosureError, match="unknown replay"):
        replace(replay, replay_status="MAYBE")
    with pytest.raises(V3ClosureError, match="contradicts"):
        replace(replay, match=False)
    divergent = "4" * 64
    with pytest.raises(V3ClosureError, match="REPLAY_MATCH"):
        ReplayEvidenceV1(
            replay.run1_checksum,
            divergent,
            "REPLAY_MATCH",
            False,
            replay.reason_codes,
            replay.replay_checksum,
        )
    with pytest.raises(V3ClosureError, match="requires reason codes"):
        replace(replay, reason_codes=())


def test_metrics_and_state_reject_invalid_or_empty_evidence() -> None:
    state, audit, _ = _state_and_replay()
    with pytest.raises(ValueError):
        replace(state.metrics, anomaly_total=-1)
    with pytest.raises(V3ClosureError, match="unknown Lot 36 validation"):
        replace(state, validation_state="UNKNOWN")
    with pytest.raises(V3ClosureError, match="requires freshness"):
        replace(state, freshness_audits=())
    with pytest.raises(V3ClosureError, match="requires freshness"):
        replace(state, quality_states=())
    with pytest.raises(V3ClosureError, match="requires reason codes"):
        replace(state, reason_codes=())
    unsafe = dict(lot36_safety())
    unsafe["trade_allowed"] = True
    with pytest.raises(V3ClosureError, match="safety"):
        replace(state, safety=unsafe)
    with pytest.raises(ValueError):
        replace(state, output_checksum="bad")
    with pytest.raises(ValueError):
        replace(audit, freshness_audit_count=0)
    with pytest.raises(V3ClosureError, match="unknown Lot 36 audit"):
        replace(audit, validation_state="UNKNOWN")
    with pytest.raises(V3ClosureError, match="safety"):
        replace(audit, safety=unsafe)
    with pytest.raises(ValueError):
        replace(audit, audit_checksum="bad")


def test_main_helpers_fail_closed_on_empty_duplicate_and_unknown_inputs() -> None:
    state, _, _ = _state_and_replay()
    assert _interval_counts([], 60_000_000, 3) == (0, 0, 0, 0, 0)
    with pytest.raises(V3ClosureError, match="requires quality records"):
        _group_records([])
    duplicated = (state.quality_states[0], state.quality_states[0])
    key = (
        state.quality_states[0].source_id,
        state.quality_states[0].instrument_id,
        state.quality_states[0].timeframe,
    )
    with pytest.raises(V3ClosureError, match="duplicate data quality state"):
        _matching_quality_state(duplicated, key)
    assert _matching_quality_state((), key) is None
    reasons = _freshness_reason_codes(1, 1, 1, 1, False, False)
    assert reasons == (
        "QUALITY_STATE_MISSING",
        "MISSING_INTERVALS_DETECTED",
        "GAPS_DETECTED",
        "OUTAGES_DETECTED",
        "LATEST_DATA_STALE",
    )
    assert _freshness_reason_codes(0, 0, 0, 0, True, False) == (
        "QUALITY_STATE_NOT_PASS",
    )


def test_quality_veto_blocks_unknown_or_below_threshold_quality() -> None:
    state, _, _ = _state_and_replay()
    evidence = state.freshness_audits
    unknown = _closure_quality_veto((), (), evidence, 9500)
    assert unknown.action == "BLOCK_ANALYSIS_OR_TRADING"
    low = replace(state.quality_states[0], quality_score_bps=9499)
    blocked = _closure_quality_veto((low,), (), evidence, 9500)
    assert blocked.action == "BLOCK_ANALYSIS_OR_TRADING"


def test_config_validation_rejects_schema_thresholds_chain_and_time() -> None:
    config = load_json_object(CONFIG_PATH)
    broken = copy.deepcopy(config)
    broken["unexpected"] = True
    with pytest.raises(V3ClosureError, match="fields differ"):
        _validate_config(broken)
    for field, value, message in (
        ("schema_version", "wrong", "schema"),
        ("config_version", "wrong", "version"),
        ("max_staleness_seconds", -1, "max_staleness_seconds"),
        ("outage_interval_multiplier", 1, "outage_interval_multiplier"),
        ("required_lots", [31, 32], "required lot chain"),
    ):
        broken = copy.deepcopy(config)
        broken[field] = value
        with pytest.raises((V3ClosureError, ValueError), match=message):
            _validate_config(broken)
    broken = copy.deepcopy(config)
    broken["event_time"] = "2026-08-06T19:21:00.000000Z"
    with pytest.raises(V3ClosureError, match="causal time"):
        _validate_config(broken)


def test_payload_checksum_rejects_tamper() -> None:
    payload = {"field": "value", "output_checksum": "0" * 64}
    with pytest.raises(V3ClosureError, match="checksum mismatch"):
        _verify_payload_checksum(payload, "output_checksum", "0" * 64, "fixture")


def test_quality_inputs_reject_missing_records_and_intervals(tmp_path: Path) -> None:
    config = {"lot34_config_path": "quality.json"}
    (tmp_path / "quality.json").write_text(json.dumps({"records": []}), encoding="utf-8")
    with pytest.raises(V3ClosureError, match="timeframe configuration"):
        _quality_inputs(tmp_path, config)
    (tmp_path / "quality.json").write_text(
        json.dumps({"records": "bad", "timeframe_seconds": {"1m": 60}}),
        encoding="utf-8",
    )
    with pytest.raises(V3ClosureError, match="records unavailable"):
        _quality_inputs(tmp_path, config)


def test_constructor_smoke_for_explicit_contract_classes() -> None:
    state, _, replay = _state_and_replay()
    assert isinstance(state.run_context, Lot36RunContextV1)
    assert isinstance(state.lineage, Lot36LineageEnvelopeV1)
    assert isinstance(state.freshness_audits[0], FreshnessGapOutageEvidenceV1)
    assert isinstance(state.validation_report, LotValidationReportV1)
    assert isinstance(state.closure_manifest, ClosureManifestV1)
    assert isinstance(state.metrics, Lot36MetricsV1)
    assert isinstance(replay, ReplayEvidenceV1)
