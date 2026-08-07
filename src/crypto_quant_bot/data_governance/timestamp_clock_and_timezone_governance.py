from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)
from .source_registry_validation import (
    fail_closed_safety,
    require_integer,
    require_object_list,
    require_string,
)
from .timestamp_clock_timezone_models import (
    CanonicalTimeEnvelopeV1,
    ClockHealthStateV1,
    Lot33LineageEnvelopeV1,
    Lot33MetricsV1,
    Lot33RunContextV1,
    RawTimestampEnvelopeV1,
    TimestampClockTimezoneGovernanceAuditV1,
    TimestampClockTimezoneGovernanceStateV1,
)
from .timestamp_clock_timezone_validation import (
    TimestampGovernanceError,
    canonical_utc,
    duration_us,
    parse_aware_timestamp,
    signed_duration_us,
    validate_precision,
    validate_source_timezone,
)

EXPECTED_GATE_CHECKSUM = "c6942ad174c4c8a32d54ac48ed9c00e0e443f3495cc657df0c2677a4dd4cb5cc"
CONFIG_FIELDS = {
    "schema_version", "config_version", "run_id", "correlation_id", "lineage_id",
    "event_time", "available_at", "generated_at", "thresholds", "records",
}
RECORD_FIELDS = {
    "record_id", "instrument_id", "source_id", "raw_timestamp", "source_timezone",
    "timestamp_precision", "source_time", "exchange_time", "event_time", "receive_time",
    "process_time", "available_at", "usable_from", "monotonic_time", "clock_domain",
    "sequence_id", "revision_id",
}


def _verify_gate(gate: dict[str, Any]) -> None:
    payload = dict(gate)
    checksum = payload.pop("output_checksum", None)
    if checksum != EXPECTED_GATE_CHECKSUM or canonical_checksum(payload) != checksum:
        raise TimestampGovernanceError("Lot 33 entry gate checksum mismatch")
    expected = {
        "gate_status": "GO_LOT33_IMPLEMENTATION_ENTRY",
        "target_lot": 33,
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "human_decision": "APPROVED_START_LOT33",
        "implementation_started": False,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise TimestampGovernanceError("Lot 33 entry gate does not authorize implementation")
    if gate.get("safety") != fail_closed_safety():
        raise TimestampGovernanceError("Lot 33 gate safety boundary changed")


def _validate_config(config: dict[str, Any]) -> None:
    if set(config) != CONFIG_FIELDS:
        raise TimestampGovernanceError("Lot 33 configuration fields differ")
    if config.get("schema_version") != "timestamp-clock-timezone-config-v1":
        raise TimestampGovernanceError("Lot 33 configuration schema changed")
    if config.get("config_version") != "lot33-timestamp-governance-config-v1":
        raise TimestampGovernanceError("Lot 33 configuration version changed")
    event = parse_aware_timestamp(require_string(config.get("event_time"), "event_time"), "event_time")
    available = parse_aware_timestamp(
        require_string(config.get("available_at"), "available_at"), "available_at"
    )
    generated = parse_aware_timestamp(
        require_string(config.get("generated_at"), "generated_at"), "generated_at"
    )
    if not event <= available <= generated:
        raise TimestampGovernanceError("Lot 33 configuration violates causal availability")


def _nullable_string(raw: dict[str, Any], field: str) -> str | None:
    if field not in raw:
        raise TimestampGovernanceError(f"{field} must be explicitly present")
    value = raw[field]
    if value is None:
        return None
    return require_string(value, field)


def _nullable_integer(raw: dict[str, Any], field: str) -> int | None:
    if field not in raw:
        raise TimestampGovernanceError(f"{field} must be explicitly present")
    value = raw[field]
    if value is None:
        return None
    return require_integer(value, field)


def _validate_raw_metadata(raw: RawTimestampEnvelopeV1) -> None:
    validate_source_timezone(raw.raw_timestamp, raw.source_timezone)
    values = (
        ("source_time", raw.source_time),
        ("event_time", raw.event_time),
        ("receive_time", raw.receive_time),
        ("process_time", raw.process_time),
        ("available_at", raw.available_at),
        ("usable_from", raw.usable_from),
    )
    for field, value in values:
        validate_precision(value, raw.timestamp_precision, field)
    if raw.exchange_time is not None:
        validate_precision(raw.exchange_time, raw.timestamp_precision, "exchange_time")


def _build_raw(raw: dict[str, Any]) -> RawTimestampEnvelopeV1:
    if set(raw) != RECORD_FIELDS:
        raise TimestampGovernanceError("raw timestamp envelope fields differ")
    envelope = RawTimestampEnvelopeV1(
        record_id=require_string(raw.get("record_id"), "record_id"),
        instrument_id=require_string(raw.get("instrument_id"), "instrument_id"),
        source_id=require_string(raw.get("source_id"), "source_id"),
        raw_timestamp=require_string(raw.get("raw_timestamp"), "raw_timestamp"),
        source_timezone=require_string(raw.get("source_timezone"), "source_timezone"),
        timestamp_precision=require_string(raw.get("timestamp_precision"), "timestamp_precision"),
        source_time=require_string(raw.get("source_time"), "source_time"),
        exchange_time=_nullable_string(raw, "exchange_time"),
        event_time=require_string(raw.get("event_time"), "event_time"),
        receive_time=require_string(raw.get("receive_time"), "receive_time"),
        process_time=require_string(raw.get("process_time"), "process_time"),
        available_at=require_string(raw.get("available_at"), "available_at"),
        usable_from=require_string(raw.get("usable_from"), "usable_from"),
        monotonic_time=_nullable_integer(raw, "monotonic_time"),
        clock_domain=require_string(raw.get("clock_domain"), "clock_domain"),
        sequence_id=require_integer(raw.get("sequence_id"), "sequence_id"),
        revision_id=require_integer(raw.get("revision_id"), "revision_id"),
    )
    _validate_raw_metadata(envelope)
    return envelope


def _allowed_sources(registry: dict[str, Any]) -> tuple[str, set[str]]:
    instruments = registry.get("instruments")
    if not isinstance(instruments, list) or len(instruments) != 1:
        raise TimestampGovernanceError("Lot 33 requires one certified instrument")
    instrument = instruments[0]
    instrument_id = require_string(instrument.get("instrument_id"), "instrument_id")
    aliases = require_object_list(instrument.get("aliases"), "aliases")
    source_ids = {require_string(alias.get("source_id"), "source_id") for alias in aliases}
    return instrument_id, source_ids


def _normalize_raw(raw: RawTimestampEnvelopeV1, out_of_order_us: int) -> CanonicalTimeEnvelopeV1:
    precision = raw.timestamp_precision
    source_utc = canonical_utc(raw.source_time, precision, "source_time")
    exchange_utc = (
        None if raw.exchange_time is None else canonical_utc(raw.exchange_time, precision, "exchange_time")
    )
    event_utc = canonical_utc(raw.event_time, precision, "event_time")
    receive_utc = canonical_utc(raw.receive_time, precision, "receive_time")
    process_utc = canonical_utc(raw.process_time, precision, "process_time")
    available_utc = canonical_utc(raw.available_at, precision, "available_at")
    usable_utc = canonical_utc(raw.usable_from, precision, "usable_from")
    drift = 0 if exchange_utc is None else signed_duration_us(source_utc, exchange_utc)
    return CanonicalTimeEnvelopeV1(
        raw=raw,
        source_time_utc=source_utc,
        exchange_time_utc=exchange_utc,
        event_time_utc=event_utc,
        receive_time_utc=receive_utc,
        process_time_utc=process_utc,
        available_at_utc=available_utc,
        usable_from_utc=usable_utc,
        clock_drift_us=drift,
        transport_latency_us=duration_us(event_utc, receive_utc, "transport_latency"),
        processing_latency_us=duration_us(receive_utc, process_utc, "processing_latency"),
        total_latency_us=duration_us(event_utc, process_utc, "total_latency"),
        out_of_order_delay_us=out_of_order_us,
        validation_state="VALIDATED_TEMPORAL_ONLY",
    )


def _out_of_order_delays(records: tuple[RawTimestampEnvelopeV1, ...]) -> tuple[int, ...]:
    delays: list[int] = []
    maximum: datetime | None = None
    for record in records:
        current = parse_aware_timestamp(record.event_time, "event_time").astimezone(UTC)
        if maximum is None or current >= maximum:
            delays.append(0)
            maximum = current
            continue
        delta = maximum - current
        delays.append(delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds)
    return tuple(delays)


def _build_health(
    envelopes: tuple[CanonicalTimeEnvelopeV1, ...],
    thresholds: dict[str, Any],
) -> ClockHealthStateV1:
    if not envelopes:
        raise TimestampGovernanceError("Lot 33 requires at least one timestamp record")
    max_drift = require_integer(thresholds.get("max_clock_drift_us"), "max_clock_drift_us")
    max_ooo = require_integer(
        thresholds.get("max_out_of_order_delay_us"), "max_out_of_order_delay_us"
    )
    max_latency = require_integer(thresholds.get("max_total_latency_us"), "max_total_latency_us")
    expected_fields = {
        "max_clock_drift_us", "max_out_of_order_delay_us", "max_total_latency_us"
    }
    if min(max_drift, max_ooo, max_latency) < 0 or set(thresholds) != expected_fields:
        raise TimestampGovernanceError("Lot 33 thresholds are invalid")
    observed_drift = max(abs(item.clock_drift_us) for item in envelopes)
    observed_ooo = max(item.out_of_order_delay_us for item in envelopes)
    observed_latency = max(item.total_latency_us for item in envelopes)
    exceeded = (
        observed_drift > max_drift
        or observed_ooo > max_ooo
        or observed_latency > max_latency
    )
    status = "DEGRADED" if exceeded else "HEALTHY"
    reasons = ("CLOCK_THRESHOLD_EXCEEDED",) if exceeded else ("CLOCK_THRESHOLDS_SATISFIED",)
    return ClockHealthStateV1(
        status, max_drift, max_ooo, max_latency,
        observed_drift, observed_ooo, observed_latency, reasons,
    )


def _build_run_context(config: dict[str, Any], code_commit: str) -> Lot33RunContextV1:
    return Lot33RunContextV1(
        require_string(config.get("run_id"), "run_id"),
        "DATA_GOVERNANCE_ONLY",
        require_string(config.get("config_version"), "config_version"),
        code_commit,
        require_string(config.get("correlation_id"), "correlation_id"),
    )


def _build_lineage(config: dict[str, Any], root: Path) -> Lot33LineageEnvelopeV1:
    return Lot33LineageEnvelopeV1(
        require_string(config.get("lineage_id"), "lineage_id"),
        "data/audit/instrument_registry_lot32.json",
        file_checksum(root / "data/audit/instrument_registry_lot32.json"),
        file_checksum(root / "data/audit/instrument_symbol_and_contract_normalization_lot32.json"),
        file_checksum(root / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json"),
        require_string(config.get("available_at"), "available_at"),
    )


def _build_state(
    config: dict[str, Any],
    envelopes: tuple[CanonicalTimeEnvelopeV1, ...],
    health: ClockHealthStateV1,
    root: Path,
    code_commit: str,
) -> TimestampClockTimezoneGovernanceStateV1:
    state = TimestampClockTimezoneGovernanceStateV1(
        run_context=_build_run_context(config, code_commit),
        lineage=_build_lineage(config, root),
        event_time=require_string(config.get("event_time"), "event_time"),
        available_at=require_string(config.get("available_at"), "available_at"),
        generated_at=require_string(config.get("generated_at"), "generated_at"),
        validation_state="VALIDATED_TEMPORAL_ONLY",
        canonical_envelopes=tuple(sorted(envelopes, key=lambda item: item.ordering_key())),
        clock_health=health,
        metrics=Lot33MetricsV1(
            len(envelopes), 0, sum(item.out_of_order_delay_us > 0 for item in envelopes), 0
        ),
        reason_codes=(
            "LOT33_ENTRY_GATE_VERIFIED",
            "LOT32_INSTRUMENT_LINEAGE_VERIFIED",
            "TIMESTAMPS_CANONICALIZED_TO_UTC",
            "RAW_TIMEZONE_AND_PRECISION_PRESERVED",
            "AVAILABLE_AT_ANTI_LOOKAHEAD_VERIFIED",
            "CLOCK_HEALTH_EVALUATED",
            "EXTERNAL_CONNECTIVITY_DISABLED",
            "LOT34_REMAINS_LOCKED",
        ),
        safety=fail_closed_safety(),
        output_checksum="0" * 64,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    state: TimestampClockTimezoneGovernanceStateV1,
    config_checksum: str,
) -> TimestampClockTimezoneGovernanceAuditV1:
    audit = TimestampClockTimezoneGovernanceAuditV1(
        code_commit=state.run_context.code_commit,
        state_output_checksum=state.output_checksum,
        config_checksum=config_checksum,
        instrument_registry_checksum=state.lineage.instrument_registry_checksum,
        record_count=len(state.canonical_envelopes),
        out_of_order_record_count=state.metrics.out_of_order_records_total,
        clock_health_status=state.clock_health.status,
        max_observed_clock_drift_us=state.clock_health.observed_clock_drift_us,
        max_observed_total_latency_us=state.clock_health.observed_total_latency_us,
        validation_state=state.validation_state,
        safety=fail_closed_safety(),
        audit_checksum="0" * 64,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def _validate_records(records: tuple[RawTimestampEnvelopeV1, ...]) -> None:
    if not records:
        raise TimestampGovernanceError("Lot 33 requires timestamp records")
    record_ids = tuple(record.record_id for record in records)
    if len(set(record_ids)) != len(record_ids):
        raise TimestampGovernanceError("timestamp record ids must be unique")


def build_lot33_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[TimestampClockTimezoneGovernanceStateV1, TimestampClockTimezoneGovernanceAuditV1]:
    config_path = root / "config/data_governance/timestamp_clock_timezone_governance_v1.json"
    gate = load_json_object(root / "data/audit/lot33_v3_entry_gate.json")
    config = load_json_object(config_path)
    registry = load_json_object(root / "data/audit/instrument_registry_lot32.json")
    _verify_gate(gate)
    _validate_config(config)
    instrument_id, sources = _allowed_sources(registry)
    records = tuple(_build_raw(item) for item in require_object_list(config.get("records"), "records"))
    _validate_records(records)
    if any(item.instrument_id != instrument_id or item.source_id not in sources for item in records):
        raise TimestampGovernanceError("timestamp record references unknown instrument or source")
    delays = _out_of_order_delays(records)
    envelopes = tuple(_normalize_raw(record, delay) for record, delay in zip(records, delays, strict=True))
    thresholds = config.get("thresholds")
    if not isinstance(thresholds, dict):
        raise TimestampGovernanceError("thresholds must be an object")
    health = _build_health(envelopes, thresholds)
    state = _build_state(config, envelopes, health, root, code_commit)
    return state, _build_audit(state, file_checksum(config_path))


def persist_lot33_artifacts(
    root: Path,
    state: TimestampClockTimezoneGovernanceStateV1,
    audit: TimestampClockTimezoneGovernanceAuditV1,
) -> None:
    atomic_write_json(
        root / "data/audit/timestamp_clock_and_timezone_governance_lot33.json",
        state.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json",
        audit.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/canonical_time_envelopes_lot33.json",
        {
            "schema_version": "canonical-time-envelope-collection-v1",
            "records": [item.to_dict() for item in state.canonical_envelopes],
        },
    )


__all__ = ["build_lot33_artifacts", "persist_lot33_artifacts"]
