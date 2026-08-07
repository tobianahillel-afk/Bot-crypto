from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    file_checksum,
)
from crypto_quant_bot.data_governance.market_data_quality_engine import (
    LOT34_REASON_CODES,
    REQUIRED_RECORD_FIELDS,
    _build_lineage,
    _build_quality_states,
    _build_run_context,
    _build_veto,
    _consistency_components,
    _coverage_components,
    _duplicate_anomalies,
    _duration_us,
    _event_identity,
    _freshness_score,
    _missing_interval_anomalies,
    _ordering_anomalies,
    _quality_state_for_group,
    _record_key,
    _record_market_value_anomalies,
    _record_temporal_anomalies,
    _schema_anomalies,
    _validate_config_identity,
    _validate_config_limits,
    _validate_config_times,
    build_lot34_artifacts,
    persist_lot34_artifacts,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_models import (
    DataAnomalyV1,
    DataQualityStateV1,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_validation import (
    MarketDataQualityError,
    decimal_from_string,
    lot34_safety,
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_sha256,
    require_string_list,
    require_text,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/data_governance/market_data_quality_engine_v1.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
CODE_SHA = "1" * 40


def config_copy() -> dict[str, object]:
    return copy.deepcopy(CONFIG)


def assert_quality_error(message: str, func: object, *args: object) -> None:
    with pytest.raises(MarketDataQualityError, match=f"^{message}$"):
        func(*args)  # type: ignore[operator]


def test_duration_us_is_exact_for_positive_and_negative_deltas() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=1, seconds=2, microseconds=3)
    assert _duration_us(start, end) == 86_402_000_003
    assert _duration_us(end, start) == -86_402_000_003


def test_validation_helpers_have_exact_success_contracts() -> None:
    assert require_text("alpha", "field") == "alpha"
    assert require_identifier("Az09-_.:", "identifier") == "Az09-_.:"
    assert require_integer(7, "integer") == 7
    assert require_sha256("a" * 64, "hash") == "a" * 64
    assert require_git_sha("b" * 40) == "b" * 40
    assert parse_utc_timestamp("2026-08-06T19:15:00Z", "time") == datetime(
        2026, 8, 6, 19, 15, tzinfo=UTC
    )
    assert decimal_from_string("1.2300", "decimal").as_tuple().exponent == -4
    assert require_string_list(["a", "b"], "values") == ("a", "b")


def test_validation_helpers_have_exact_failure_contracts() -> None:
    assert_quality_error("field must be an explicit trimmed string", require_text, " x ", "field")
    assert_quality_error("identifier contains unsupported characters", require_identifier, "x/y", "identifier")
    assert_quality_error("integer must be an integer", require_integer, True, "integer")
    assert_quality_error("hash must be a lowercase sha256", require_sha256, "A" * 64, "hash")
    assert_quality_error("code_commit must be a lowercase 40-character git sha", require_git_sha, "A" * 40)
    assert_quality_error("time must be UTC and end with Z", parse_utc_timestamp, "2026-08-06T19:15:00+00:00", "time")
    assert_quality_error("decimal must be finite", decimal_from_string, "Infinity", "decimal")
    assert_quality_error("values must be a list", require_string_list, ("a",), "values")


def test_config_identity_validates_exact_schema_and_version() -> None:
    config = config_copy()
    _validate_config_identity(config)
    config["schema_version"] = "market-data-quality-config-v2"
    assert_quality_error("Lot 34 configuration schema changed", _validate_config_identity, config)
    config = config_copy()
    config["config_version"] = "other"
    assert_quality_error("Lot 34 configuration version changed", _validate_config_identity, config)
    config = config_copy()
    del config["lineage_id"]
    assert_quality_error("Lot 34 configuration fields differ", _validate_config_identity, config)


def test_config_times_validate_all_three_boundaries() -> None:
    config = config_copy()
    _validate_config_times(config)
    config["event_time"] = config["available_at"]
    config["generated_at"] = config["available_at"]
    _validate_config_times(config)
    config = config_copy()
    config["event_time"] = "2026-08-06T19:18:00.060000Z"
    assert_quality_error("Lot 34 configuration violates causal availability", _validate_config_times, config)
    config = config_copy()
    config["generated_at"] = "2026-08-06T19:18:00.040000Z"
    assert_quality_error("Lot 34 configuration violates causal availability", _validate_config_times, config)


def test_config_times_reject_invalid_timestamp_at_each_position() -> None:
    for field in ("event_time", "available_at", "generated_at"):
        config = config_copy()
        config[field] = "badZ"
        assert_quality_error(f"{field} is not a valid timestamp", _validate_config_times, config)


def test_config_limits_validate_each_bound_and_container() -> None:
    config = config_copy()
    _validate_config_limits(config)
    cases = [
        ("minimum_quality_bps", -1, "minimum_quality_bps must be >= 0"),
        ("max_staleness_seconds", -1, "max_staleness_seconds must be >= 0"),
        ("minimum_quality_bps", 10_001, "minimum_quality_bps cannot exceed 10000"),
    ]
    for field, value, message in cases:
        current = config_copy()
        current[field] = value
        assert_quality_error(message, _validate_config_limits, current)


def test_config_limits_validate_timeframe_map_entries() -> None:
    for value in ([], {}):
        config = config_copy()
        config["timeframe_seconds"] = value
        assert_quality_error("timeframe_seconds must be a non-empty object", _validate_config_limits, config)
    config = config_copy()
    config["timeframe_seconds"] = {"bad/id": 60}
    assert_quality_error("timeframe contains unsupported characters", _validate_config_limits, config)
    config = config_copy()
    config["timeframe_seconds"] = {"1m": 0}
    assert_quality_error("timeframe_seconds must be >= 1", _validate_config_limits, config)


def test_config_limits_validate_records_container() -> None:
    for value in ("records", []):
        config = config_copy()
        config["records"] = value
        assert_quality_error("Lot 34 requires at least one quality record", _validate_config_limits, config)


def test_record_key_and_event_identity_are_exact() -> None:
    record = config_copy()["records"][0]
    assert _record_key(record) == (
        "kraken-public-spot-metadata",
        "btc-eur-spot",
        "1m",
    )
    assert _event_identity(record) == (
        "kraken-public-spot-metadata",
        "btc-eur-spot",
        "1m",
        "2026-08-06T19:15:00.000000Z",
        1,
        0,
    )


def test_schema_anomaly_has_exact_contract() -> None:
    record = copy.deepcopy(config_copy()["records"][0])
    assert _schema_anomalies([record], "ohlc-quality-record-v1") == []
    record["extra"] = 1
    anomalies = _schema_anomalies([record], "ohlc-quality-record-v1")
    assert [item.to_dict() for item in anomalies] == [
        {
            "schema_version": "data-anomaly-v1",
            "anomaly_id": "lot34-schema_drift-0001",
            "anomaly_type": "SCHEMA_DRIFT",
            "severity": "ERROR",
            "record_ids": ["quality-candle-1"],
            "interval_start": "2026-08-06T19:15:00.000000Z",
            "interval_end": "2026-08-06T19:15:00.000000Z",
            "correction_permitted": False,
            "quarantined": True,
            "reason_code": "DQ_SCHEMA_DRIFT",
        }
    ]


def test_duplicate_identity_uses_every_identity_component() -> None:
    base = copy.deepcopy(config_copy()["records"][0])
    duplicate = copy.deepcopy(base)
    duplicate["record_id"] = "duplicate"
    anomalies = _duplicate_anomalies([base, duplicate], 7)
    assert anomalies[0].anomaly_id == "lot34-duplicate-0008"
    assert anomalies[0].record_ids == ("quality-candle-1", "duplicate")
    for field, value in (
        ("source_id", "other-source"),
        ("instrument_id", "eth-eur-spot"),
        ("timeframe", "5m"),
        ("event_time", "2026-08-06T19:15:01.000000Z"),
        ("sequence_id", 2),
        ("revision_id", 1),
    ):
        variant = copy.deepcopy(duplicate)
        variant[field] = value
        assert _duplicate_anomalies([base, variant], 0) == []


def test_ordering_detects_event_sequence_and_revision_regressions() -> None:
    first = copy.deepcopy(config_copy()["records"][0])
    later = copy.deepcopy(first)
    later.update(record_id="later", event_time="2026-08-06T19:16:00.000000Z", sequence_id=2)
    assert _ordering_anomalies([first, later], 0) == []
    anomaly = _ordering_anomalies([later, first], 3)[0]
    assert anomaly.anomaly_id == "lot34-out_of_order-0004"
    assert anomaly.record_ids == ("later", "quality-candle-1")
    same_time = copy.deepcopy(later)
    same_time.update(record_id="seq-back", sequence_id=1)
    assert _ordering_anomalies([later, same_time], 0)[0].record_ids == ("later", "seq-back")
    revision = copy.deepcopy(later)
    revision.update(record_id="revision-2", revision_id=2)
    revision_back = copy.deepcopy(revision)
    revision_back.update(record_id="revision-1", revision_id=1)
    assert _ordering_anomalies([revision, revision_back], 0)[0].record_ids == (
        "revision-2",
        "revision-1",
    )


def test_ordering_is_isolated_per_market_group() -> None:
    newer = copy.deepcopy(config_copy()["records"][1])
    older_other = copy.deepcopy(config_copy()["records"][0])
    older_other["source_id"] = "other-source"
    assert _ordering_anomalies([newer, older_other], 0) == []


def test_missing_interval_uses_strict_microsecond_boundary() -> None:
    first = copy.deepcopy(config_copy()["records"][0])
    exact = copy.deepcopy(first)
    exact.update(record_id="exact", event_time="2026-08-06T19:16:00.000000Z")
    assert _missing_interval_anomalies([first, exact], {"1m": 60}, 0) == []
    late = copy.deepcopy(exact)
    late.update(record_id="late", event_time="2026-08-06T19:16:00.000001Z")
    anomaly = _missing_interval_anomalies([first, late], {"1m": 60}, 2)[0]
    assert anomaly.anomaly_id == "lot34-missing_interval-0003"
    assert anomaly.record_ids == ("quality-candle-1", "late")


def test_temporal_quality_uses_strict_staleness_boundary() -> None:
    record = copy.deepcopy(config_copy()["records"][0])
    generated = datetime(2026, 8, 6, 19, 18, 0, 100_000, tzinfo=UTC)
    record["available_at"] = "2026-08-06T19:15:59.100000Z"
    assert _record_temporal_anomalies(record, generated, 121, 0) == []
    record["available_at"] = "2026-08-06T19:15:59.099999Z"
    anomaly = _record_temporal_anomalies(record, generated, 121, 5)[0]
    assert anomaly.anomaly_id == "lot34-stale_data-0006"
    assert anomaly.reason_code == "DQ_STALE_DATA"


def test_market_value_checks_each_ohlc_relation() -> None:
    base = copy.deepcopy(config_copy()["records"][0])
    assert _record_market_value_anomalies(base, 0) == []
    variants = (
        ("high", "56800", "INVALID_OHLC"),
        ("high", "57010", "INVALID_OHLC"),
        ("low", "57060", "INVALID_OHLC"),
        ("volume", "-0.0001", "NEGATIVE_VOLUME"),
        ("bid", "57051", "IMPOSSIBLE_SPREAD"),
        ("ask", "-1", "IMPOSSIBLE_SPREAD"),
    )
    for field, value, expected in variants:
        record = copy.deepcopy(base)
        record[field] = value
        assert expected in {item.anomaly_type for item in _record_market_value_anomalies(record, 0)}


def test_market_value_boundary_values_are_allowed() -> None:
    record = copy.deepcopy(config_copy()["records"][0])
    record.update(high="57050.00", low="57000.00", volume="0", bid="0", ask="0")
    assert _record_market_value_anomalies(record, 0) == []


def test_coverage_components_are_exact_for_full_single_and_gapped_data() -> None:
    records = copy.deepcopy(config_copy()["records"])
    assert _coverage_components(records, "1m", CONFIG) == (3, 3, 10_000)
    assert _coverage_components(records[:1], "1m", CONFIG) == (1, 1, 10_000)
    assert _coverage_components([records[0], records[2]], "1m", CONFIG) == (3, 2, 6666)


def test_freshness_score_is_exact_and_uses_newest_available_record() -> None:
    records = copy.deepcopy(config_copy()["records"])
    assert _freshness_score(records, CONFIG) == 10_000
    config = config_copy()
    config["records"][2]["available_at"] = "2026-08-06T19:17:00.000000Z"
    config["records"][1]["available_at"] = "2026-08-06T19:16:59.000000Z"
    assert _freshness_score(config["records"], config) == 5042
    assert _freshness_score([], config) == 0


def test_consistency_components_count_only_group_anomalies() -> None:
    records = copy.deepcopy(config_copy()["records"])
    assert _consistency_components(records, ()) == (10_000, 10_000, 0)
    drifted = copy.deepcopy(records)
    drifted[0]["extra"] = 1
    foreign = DataAnomalyV1(
        "foreign", "STALE_DATA", "ERROR", ("foreign-record",),
        "2026-08-06T19:15:00Z", "2026-08-06T19:15:00Z", False, True, "DQ_STALE_DATA"
    )
    local = DataAnomalyV1(
        "local", "STALE_DATA", "ERROR", ("quality-candle-2",),
        "2026-08-06T19:16:00Z", "2026-08-06T19:16:00Z", False, True, "DQ_STALE_DATA"
    )
    assert _consistency_components(drifted, (foreign, local)) == (6666, 8750, 1)


def test_quality_state_has_exact_healthy_contract() -> None:
    records = copy.deepcopy(config_copy()["records"])
    key = _record_key(records[0])
    state = _quality_state_for_group(key, records, (), CONFIG)
    assert state.to_dict() == {
        "schema_version": "data-quality-state-v1",
        "source_id": "kraken-public-spot-metadata",
        "instrument_id": "btc-eur-spot",
        "timeframe": "1m",
        "record_count": 3,
        "expected_interval_count": 3,
        "observed_interval_count": 3,
        "anomaly_count": 0,
        "coverage_bps": 10000,
        "freshness_bps": 10000,
        "completeness_bps": 10000,
        "consistency_bps": 10000,
        "quality_score_bps": 10000,
        "status": "PASS",
    }


def test_veto_uses_minimum_group_score_and_sorted_blocking_types() -> None:
    states = _build_quality_states(CONFIG, ())
    lower = replace(states[0], source_id="other-source", quality_score_bps=9700)
    veto = _build_veto((*states, lower), (), 9500)
    assert veto.observed_quality_bps == 9700
    assert veto.action == "ALLOW_ANALYSIS"
    anomalies = (
        DataAnomalyV1("z", "STALE_DATA", "ERROR", ("r",), "2026-08-06T19:15:00Z", "2026-08-06T19:15:00Z", False, True, "DQ_STALE_DATA"),
        DataAnomalyV1("a", "DUPLICATE", "ERROR", ("r",), "2026-08-06T19:15:00Z", "2026-08-06T19:15:00Z", False, True, "DQ_DUPLICATE_EVENT"),
    )
    blocked = _build_veto(states, anomalies, 9500)
    assert blocked.blocking_anomaly_types == ("DUPLICATE", "STALE_DATA")
    assert blocked.reason_codes == ("DATA_QUALITY_ANOMALY_PRESENT",)


def test_run_context_and_lineage_are_exact() -> None:
    run_context = _build_run_context(CONFIG, CODE_SHA)
    assert run_context.to_dict() == {
        "schema_version": "run-context-v1",
        "run_id": "lot34-reference-run",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "config_version": "lot34-market-data-quality-config-v1",
        "code_commit": CODE_SHA,
        "correlation_id": "lot34-reference-correlation",
    }
    lineage = _build_lineage(ROOT, CONFIG)
    assert lineage.canonical_time_collection_checksum == file_checksum(
        ROOT / "data/audit/canonical_time_envelopes_lot33.json"
    )
    assert lineage.lot33_state_checksum == "4bb5f8df3b49a8a54b6a932a37d35a4575edc63f897c55e88df90dfaf000f450"
    assert lineage.lot33_audit_checksum == "73afe6a1d7dc73565d76f7e6d5f7c96cbc4fdecc6dadce88c2e88edb1ca365ad"


def test_build_artifacts_have_exact_reason_metrics_safety_and_checksums() -> None:
    state, audit = build_lot34_artifacts(ROOT, CODE_SHA)
    assert state.reason_codes == LOT34_REASON_CODES
    assert state.metrics.to_dict()["lot_34_records_processed_total"] == 3
    assert state.safety == lot34_safety()
    assert canonical_checksum(state.payload_without_checksum()) == state.output_checksum
    assert audit.state_output_checksum == state.output_checksum
    assert audit.config_checksum == file_checksum(CONFIG_PATH)
    assert canonical_checksum(audit.payload_without_checksum()) == audit.audit_checksum


def test_persistence_writes_all_five_exact_payloads(tmp_path: Path) -> None:
    state, audit = build_lot34_artifacts(ROOT, CODE_SHA)
    persist_lot34_artifacts(tmp_path, state, audit)
    expected = {
        "market_data_quality_engine_lot34.json": state.to_dict(),
        "market_data_quality_engine_audit_lot34.json": audit.to_dict(),
        "data_quality_states_lot34.json": {
            "schema_version": "data-quality-state-collection-v1",
            "records": [item.to_dict() for item in state.quality_states],
        },
        "data_anomalies_lot34.json": {
            "schema_version": "data-anomaly-collection-v1",
            "records": [item.to_dict() for item in state.anomalies],
        },
        "data_quality_veto_lot34.json": state.veto.to_dict(),
    }
    for filename, payload in expected.items():
        path = tmp_path / "data/audit" / filename
        assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_required_record_field_set_is_exact() -> None:
    assert REQUIRED_RECORD_FIELDS == {
        "record_id", "source_id", "instrument_id", "timeframe", "event_time",
        "available_at", "sequence_id", "revision_id", "source_schema_version",
        "open", "high", "low", "close", "volume", "bid", "ask",
    }
