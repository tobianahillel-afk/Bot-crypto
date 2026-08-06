from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance import (
    build_lot33_artifacts,
    persist_lot33_artifacts,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_models import (
    CanonicalTimeEnvelopeV1,
    ClockHealthStateV1,
    Lot33MetricsV1,
    Lot33RunContextV1,
    RawTimestampEnvelopeV1,
    TimestampClockTimezoneGovernanceStateV1,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_validation import (
    TimestampGovernanceError,
    canonical_utc,
    duration_us,
    validate_source_timezone,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "a" * 40
INPUT_PATHS = (
    "config/data_governance/timestamp_clock_timezone_governance_v1.json",
    "data/audit/lot33_v3_entry_gate.json",
    "data/audit/instrument_registry_lot32.json",
    "data/audit/instrument_symbol_and_contract_normalization_lot32.json",
    "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json",
)


def copy_inputs(destination: Path) -> None:
    for relative in INPUT_PATHS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def mutate_json(root: Path, relative: str, mutation: object) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert callable(mutation)
    mutation(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_raw(**overrides: object) -> RawTimestampEnvelopeV1:
    values: dict[str, object] = {
        "record_id": "test-record",
        "instrument_id": "btc-eur-spot",
        "source_id": "kraken-public-spot-metadata",
        "raw_timestamp": "2026-08-06T19:15:00.100000Z",
        "source_timezone": "UTC",
        "timestamp_precision": "MICROSECONDS",
        "source_time": "2026-08-06T19:15:00.100000Z",
        "exchange_time": "2026-08-06T19:15:00.101000Z",
        "event_time": "2026-08-06T19:15:00.101000Z",
        "receive_time": "2026-08-06T19:15:00.151000Z",
        "process_time": "2026-08-06T19:15:00.171000Z",
        "available_at": "2026-08-06T19:15:00.171000Z",
        "usable_from": "2026-08-06T19:15:00.171000Z",
        "monotonic_time": 1,
        "clock_domain": "PROCESS_MONOTONIC_NS",
        "sequence_id": 1,
        "revision_id": 0,
    }
    values.update(overrides)
    return RawTimestampEnvelopeV1(**values)  # type: ignore[arg-type]


def test_lot33_build_is_deterministic_and_healthy() -> None:
    first_state, first_audit = build_lot33_artifacts(ROOT, VALID_SHA)
    second_state, second_audit = build_lot33_artifacts(ROOT, VALID_SHA)
    assert first_state.to_dict() == second_state.to_dict()
    assert first_audit.to_dict() == second_audit.to_dict()
    assert first_state.clock_health.status == "HEALTHY"
    assert first_state.clock_health.observed_clock_drift_us == 1000
    assert first_state.clock_health.observed_out_of_order_delay_us == 201000
    assert first_state.clock_health.observed_total_latency_us == 420000
    assert first_audit.record_count == 3
    assert first_audit.out_of_order_record_count == 1


def test_lot33_preserves_raw_timezone_precision_and_canonicalizes_utc() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    by_record = {item.raw.record_id: item for item in state.canonical_envelopes}
    paris = by_record["bitstamp-record-1"]
    assert paris.raw.raw_timestamp == "2026-08-06T21:15:00.100000+02:00"
    assert paris.raw.source_timezone == "Europe/Paris"
    assert paris.raw.timestamp_precision == "MICROSECONDS"
    assert paris.source_time_utc == "2026-08-06T19:15:00.100000Z"
    assert paris.event_time_utc == "2026-08-06T19:15:00.101000Z"
    assert paris.clock_drift_us == 1000


def test_equal_event_times_use_sequence_id_and_late_event_is_measured() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    records = state.canonical_envelopes
    assert [item.raw.record_id for item in records] == [
        "kraken-record-3-late",
        "bitstamp-record-1",
        "coinbase-record-2",
    ]
    assert records[1].event_time_utc == records[2].event_time_utc
    assert records[1].raw.sequence_id == 1
    assert records[2].raw.sequence_id == 2
    assert records[0].out_of_order_delay_us == 201000
    assert records[1].out_of_order_delay_us == 0
    assert records[2].out_of_order_delay_us == 0


def test_latency_components_are_exact_integer_microseconds() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    by_record = {item.raw.record_id: item for item in state.canonical_envelopes}
    assert by_record["bitstamp-record-1"].transport_latency_us == 50000
    assert by_record["bitstamp-record-1"].processing_latency_us == 20000
    assert by_record["bitstamp-record-1"].total_latency_us == 70000
    assert by_record["coinbase-record-2"].total_latency_us == 80000
    assert by_record["kraken-record-3-late"].total_latency_us == 420000
    assert duration_us(
        "2026-08-06T19:15:00.100000Z",
        "2026-08-06T19:15:00.100001Z",
        "one_microsecond",
    ) == 1


def test_persistence_writes_three_linked_artifacts(tmp_path: Path) -> None:
    state, audit = build_lot33_artifacts(ROOT, VALID_SHA)
    persist_lot33_artifacts(tmp_path, state, audit)
    persisted_state = json.loads(
        (tmp_path / "data/audit/timestamp_clock_and_timezone_governance_lot33.json").read_text()
    )
    persisted_audit = json.loads(
        (tmp_path / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json").read_text()
    )
    collection = json.loads(
        (tmp_path / "data/audit/canonical_time_envelopes_lot33.json").read_text()
    )
    assert persisted_state == state.to_dict()
    assert persisted_audit == audit.to_dict()
    assert collection["records"] == persisted_state["canonical_envelopes"]
    assert persisted_audit["state_output_checksum"] == persisted_state["output_checksum"]


def test_timezone_naive_unknown_or_wrong_offset_is_rejected() -> None:
    with pytest.raises(TimestampGovernanceError, match="timezone"):
        canonical_utc("2026-08-06T19:15:00.100000", "MICROSECONDS", "event_time")
    with pytest.raises(TimestampGovernanceError, match="unknown"):
        validate_source_timezone("2026-08-06T19:15:00.100000Z", "Mars/Olympus")
    with pytest.raises(TimestampGovernanceError, match="offset"):
        validate_source_timezone("2026-12-06T21:15:00.100000+02:00", "Europe/Paris")


def test_dst_fold_offsets_are_explicit_and_deterministic() -> None:
    validate_source_timezone("2026-10-25T02:30:00.000000+02:00", "Europe/Paris")
    validate_source_timezone("2026-10-25T02:30:00.000000+01:00", "Europe/Paris")
    assert canonical_utc(
        "2026-10-25T02:30:00.000000+02:00", "MICROSECONDS", "fold_early"
    ) == "2026-10-25T00:30:00.000000Z"
    assert canonical_utc(
        "2026-10-25T02:30:00.000000+01:00", "MICROSECONDS", "fold_late"
    ) == "2026-10-25T01:30:00.000000Z"


def test_precision_and_raw_source_identity_are_strict() -> None:
    with pytest.raises(TimestampGovernanceError, match="precision"):
        canonical_utc("2026-08-06T19:15:00.100Z", "MICROSECONDS", "event_time")
    with pytest.raises(TimestampGovernanceError, match="preserve source_time"):
        make_raw(source_time="2026-08-06T19:15:00.101000Z")


def test_monotonic_clock_contract_is_explicit() -> None:
    assert make_raw(monotonic_time=None, clock_domain="WALL_CLOCK_ONLY").monotonic_time is None
    with pytest.raises(TimestampGovernanceError, match="WALL_CLOCK_ONLY"):
        make_raw(monotonic_time=None, clock_domain="PROCESS_MONOTONIC_NS")
    with pytest.raises(TimestampGovernanceError, match="PROCESS_MONOTONIC_NS"):
        make_raw(monotonic_time=1, clock_domain="WALL_CLOCK_ONLY")


def test_causal_availability_and_negative_latency_are_rejected() -> None:
    raw = make_raw()
    with pytest.raises(TimestampGovernanceError, match="causal availability"):
        CanonicalTimeEnvelopeV1(
            raw=raw,
            source_time_utc=raw.source_time,
            exchange_time_utc=raw.exchange_time,
            event_time_utc=raw.event_time,
            receive_time_utc=raw.receive_time,
            process_time_utc=raw.process_time,
            available_at_utc="2026-08-06T19:15:00.160000Z",
            usable_from_utc=raw.usable_from,
            clock_drift_us=1000,
            transport_latency_us=50000,
            processing_latency_us=20000,
            total_latency_us=70000,
            out_of_order_delay_us=0,
            validation_state="VALIDATED_TEMPORAL_ONLY",
        )
    with pytest.raises(TimestampGovernanceError, match="negative"):
        duration_us(raw.receive_time, raw.event_time, "negative")


def test_threshold_exceedance_produces_degraded_not_permission(tmp_path: Path) -> None:
    copy_inputs(tmp_path)

    def lower_threshold(payload: dict[str, object]) -> None:
        thresholds = payload["thresholds"]
        assert isinstance(thresholds, dict)
        thresholds["max_total_latency_us"] = 1000

    mutate_json(
        tmp_path,
        "config/data_governance/timestamp_clock_timezone_governance_v1.json",
        lower_threshold,
    )
    state, audit = build_lot33_artifacts(tmp_path, VALID_SHA)
    assert state.clock_health.status == "DEGRADED"
    assert state.clock_health.reason_codes == ("CLOCK_THRESHOLD_EXCEEDED",)
    assert audit.clock_health_status == "DEGRADED"
    assert state.safety["trade_allowed"] is False
    assert state.safety["execution_allowed"] is False


def test_duplicate_unknown_and_tampered_inputs_fail_closed(tmp_path: Path) -> None:
    copy_inputs(tmp_path)

    def duplicate(payload: dict[str, object]) -> None:
        records = payload["records"]
        assert isinstance(records, list)
        records[1]["record_id"] = records[0]["record_id"]

    mutate_json(tmp_path, INPUT_PATHS[0], duplicate)
    with pytest.raises(TimestampGovernanceError, match="unique"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)

    def unknown_source(payload: dict[str, object]) -> None:
        records = payload["records"]
        assert isinstance(records, list)
        records[0]["source_id"] = "unknown-source"

    mutate_json(tmp_path, INPUT_PATHS[0], unknown_source)
    with pytest.raises(TimestampGovernanceError, match="unknown instrument or source"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)

    def tamper_gate(payload: dict[str, object]) -> None:
        payload["target_lot"] = 34

    mutate_json(tmp_path, INPUT_PATHS[1], tamper_gate)
    with pytest.raises(TimestampGovernanceError, match="checksum"):
        build_lot33_artifacts(tmp_path, VALID_SHA)


def test_state_metrics_context_and_health_contracts_are_strict() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    with pytest.raises(TimestampGovernanceError, match="ordered"):
        replace(state, canonical_envelopes=tuple(reversed(state.canonical_envelopes)))
    with pytest.raises(TimestampGovernanceError, match="metrics"):
        Lot33MetricsV1(3, -1, 1, 0)
    with pytest.raises(TimestampGovernanceError, match="status"):
        ClockHealthStateV1("UNKNOWN", 1, 1, 1, 0, 0, 0, ("UNKNOWN",))
    with pytest.raises(TimestampGovernanceError, match="runtime"):
        Lot33RunContextV1("run", "LIVE", "config", VALID_SHA, "correlation")
    unsafe = dict(state.safety)
    unsafe["trade_allowed"] = True
    with pytest.raises(TimestampGovernanceError, match="fail-closed"):
        replace(state, safety=unsafe)


def test_lot33_schemas_are_strict() -> None:
    names = (
        "raw_timestamp_envelope_v1.schema.json",
        "canonical_time_envelope_v1.schema.json",
        "timestamp_clock_timezone_governance_state_v1.schema.json",
        "timestamp_clock_timezone_governance_audit_v1.schema.json",
    )
    schemas = {
        name: json.loads((ROOT / "contracts/schemas" / name).read_text(encoding="utf-8"))
        for name in names
    }
    assert all(schema["additionalProperties"] is False for schema in schemas.values())
    state_schema = schemas["timestamp_clock_timezone_governance_state_v1.schema.json"]
    assert state_schema["properties"]["trade_allowed"]["const"] is False
    assert state_schema["properties"]["approved_size"]["const"] == 0
    assert state_schema["properties"]["canonical_envelopes"]["items"]["$ref"] == (
        "canonical_time_envelope_v1.schema.json"
    )
