from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure import (
    EXPECTED_LOT34_IMPLEMENTATION_COMMIT,
    _closure_quality_veto,
    audit_freshness_gap_outage,
    build_lot36_artifacts,
    build_replay_evidence,
)
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_models import (
    FreshnessGapOutageEvidenceV1,
)
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_validation import (
    V3ClosureError,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    load_json_object,
)
from crypto_quant_bot.data_governance.market_data_quality_engine import (
    build_lot34_artifacts,
    detect_anomalies,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_models import (
    DataQualityStateV1,
)

ROOT = Path(__file__).resolve().parents[1]
QUALITY_CONFIG = ROOT / "config/data_governance/market_data_quality_engine_v1.json"
CODE_COMMIT = "1" * 40
Mutation = Callable[[list[dict[str, Any]]], None]


def _quality_fixture() -> tuple[dict[str, Any], tuple[DataQualityStateV1, ...]]:
    config = load_json_object(QUALITY_CONFIG)
    state, _ = build_lot34_artifacts(ROOT, EXPECTED_LOT34_IMPLEMENTATION_COMMIT)
    return config, state.quality_states


def _records(config: dict[str, Any]) -> list[dict[str, Any]]:
    records = config["records"]
    assert isinstance(records, list)
    assert all(isinstance(record, dict) for record in records)
    return records


def _audit(
    records: list[dict[str, Any]],
    quality_states: tuple[DataQualityStateV1, ...],
    reference: str,
    max_staleness: int = 121,
) -> tuple[FreshnessGapOutageEvidenceV1, ...]:
    return audit_freshness_gap_outage(
        records,
        quality_states,
        {"1m": 60},
        reference,
        max_staleness,
        3,
    )


def _remove_middle(records: list[dict[str, Any]]) -> None:
    records.pop(1)


def _append_duplicate(records: list[dict[str, Any]]) -> None:
    records.append(copy.deepcopy(records[0]))


def _reverse(records: list[dict[str, Any]]) -> None:
    records.reverse()


def _make_stale(records: list[dict[str, Any]]) -> None:
    records[0]["available_at"] = "2026-08-06T19:15:00.000000Z"


def _break_ohlc(records: list[dict[str, Any]]) -> None:
    records[0]["high"] = "56000.00"


def _negative_volume(records: list[dict[str, Any]]) -> None:
    records[0]["volume"] = "-1"


def _impossible_spread(records: list[dict[str, Any]]) -> None:
    records[0]["bid"] = "58000.00"


def _schema_drift(records: list[dict[str, Any]]) -> None:
    records[0]["source_schema_version"] = "future-schema-v9"


def test_lot36_reference_build_is_candidate_only_and_fail_closed() -> None:
    state, audit = build_lot36_artifacts(ROOT, CODE_COMMIT)
    assert state.validation_state == "VALIDATED_V3_CLOSURE_CANDIDATE"
    assert state.data_quality_veto.action == "ALLOW_ANALYSIS"
    assert state.reconciliation_veto.action == "ALLOW_ANALYSIS"
    assert state.closure_manifest.closure_status == "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT"
    assert state.closure_manifest.v3_closed is False
    assert state.closure_manifest.post_merge_audit_required is True
    assert state.closure_manifest.human_review_required is True
    assert state.closure_manifest.next_lot == 37
    assert state.closure_manifest.next_lot_status == "PLANNED_LOCKED"
    assert audit.state_output_checksum == state.output_checksum
    assert audit.validation_state == state.validation_state
    assert state.safety["trade_allowed"] is False
    assert state.safety["execution_allowed"] is False
    assert state.safety["approved_size"] == 0


def test_lot36_reference_freshness_gap_outage_audit_passes() -> None:
    state, _ = build_lot36_artifacts(ROOT, CODE_COMMIT)
    assert len(state.freshness_audits) == 1
    evidence = state.freshness_audits[0]
    assert evidence.status == "PASS"
    assert evidence.record_count == 3
    assert evidence.expected_interval_count == 3
    assert evidence.observed_interval_count == 3
    assert evidence.missing_interval_count == 0
    assert evidence.gap_count == 0
    assert evidence.outage_count == 0
    assert evidence.stale_record_count == 0
    assert evidence.freshness_bps == 10000
    assert evidence.freshness_age_us == 90_000


def test_lot36_gap_injection_blocks_freshness_audit_without_mutating_input() -> None:
    config, states = _quality_fixture()
    original = _records(config)
    before = copy.deepcopy(original)
    modified = [copy.deepcopy(original[0]), copy.deepcopy(original[2])]
    evidence = _audit(modified, states, "2026-08-06T19:18:00.100000Z")[0]
    assert evidence.status == "BLOCKED"
    assert evidence.missing_interval_count == 1
    assert evidence.gap_count == 1
    assert evidence.outage_count == 0
    assert original == before


def test_lot36_outage_boundary_is_detected_deterministically() -> None:
    config, states = _quality_fixture()
    records = copy.deepcopy(_records(config)[:2])
    third = copy.deepcopy(records[-1])
    third["record_id"] = "quality-candle-outage"
    third["event_time"] = "2026-08-06T19:19:00.000000Z"
    third["available_at"] = "2026-08-06T19:19:00.010000Z"
    third["sequence_id"] = 3
    records.append(third)
    evidence = _audit(records, states, "2026-08-06T19:19:00.100000Z", 1000)[0]
    assert evidence.status == "BLOCKED"
    assert evidence.gap_count == 1
    assert evidence.outage_count == 1
    assert evidence.missing_interval_count == 2


def test_lot36_stale_latest_record_blocks() -> None:
    config, states = _quality_fixture()
    evidence = _audit(
        copy.deepcopy(_records(config)),
        states,
        "2026-08-06T19:20:01.010001Z",
        121,
    )[0]
    assert evidence.status == "BLOCKED"
    assert evidence.stale_record_count == 1
    assert evidence.freshness_bps == 0
    assert "LATEST_DATA_STALE" in evidence.reason_codes


def test_lot36_rejects_future_availability_relative_to_reference() -> None:
    config, states = _quality_fixture()
    with pytest.raises(V3ClosureError, match="duration cannot run backwards"):
        _audit(
            copy.deepcopy(_records(config)),
            states,
            "2026-08-06T19:17:59.000000Z",
        )


def test_lot36_freshness_audit_is_input_order_independent() -> None:
    config, states = _quality_fixture()
    records = copy.deepcopy(_records(config))
    forward = _audit(records, states, "2026-08-06T19:18:00.100000Z")
    reverse = _audit(list(reversed(records)), states, "2026-08-06T19:18:00.100000Z")
    assert [item.to_dict() for item in forward] == [item.to_dict() for item in reverse]


@pytest.mark.parametrize(
    ("expected_type", "mutate"),
    [
        ("MISSING_INTERVAL", _remove_middle),
        ("DUPLICATE", _append_duplicate),
        ("OUT_OF_ORDER", _reverse),
        ("STALE_DATA", _make_stale),
        ("INVALID_OHLC", _break_ohlc),
        ("NEGATIVE_VOLUME", _negative_volume),
        ("IMPOSSIBLE_SPREAD", _impossible_spread),
        ("SCHEMA_DRIFT", _schema_drift),
    ],
)
def test_lot36_reaudit_detects_every_lot34_anomaly_family(
    expected_type: str, mutate: Mutation
) -> None:
    config = copy.deepcopy(load_json_object(QUALITY_CONFIG))
    records = _records(config)
    mutate(records)
    anomalies = detect_anomalies(config)
    assert expected_type in {item.anomaly_type for item in anomalies}


def test_lot36_any_quality_anomaly_forces_fail_closed_veto() -> None:
    config, states = _quality_fixture()
    mutated = copy.deepcopy(config)
    records = _records(mutated)
    records[0]["volume"] = "-1"
    anomalies = detect_anomalies(mutated)
    freshness = _audit(records, states, "2026-08-06T19:18:00.100000Z")
    veto = _closure_quality_veto(states, anomalies, freshness, 9500)
    assert veto.action == "BLOCK_ANALYSIS_OR_TRADING"
    assert "NEGATIVE_VOLUME" in veto.blocking_anomaly_types


def test_lot36_exact_replay_matches() -> None:
    replay = build_replay_evidence(ROOT, CODE_COMMIT)
    assert replay.replay_status == "REPLAY_MATCH"
    assert replay.match is True
    assert replay.run1_checksum == replay.run2_checksum


def test_lot36_state_serializes_deterministically() -> None:
    state, audit = build_lot36_artifacts(ROOT, CODE_COMMIT)
    first = json.dumps(state.to_dict(), sort_keys=True, separators=(",", ":"))
    second = json.dumps(state.to_dict(), sort_keys=True, separators=(",", ":"))
    assert first == second
    assert audit.state_output_checksum == state.output_checksum
