from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .timestamp_clock_timezone_validation import (
    TimestampGovernanceError,
    parse_aware_timestamp,
    require_git_sha,
    require_identifier,
    require_sha256,
    require_text,
    validate_fail_closed,
    validate_precision,
)


@dataclass(frozen=True, slots=True)
class Lot33RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        for field, value in (
            ("run_id", self.run_id),
            ("config_version", self.config_version),
            ("correlation_id", self.correlation_id),
        ):
            require_identifier(value, field)
        if self.runtime_mode != "DATA_GOVERNANCE_ONLY":
            raise TimestampGovernanceError("Lot 33 runtime must be DATA_GOVERNANCE_ONLY")
        require_git_sha(self.code_commit)

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot33LineageEnvelopeV1:
    lineage_id: str
    instrument_registry_path: str
    instrument_registry_checksum: str
    lot32_state_checksum: str
    lot32_audit_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_identifier(self.lineage_id, "lineage_id")
        if self.instrument_registry_path != "data/audit/instrument_registry_lot32.json":
            raise TimestampGovernanceError("Lot 33 lineage must use InstrumentRegistryV1")
        for field, value in (
            ("instrument_registry_checksum", self.instrument_registry_checksum),
            ("lot32_state_checksum", self.lot32_state_checksum),
            ("lot32_audit_checksum", self.lot32_audit_checksum),
        ):
            require_sha256(value, field)
        parse_aware_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot33-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "instrument_registry_path": self.instrument_registry_path,
            "instrument_registry_checksum": self.instrument_registry_checksum,
            "lot32_state_checksum": self.lot32_state_checksum,
            "lot32_audit_checksum": self.lot32_audit_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class RawTimestampEnvelopeV1:
    record_id: str
    instrument_id: str
    source_id: str
    raw_timestamp: str
    source_timezone: str
    timestamp_precision: str
    source_time: str
    exchange_time: str | None
    event_time: str
    receive_time: str
    process_time: str
    available_at: str
    usable_from: str
    monotonic_time: int | None
    clock_domain: str
    sequence_id: int
    revision_id: int

    def __post_init__(self) -> None:
        for field, value in (
            ("record_id", self.record_id),
            ("instrument_id", self.instrument_id),
            ("source_id", self.source_id),
        ):
            require_identifier(value, field)
        require_text(self.source_timezone, "source_timezone")
        validate_precision(self.raw_timestamp, self.timestamp_precision)
        self._validate_timestamps()
        self._validate_sequence_and_clock()

    def _validate_timestamps(self) -> None:
        for field, value in (
            ("raw_timestamp", self.raw_timestamp),
            ("source_time", self.source_time),
            ("event_time", self.event_time),
            ("receive_time", self.receive_time),
            ("process_time", self.process_time),
            ("available_at", self.available_at),
            ("usable_from", self.usable_from),
        ):
            parse_aware_timestamp(value, field)
        if self.exchange_time is not None:
            parse_aware_timestamp(self.exchange_time, "exchange_time")
        if self.raw_timestamp != self.source_time:
            raise TimestampGovernanceError("raw_timestamp must preserve source_time exactly")

    def _validate_sequence_and_clock(self) -> None:
        if self.sequence_id < 0 or self.revision_id < 0:
            raise TimestampGovernanceError("sequence_id and revision_id cannot be negative")
        if self.monotonic_time is None:
            if self.clock_domain != "WALL_CLOCK_ONLY":
                raise TimestampGovernanceError("missing monotonic_time requires WALL_CLOCK_ONLY")
        elif self.monotonic_time < 0 or self.clock_domain != "PROCESS_MONOTONIC_NS":
            raise TimestampGovernanceError("monotonic_time requires PROCESS_MONOTONIC_NS")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "raw-timestamp-envelope-v1",
            "record_id": self.record_id,
            "instrument_id": self.instrument_id,
            "source_id": self.source_id,
            "raw_timestamp": self.raw_timestamp,
            "source_timezone": self.source_timezone,
            "timestamp_precision": self.timestamp_precision,
            "source_time": self.source_time,
            "exchange_time": self.exchange_time,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "process_time": self.process_time,
            "available_at": self.available_at,
            "usable_from": self.usable_from,
            "monotonic_time": self.monotonic_time,
            "clock_domain": self.clock_domain,
            "sequence_id": self.sequence_id,
            "revision_id": self.revision_id,
        }


@dataclass(frozen=True, slots=True)
class CanonicalTimeEnvelopeV1:
    raw: RawTimestampEnvelopeV1
    source_time_utc: str
    exchange_time_utc: str | None
    event_time_utc: str
    receive_time_utc: str
    process_time_utc: str
    available_at_utc: str
    usable_from_utc: str
    clock_drift_us: int
    transport_latency_us: int
    processing_latency_us: int
    total_latency_us: int
    out_of_order_delay_us: int
    validation_state: str

    def __post_init__(self) -> None:
        for value in (
            self.transport_latency_us,
            self.processing_latency_us,
            self.total_latency_us,
            self.out_of_order_delay_us,
        ):
            if value < 0:
                raise TimestampGovernanceError("latency values cannot be negative")
        if self.validation_state != "VALIDATED_TEMPORAL_ONLY":
            raise TimestampGovernanceError("unexpected canonical time validation_state")
        self._validate_causal_order()

    def _validate_causal_order(self) -> None:
        event = parse_aware_timestamp(self.event_time_utc, "event_time_utc")
        receive = parse_aware_timestamp(self.receive_time_utc, "receive_time_utc")
        process = parse_aware_timestamp(self.process_time_utc, "process_time_utc")
        available = parse_aware_timestamp(self.available_at_utc, "available_at_utc")
        usable = parse_aware_timestamp(self.usable_from_utc, "usable_from_utc")
        if not event <= receive <= process <= available <= usable:
            raise TimestampGovernanceError("canonical time violates causal availability")

    def ordering_key(self) -> tuple[str, int, int]:
        return self.event_time_utc, self.raw.sequence_id, self.raw.revision_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "canonical-time-envelope-v1",
            "raw": self.raw.to_dict(),
            "source_time_utc": self.source_time_utc,
            "exchange_time_utc": self.exchange_time_utc,
            "event_time_utc": self.event_time_utc,
            "receive_time_utc": self.receive_time_utc,
            "process_time_utc": self.process_time_utc,
            "available_at_utc": self.available_at_utc,
            "usable_from_utc": self.usable_from_utc,
            "clock_drift_us": self.clock_drift_us,
            "transport_latency_us": self.transport_latency_us,
            "processing_latency_us": self.processing_latency_us,
            "total_latency_us": self.total_latency_us,
            "out_of_order_delay_us": self.out_of_order_delay_us,
            "validation_state": self.validation_state,
        }


@dataclass(frozen=True, slots=True)
class ClockHealthStateV1:
    status: str
    max_clock_drift_us: int
    max_out_of_order_delay_us: int
    max_total_latency_us: int
    observed_clock_drift_us: int
    observed_out_of_order_delay_us: int
    observed_total_latency_us: int
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"HEALTHY", "DEGRADED", "BLOCKED"}:
            raise TimestampGovernanceError("unknown clock health status")
        values = (
            self.max_clock_drift_us,
            self.max_out_of_order_delay_us,
            self.max_total_latency_us,
            self.observed_clock_drift_us,
            self.observed_out_of_order_delay_us,
            self.observed_total_latency_us,
        )
        if any(value < 0 for value in values):
            raise TimestampGovernanceError("clock health values cannot be negative")
        if not self.reason_codes:
            raise TimestampGovernanceError("clock health requires reason codes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "clock-health-state-v1",
            "status": self.status,
            "max_clock_drift_us": self.max_clock_drift_us,
            "max_out_of_order_delay_us": self.max_out_of_order_delay_us,
            "max_total_latency_us": self.max_total_latency_us,
            "observed_clock_drift_us": self.observed_clock_drift_us,
            "observed_out_of_order_delay_us": self.observed_out_of_order_delay_us,
            "observed_total_latency_us": self.observed_total_latency_us,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class Lot33MetricsV1:
    records_processed_total: int
    validation_failures_total: int
    out_of_order_records_total: int
    processing_latency_us: int

    def __post_init__(self) -> None:
        values = (
            self.records_processed_total,
            self.validation_failures_total,
            self.out_of_order_records_total,
            self.processing_latency_us,
        )
        if any(value < 0 for value in values):
            raise TimestampGovernanceError("Lot 33 metrics cannot be negative")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": "lot33-metrics-v1",
            "lot_33_records_processed_total": self.records_processed_total,
            "lot_33_validation_failures_total": self.validation_failures_total,
            "lot_33_out_of_order_records_total": self.out_of_order_records_total,
            "lot_33_processing_latency_us": self.processing_latency_us,
        }


@dataclass(frozen=True, slots=True)
class TimestampClockTimezoneGovernanceStateV1:
    run_context: Lot33RunContextV1
    lineage: Lot33LineageEnvelopeV1
    event_time: str
    available_at: str
    generated_at: str
    validation_state: str
    canonical_envelopes: tuple[CanonicalTimeEnvelopeV1, ...]
    clock_health: ClockHealthStateV1
    metrics: Lot33MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        for field, value in (
            ("event_time", self.event_time),
            ("available_at", self.available_at),
            ("generated_at", self.generated_at),
        ):
            parse_aware_timestamp(value, field)
        if self.validation_state != "VALIDATED_TEMPORAL_ONLY":
            raise TimestampGovernanceError("unexpected Lot 33 validation_state")
        keys = tuple(item.ordering_key() for item in self.canonical_envelopes)
        if not keys or keys != tuple(sorted(keys)) or len(set(keys)) != len(keys):
            raise TimestampGovernanceError("canonical time envelopes must be unique and ordered")
        expected_reasons = (
            "LOT33_ENTRY_GATE_VERIFIED",
            "LOT32_INSTRUMENT_LINEAGE_VERIFIED",
            "TIMESTAMPS_CANONICALIZED_TO_UTC",
            "RAW_TIMEZONE_AND_PRECISION_PRESERVED",
            "AVAILABLE_AT_ANTI_LOOKAHEAD_VERIFIED",
            "CLOCK_HEALTH_EVALUATED",
            "EXTERNAL_CONNECTIVITY_DISABLED",
            "LOT34_REMAINS_LOCKED",
        )
        if self.reason_codes != expected_reasons:
            raise TimestampGovernanceError("unexpected Lot 33 reason code sequence")
        validate_fail_closed(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "timestamp-clock-timezone-governance-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "available_at": self.available_at,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "canonical_envelopes": [item.to_dict() for item in self.canonical_envelopes],
            "clock_health": self.clock_health.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload


@dataclass(frozen=True, slots=True)
class TimestampClockTimezoneGovernanceAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    instrument_registry_checksum: str
    record_count: int
    out_of_order_record_count: int
    clock_health_status: str
    max_observed_clock_drift_us: int
    max_observed_total_latency_us: int
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit)
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("instrument_registry_checksum", self.instrument_registry_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        if self.record_count < 1 or self.out_of_order_record_count < 0:
            raise TimestampGovernanceError("audit counts are invalid")
        if self.clock_health_status not in {"HEALTHY", "DEGRADED", "BLOCKED"}:
            raise TimestampGovernanceError("audit clock status is invalid")
        if self.max_observed_clock_drift_us < 0 or self.max_observed_total_latency_us < 0:
            raise TimestampGovernanceError("audit observations cannot be negative")
        if self.validation_state != "VALIDATED_TEMPORAL_ONLY":
            raise TimestampGovernanceError("unexpected audit validation_state")
        validate_fail_closed(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "timestamp-clock-timezone-governance-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "instrument_registry_checksum": self.instrument_registry_checksum,
            "record_count": self.record_count,
            "out_of_order_record_count": self.out_of_order_record_count,
            "clock_health_status": self.clock_health_status,
            "max_observed_clock_drift_us": self.max_observed_clock_drift_us,
            "max_observed_total_latency_us": self.max_observed_total_latency_us,
            "validation_state": self.validation_state,
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["audit_checksum"] = self.audit_checksum
        return payload
