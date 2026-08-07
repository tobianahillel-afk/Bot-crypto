from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .market_data_quality_engine_validation import (
    MarketDataQualityError,
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_sha256,
    validate_lot34_safety,
)

ANOMALY_TYPES = {
    "MISSING_INTERVAL",
    "DUPLICATE",
    "OUT_OF_ORDER",
    "STALE_DATA",
    "INVALID_OHLC",
    "NEGATIVE_VOLUME",
    "IMPOSSIBLE_SPREAD",
    "SCHEMA_DRIFT",
}
SEVERITIES = {"INFO", "WARNING", "ERROR", "CRITICAL"}
VETO_ACTIONS = {"ALLOW_ANALYSIS", "BLOCK_ANALYSIS_OR_TRADING"}


@dataclass(frozen=True, slots=True)
class Lot34RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        require_identifier(self.run_id, "run_id")
        require_identifier(self.config_version, "config_version")
        require_identifier(self.correlation_id, "correlation_id")
        if self.runtime_mode != "DATA_GOVERNANCE_ONLY":
            raise MarketDataQualityError("Lot 34 runtime must be DATA_GOVERNANCE_ONLY")
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
class Lot34LineageEnvelopeV1:
    lineage_id: str
    lot33_state_checksum: str
    lot33_audit_checksum: str
    canonical_time_collection_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_identifier(self.lineage_id, "lineage_id")
        require_sha256(self.lot33_state_checksum, "lot33_state_checksum")
        require_sha256(self.lot33_audit_checksum, "lot33_audit_checksum")
        require_sha256(self.canonical_time_collection_checksum, "canonical_time_collection_checksum")
        parse_utc_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot34-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "lot33_state_checksum": self.lot33_state_checksum,
            "lot33_audit_checksum": self.lot33_audit_checksum,
            "canonical_time_collection_checksum": self.canonical_time_collection_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class DataAnomalyV1:
    anomaly_id: str
    anomaly_type: str
    severity: str
    record_ids: tuple[str, ...]
    interval_start: str
    interval_end: str
    correction_permitted: bool
    quarantined: bool
    reason_code: str

    def __post_init__(self) -> None:
        require_identifier(self.anomaly_id, "anomaly_id")
        if self.anomaly_type not in ANOMALY_TYPES:
            raise MarketDataQualityError("unknown anomaly type")
        if self.severity not in SEVERITIES:
            raise MarketDataQualityError("unknown anomaly severity")
        if not self.record_ids:
            raise MarketDataQualityError("anomaly requires at least one record reference")
        for record_id in self.record_ids:
            require_identifier(record_id, "record_id")
        start = parse_utc_timestamp(self.interval_start, "interval_start")
        end = parse_utc_timestamp(self.interval_end, "interval_end")
        if start > end:
            raise MarketDataQualityError("anomaly interval cannot run backwards")
        if self.correction_permitted:
            raise MarketDataQualityError("Lot 34 cannot permit destructive correction")
        if not self.quarantined:
            raise MarketDataQualityError("Lot 34 anomalies must be quarantined non-destructively")
        require_identifier(self.reason_code, "reason_code")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "data-anomaly-v1",
            "anomaly_id": self.anomaly_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "record_ids": list(self.record_ids),
            "interval_start": self.interval_start,
            "interval_end": self.interval_end,
            "correction_permitted": self.correction_permitted,
            "quarantined": self.quarantined,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True, slots=True)
class DataQualityStateV1:
    source_id: str
    instrument_id: str
    timeframe: str
    record_count: int
    expected_interval_count: int
    observed_interval_count: int
    anomaly_count: int
    coverage_bps: int
    freshness_bps: int
    completeness_bps: int
    consistency_bps: int
    quality_score_bps: int
    status: str

    def __post_init__(self) -> None:
        require_identifier(self.source_id, "source_id")
        require_identifier(self.instrument_id, "instrument_id")
        require_identifier(self.timeframe, "timeframe")
        for field, value in (
            ("record_count", self.record_count),
            ("expected_interval_count", self.expected_interval_count),
            ("observed_interval_count", self.observed_interval_count),
            ("anomaly_count", self.anomaly_count),
        ):
            require_integer(value, field, minimum=0)
        for field, value in (
            ("coverage_bps", self.coverage_bps),
            ("freshness_bps", self.freshness_bps),
            ("completeness_bps", self.completeness_bps),
            ("consistency_bps", self.consistency_bps),
            ("quality_score_bps", self.quality_score_bps),
        ):
            if not 0 <= value <= 10_000:
                raise MarketDataQualityError(f"{field} must be between 0 and 10000")
        if self.status not in {"PASS", "DEGRADED", "BLOCKED", "UNKNOWN"}:
            raise MarketDataQualityError("unknown data quality status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "data-quality-state-v1",
            "source_id": self.source_id,
            "instrument_id": self.instrument_id,
            "timeframe": self.timeframe,
            "record_count": self.record_count,
            "expected_interval_count": self.expected_interval_count,
            "observed_interval_count": self.observed_interval_count,
            "anomaly_count": self.anomaly_count,
            "coverage_bps": self.coverage_bps,
            "freshness_bps": self.freshness_bps,
            "completeness_bps": self.completeness_bps,
            "consistency_bps": self.consistency_bps,
            "quality_score_bps": self.quality_score_bps,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class DataQualityVetoV1:
    action: str
    quality_known: bool
    minimum_quality_bps: int
    observed_quality_bps: int
    blocking_anomaly_types: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.action not in VETO_ACTIONS:
            raise MarketDataQualityError("unknown quality veto action")
        if not 0 <= self.minimum_quality_bps <= 10_000:
            raise MarketDataQualityError("minimum quality must be in basis points")
        if not 0 <= self.observed_quality_bps <= 10_000:
            raise MarketDataQualityError("observed quality must be in basis points")
        for anomaly_type in self.blocking_anomaly_types:
            if anomaly_type not in ANOMALY_TYPES:
                raise MarketDataQualityError("veto references unknown anomaly")
        if not self.reason_codes:
            raise MarketDataQualityError("quality veto requires reason codes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "data-quality-veto-v1",
            "action": self.action,
            "quality_known": self.quality_known,
            "minimum_quality_bps": self.minimum_quality_bps,
            "observed_quality_bps": self.observed_quality_bps,
            "blocking_anomaly_types": list(self.blocking_anomaly_types),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class Lot34MetricsV1:
    records_processed_total: int
    validation_failures_total: int
    anomalies_detected_total: int
    quarantined_records_total: int
    processing_latency_us: int

    def __post_init__(self) -> None:
        for field, value in (
            ("records_processed_total", self.records_processed_total),
            ("validation_failures_total", self.validation_failures_total),
            ("anomalies_detected_total", self.anomalies_detected_total),
            ("quarantined_records_total", self.quarantined_records_total),
            ("processing_latency_us", self.processing_latency_us),
        ):
            require_integer(value, field, minimum=0)

    def to_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": "lot34-metrics-v1",
            "lot_34_records_processed_total": self.records_processed_total,
            "lot_34_validation_failures_total": self.validation_failures_total,
            "lot_34_anomalies_detected_total": self.anomalies_detected_total,
            "lot_34_quarantined_records_total": self.quarantined_records_total,
            "lot_34_processing_latency_us": self.processing_latency_us,
        }


@dataclass(frozen=True, slots=True)
class MarketDataQualityEngineStateV1:
    run_context: Lot34RunContextV1
    lineage: Lot34LineageEnvelopeV1
    event_time: str
    available_at: str
    generated_at: str
    validation_state: str
    quality_states: tuple[DataQualityStateV1, ...]
    anomalies: tuple[DataAnomalyV1, ...]
    quarantine_record_ids: tuple[str, ...]
    veto: DataQualityVetoV1
    metrics: Lot34MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        event = parse_utc_timestamp(self.event_time, "event_time")
        available = parse_utc_timestamp(self.available_at, "available_at")
        generated = parse_utc_timestamp(self.generated_at, "generated_at")
        if not event <= available <= generated:
            raise MarketDataQualityError("Lot 34 state violates causal availability")
        if self.validation_state not in {"VALIDATED_DATA_QUALITY_ONLY", "BLOCKED_DATA_QUALITY"}:
            raise MarketDataQualityError("unexpected Lot 34 validation state")
        if not self.quality_states:
            raise MarketDataQualityError("Lot 34 requires quality states")
        if tuple(sorted(self.quarantine_record_ids)) != self.quarantine_record_ids:
            raise MarketDataQualityError("quarantine ids must be sorted")
        validate_lot34_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "market-data-quality-engine-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "available_at": self.available_at,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "quality_states": [item.to_dict() for item in self.quality_states],
            "anomalies": [item.to_dict() for item in self.anomalies],
            "quarantine_record_ids": list(self.quarantine_record_ids),
            "veto": self.veto.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload


@dataclass(frozen=True, slots=True)
class MarketDataQualityEngineAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    lot33_state_checksum: str
    lot33_audit_checksum: str
    record_count: int
    anomaly_count: int
    quarantined_record_count: int
    veto_action: str
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit)
        for checksum_field, checksum_value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("lot33_state_checksum", self.lot33_state_checksum),
            ("lot33_audit_checksum", self.lot33_audit_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(checksum_value, checksum_field)
        for count_field, count_value in (
            ("record_count", self.record_count),
            ("anomaly_count", self.anomaly_count),
            ("quarantined_record_count", self.quarantined_record_count),
        ):
            require_integer(count_value, count_field, minimum=0)
        if self.veto_action not in VETO_ACTIONS:
            raise MarketDataQualityError("audit veto action invalid")
        validate_lot34_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "market-data-quality-engine-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "lot33_state_checksum": self.lot33_state_checksum,
            "lot33_audit_checksum": self.lot33_audit_checksum,
            "record_count": self.record_count,
            "anomaly_count": self.anomaly_count,
            "quarantined_record_count": self.quarantined_record_count,
            "veto_action": self.veto_action,
            "validation_state": self.validation_state,
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["audit_checksum"] = self.audit_checksum
        return payload
