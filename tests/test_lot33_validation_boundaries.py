from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

import crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance import (
    build_lot33_artifacts,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_models import (
    CanonicalTimeEnvelopeV1,
    ClockHealthStateV1,
    Lot33LineageEnvelopeV1,
    RawTimestampEnvelopeV1,
    TimestampClockTimezoneGovernanceAuditV1,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_validation import (
    TimestampGovernanceError,
    canonical_utc,
    require_git_sha,
    require_identifier,
    require_sha256,
    signed_duration_us,
    validate_precision,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "b" * 40
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


def load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_raw(**overrides: object) -> RawTimestampEnvelopeV1:
    values: dict[str, object] = {
        "record_id": "boundary-record",
        "instrument_id": "btc-eur-spot",
        "source_id": "kraken-public-spot-metadata",
        "raw_timestamp": "2026-08-06T19:15:00.100000Z",
        "source_timezone": "UTC",
        "timestamp_precision": "MICROSECONDS",
        "source_time": "2026-08-06T19:15:00.100000Z",
        "exchange_time": None,
        "event_time": "2026-08-06T19:15:00.101000Z",
        "receive_time": "2026-08-06T19:15:00.151000Z",
        "process_time": "2026-08-06T19:15:00.171000Z",
        "available_at": "2026-08-06T19:15:00.171000Z",
        "usable_from": "2026-08-06T19:15:00.171000Z",
        "monotonic_time": None,
        "clock_domain": "WALL_CLOCK_ONLY",
        "sequence_id": 0,
        "revision_id": 0,
    }
    values.update(overrides)
    return RawTimestampEnvelopeV1(**values)  # type: ignore[arg-type]


def test_seconds_and_milliseconds_are_canonicalized_exactly() -> None:
    assert canonical_utc("2026-08-06T21:15:00+02:00", "SECONDS", "seconds") == (
        "2026-08-06T19:15:00Z"
    )
    assert canonical_utc("2026-08-06T21:15:00.123+02:00", "MILLISECONDS", "millis") == (
        "2026-08-06T19:15:00.123Z"
    )
    with pytest.raises(TimestampGovernanceError, match="unknown"):
        validate_precision("2026-08-06T19:15:00Z", "NANOSECONDS")


def test_identifiers_and_hashes_are_strict() -> None:
    require_identifier("canonical-id", "id")
    require_sha256("a" * 64, "checksum")
    require_git_sha("b" * 40)
    with pytest.raises(TimestampGovernanceError, match="canonical lowercase"):
        require_identifier("Not_Canonical", "id")
    with pytest.raises(TimestampGovernanceError, match="sha256"):
        require_sha256("A" * 64, "checksum")
    with pytest.raises(TimestampGovernanceError, match="git sha"):
        require_git_sha("g" * 40)


def test_signed_drift_can_be_negative_but_latency_cannot() -> None:
    assert signed_duration_us(
        "2026-08-06T19:15:00.101000Z",
        "2026-08-06T19:15:00.100000Z",
    ) == -1000
    raw = make_raw()
    envelope = engine._normalize_raw(raw, 0)
    assert envelope.exchange_time_utc is None
    assert envelope.clock_drift_us == 0


def test_gate_scope_and_safety_changes_are_rejected(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    gate_path = tmp_path / INPUT_PATHS[1]
    gate = load(gate_path)
    gate["human_decision"] = "UNKNOWN"
    payload = dict(gate)
    payload.pop("output_checksum")
    gate["output_checksum"] = canonical_checksum(payload)
    write(gate_path, gate)
    with pytest.raises(TimestampGovernanceError, match="does not authorize"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    gate = load(gate_path)
    safety = gate["safety"]
    assert isinstance(safety, dict)
    safety["trade_allowed"] = True
    payload = dict(gate)
    payload.pop("output_checksum")
    gate["output_checksum"] = canonical_checksum(payload)
    write(gate_path, gate)
    with pytest.raises(TimestampGovernanceError, match="safety"):
        build_lot33_artifacts(tmp_path, VALID_SHA)


def test_configuration_schema_version_fields_and_causality_are_strict(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    config_path = tmp_path / INPUT_PATHS[0]
    config = load(config_path)
    config["unexpected"] = True
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="fields differ"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    config["schema_version"] = "v2"
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="schema"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    config["config_version"] = "wrong"
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="version"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    config["event_time"] = "2026-08-06T19:15:01.000000Z"
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="causal availability"):
        build_lot33_artifacts(tmp_path, VALID_SHA)


def test_raw_fields_nullable_types_precision_and_timezone_are_strict(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    config_path = tmp_path / INPUT_PATHS[0]
    config = load(config_path)
    records = config["records"]
    assert isinstance(records, list)
    del records[0]["exchange_time"]
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="fields differ"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    records = config["records"]
    assert isinstance(records, list)
    records[0]["monotonic_time"] = "1"
    write(config_path, config)
    with pytest.raises(ValueError, match="integer"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    records = config["records"]
    assert isinstance(records, list)
    records[0]["receive_time"] = "2026-08-06T19:15:00.151Z"
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="precision"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    records = config["records"]
    assert isinstance(records, list)
    records[0]["source_timezone"] = "UTC"
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="offset"):
        build_lot33_artifacts(tmp_path, VALID_SHA)


def test_registry_and_record_collection_boundaries_fail_closed(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    registry_path = tmp_path / INPUT_PATHS[2]
    registry = load(registry_path)
    registry["instruments"] = []
    write(registry_path, registry)
    with pytest.raises(TimestampGovernanceError, match="one certified instrument"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config_path = tmp_path / INPUT_PATHS[0]
    config = load(config_path)
    config["records"] = []
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="timestamp records"):
        build_lot33_artifacts(tmp_path, VALID_SHA)


def test_threshold_field_types_and_each_degradation_path(tmp_path: Path) -> None:
    config_relative = INPUT_PATHS[0]
    for field in (
        "max_clock_drift_us",
        "max_out_of_order_delay_us",
        "max_total_latency_us",
    ):
        copy_inputs(tmp_path)
        config_path = tmp_path / config_relative
        config = load(config_path)
        thresholds = config["thresholds"]
        assert isinstance(thresholds, dict)
        thresholds[field] = 0
        write(config_path, config)
        state, _ = build_lot33_artifacts(tmp_path, VALID_SHA)
        assert state.clock_health.status == "DEGRADED"

    copy_inputs(tmp_path)
    config_path = tmp_path / config_relative
    config = load(config_path)
    thresholds = config["thresholds"]
    assert isinstance(thresholds, dict)
    thresholds["extra"] = 1
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="thresholds"):
        build_lot33_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)
    config = load(config_path)
    config["thresholds"] = []
    write(config_path, config)
    with pytest.raises(TimestampGovernanceError, match="object"):
        build_lot33_artifacts(tmp_path, VALID_SHA)


def test_lineage_health_audit_and_envelope_models_reject_invalid_values() -> None:
    with pytest.raises(TimestampGovernanceError, match="InstrumentRegistryV1"):
        Lot33LineageEnvelopeV1("lineage", "wrong.json", "a" * 64, "b" * 64, "c" * 64, "2026-08-06T19:15:00Z")
    with pytest.raises(TimestampGovernanceError, match="reason codes"):
        ClockHealthStateV1("HEALTHY", 1, 1, 1, 0, 0, 0, ())
    with pytest.raises(TimestampGovernanceError, match="audit counts"):
        TimestampClockTimezoneGovernanceAuditV1(
            VALID_SHA, "a" * 64, "b" * 64, "c" * 64, 0, 0,
            "HEALTHY", 0, 0, "VALIDATED_TEMPORAL_ONLY",
            {
                "analysis_only": True, "used_for_decision": False,
                "external_connectivity_allowed": False, "network_ingestion_allowed": False,
                "real_credentials_allowed": False, "signal_generation_allowed": False,
                "risk_approval_allowed": False, "order_routing_allowed": False,
                "trade_allowed": False, "execution_allowed": False, "approved_size": 0,
            },
            "d" * 64,
        )


def test_canonical_envelope_serialization_is_complete() -> None:
    raw = make_raw()
    envelope = CanonicalTimeEnvelopeV1(
        raw, raw.source_time, None, raw.event_time, raw.receive_time, raw.process_time,
        raw.available_at, raw.usable_from, 0, 50000, 20000, 70000, 0,
        "VALIDATED_TEMPORAL_ONLY",
    )
    assert envelope.to_dict() == {
        "schema_version": "canonical-time-envelope-v1",
        "raw": raw.to_dict(),
        "source_time_utc": raw.source_time,
        "exchange_time_utc": None,
        "event_time_utc": raw.event_time,
        "receive_time_utc": raw.receive_time,
        "process_time_utc": raw.process_time,
        "available_at_utc": raw.available_at,
        "usable_from_utc": raw.usable_from,
        "clock_drift_us": 0,
        "transport_latency_us": 50000,
        "processing_latency_us": 20000,
        "total_latency_us": 70000,
        "out_of_order_delay_us": 0,
        "validation_state": "VALIDATED_TEMPORAL_ONLY",
    }
