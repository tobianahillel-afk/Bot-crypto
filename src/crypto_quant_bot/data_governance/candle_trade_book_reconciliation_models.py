from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .candle_trade_book_reconciliation_validation import (
    ReconciliationError,
    non_negative_decimal_string,
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_sha256,
    validate_lot35_safety,
)

ENTITY_TYPES = {"CANDLE", "TRADE", "BOOK"}
SOURCE_OF_TRUTH = {"PRIMARY", "SECONDARY", "UNKNOWN"}
CLASSIFICATIONS = {
    "MATCH",
    "TOLERATED_DIFF",
    "MINOR_DIVERGENCE",
    "CRITICAL_DIVERGENCE",
}
CORRECTIVE_ACTIONS = {"NONE", "REVIEW_AND_PAUSE", "MANUAL_RECONCILIATION_REQUIRED"}
VETO_ACTIONS = {"ALLOW_ANALYSIS", "PAUSE", "KILL_SWITCH"}


@dataclass(frozen=True, slots=True)
class Lot35RunContextV1:
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
            raise ReconciliationError("Lot 35 runtime must be DATA_GOVERNANCE_ONLY")
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
class Lot35LineageEnvelopeV1:
    lineage_id: str
    lot34_state_checksum: str
    lot34_audit_checksum: str
    quality_state_collection_checksum: str
    anomaly_collection_checksum: str
    quality_veto_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_identifier(self.lineage_id, "lineage_id")
        require_sha256(self.lot34_state_checksum, "lot34_state_checksum")
        require_sha256(self.lot34_audit_checksum, "lot34_audit_checksum")
        require_sha256(
            self.quality_state_collection_checksum,
            "quality_state_collection_checksum",
        )
        require_sha256(self.anomaly_collection_checksum, "anomaly_collection_checksum")
        require_sha256(self.quality_veto_checksum, "quality_veto_checksum")
        parse_utc_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot35-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "lot34_state_checksum": self.lot34_state_checksum,
            "lot34_audit_checksum": self.lot34_audit_checksum,
            "quality_state_collection_checksum": self.quality_state_collection_checksum,
            "anomaly_collection_checksum": self.anomaly_collection_checksum,
            "quality_veto_checksum": self.quality_veto_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationSnapshotV1:
    record_id: str
    identifier: str
    quantity: str
    price: str
    fee: str
    balance: str
    position: str
    event_time: str

    def __post_init__(self) -> None:
        require_identifier(self.record_id, "record_id")
        require_identifier(self.identifier, "identifier")
        non_negative_decimal_string(self.quantity, "quantity")
        non_negative_decimal_string(self.price, "price")
        non_negative_decimal_string(self.fee, "fee")
        non_negative_decimal_string(self.balance, "balance")
        non_negative_decimal_string(self.position, "position")
        parse_utc_timestamp(self.event_time, "event_time")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "reconciliation-snapshot-v1",
            "record_id": self.record_id,
            "identifier": self.identifier,
            "quantity": self.quantity,
            "price": self.price,
            "fee": self.fee,
            "balance": self.balance,
            "position": self.position,
            "event_time": self.event_time,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationDeltaV1:
    quantity_abs: str
    price_abs: str
    fee_abs: str
    balance_abs: str
    position_abs: str
    timestamp_us: int

    def __post_init__(self) -> None:
        non_negative_decimal_string(self.quantity_abs, "quantity_abs")
        non_negative_decimal_string(self.price_abs, "price_abs")
        non_negative_decimal_string(self.fee_abs, "fee_abs")
        non_negative_decimal_string(self.balance_abs, "balance_abs")
        non_negative_decimal_string(self.position_abs, "position_abs")
        require_integer(self.timestamp_us, "timestamp_us", minimum=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "reconciliation-delta-v1",
            "quantity_abs": self.quantity_abs,
            "price_abs": self.price_abs,
            "fee_abs": self.fee_abs,
            "balance_abs": self.balance_abs,
            "position_abs": self.position_abs,
            "timestamp_us": self.timestamp_us,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationReportV1:
    reconciliation_id: str
    entity_type: str
    source_of_truth: str
    primary_record_id: str | None
    secondary_record_id: str | None
    classification: str
    delta: ReconciliationDeltaV1 | None
    tolerance_version: str
    duplicate: bool
    orphan: bool
    corrective_action: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        require_identifier(self.reconciliation_id, "reconciliation_id")
        if self.entity_type not in ENTITY_TYPES:
            raise ReconciliationError("unknown reconciliation entity type")
        if self.source_of_truth not in SOURCE_OF_TRUTH:
            raise ReconciliationError("unknown source-of-truth value")
        if self.primary_record_id is not None:
            require_identifier(self.primary_record_id, "primary_record_id")
        if self.secondary_record_id is not None:
            require_identifier(self.secondary_record_id, "secondary_record_id")
        if self.classification not in CLASSIFICATIONS:
            raise ReconciliationError("unknown reconciliation classification")
        if self.corrective_action not in CORRECTIVE_ACTIONS:
            raise ReconciliationError("unknown reconciliation corrective action")
        require_identifier(self.tolerance_version, "tolerance_version")
        if not self.reason_codes:
            raise ReconciliationError("reconciliation report requires reason codes")
        for reason in self.reason_codes:
            require_identifier(reason, "reason_code")
        if self.orphan and self.delta is not None:
            raise ReconciliationError("orphan reconciliation cannot claim exact deltas")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "reconciliation-report-v1",
            "reconciliation_id": self.reconciliation_id,
            "entity_type": self.entity_type,
            "source_of_truth": self.source_of_truth,
            "primary_record_id": self.primary_record_id,
            "secondary_record_id": self.secondary_record_id,
            "classification": self.classification,
            "delta": None if self.delta is None else self.delta.to_dict(),
            "tolerance_version": self.tolerance_version,
            "duplicate": self.duplicate,
            "orphan": self.orphan,
            "corrective_action": self.corrective_action,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationVetoV1:
    action: str
    reconciliation_known: bool
    minor_divergence_count: int
    critical_divergence_count: int
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.action not in VETO_ACTIONS:
            raise ReconciliationError("unknown reconciliation veto action")
        require_integer(self.minor_divergence_count, "minor_divergence_count", minimum=0)
        require_integer(self.critical_divergence_count, "critical_divergence_count", minimum=0)
        if not self.reason_codes:
            raise ReconciliationError("reconciliation veto requires reason codes")
        for reason in self.reason_codes:
            require_identifier(reason, "reason_code")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "reconciliation-veto-v1",
            "action": self.action,
            "reconciliation_known": self.reconciliation_known,
            "minor_divergence_count": self.minor_divergence_count,
            "critical_divergence_count": self.critical_divergence_count,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class Lot35MetricsV1:
    records_processed_total: int
    validation_failures_total: int
    match_total: int
    tolerated_diff_total: int
    minor_divergence_total: int
    critical_divergence_total: int
    processing_latency_us: int

    def __post_init__(self) -> None:
        for field, value in (
            ("records_processed_total", self.records_processed_total),
            ("validation_failures_total", self.validation_failures_total),
            ("match_total", self.match_total),
            ("tolerated_diff_total", self.tolerated_diff_total),
            ("minor_divergence_total", self.minor_divergence_total),
            ("critical_divergence_total", self.critical_divergence_total),
            ("processing_latency_us", self.processing_latency_us),
        ):
            require_integer(value, field, minimum=0)

    def to_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": "lot35-metrics-v1",
            "lot_35_records_processed_total": self.records_processed_total,
            "lot_35_validation_failures_total": self.validation_failures_total,
            "lot_35_match_total": self.match_total,
            "lot_35_tolerated_diff_total": self.tolerated_diff_total,
            "lot_35_minor_divergence_total": self.minor_divergence_total,
            "lot_35_critical_divergence_total": self.critical_divergence_total,
            "lot_35_processing_latency_us": self.processing_latency_us,
        }


@dataclass(frozen=True, slots=True)
class CandleTradeBookReconciliationStateV1:
    run_context: Lot35RunContextV1
    lineage: Lot35LineageEnvelopeV1
    event_time: str
    available_at: str
    generated_at: str
    validation_state: str
    reports: tuple[ReconciliationReportV1, ...]
    veto: ReconciliationVetoV1
    metrics: Lot35MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        event = parse_utc_timestamp(self.event_time, "event_time")
        available = parse_utc_timestamp(self.available_at, "available_at")
        generated = parse_utc_timestamp(self.generated_at, "generated_at")
        if not event <= available <= generated:
            raise ReconciliationError("Lot 35 state violates causal availability")
        if self.validation_state not in {
            "VALIDATED_RECONCILIATION_ONLY",
            "BLOCKED_RECONCILIATION",
        }:
            raise ReconciliationError("unexpected Lot 35 validation state")
        if not self.reports:
            raise ReconciliationError("Lot 35 requires reconciliation reports")
        validate_lot35_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "candle-trade-book-reconciliation-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "available_at": self.available_at,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "reports": [item.to_dict() for item in self.reports],
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
class CandleTradeBookReconciliationAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    lot34_state_checksum: str
    lot34_audit_checksum: str
    report_count: int
    match_count: int
    tolerated_diff_count: int
    minor_divergence_count: int
    critical_divergence_count: int
    veto_action: str
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit)
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("lot34_state_checksum", self.lot34_state_checksum),
            ("lot34_audit_checksum", self.lot34_audit_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        for field, value in (
            ("report_count", self.report_count),
            ("match_count", self.match_count),
            ("tolerated_diff_count", self.tolerated_diff_count),
            ("minor_divergence_count", self.minor_divergence_count),
            ("critical_divergence_count", self.critical_divergence_count),
        ):
            require_integer(value, field, minimum=0)
        if self.veto_action not in VETO_ACTIONS:
            raise ReconciliationError("audit veto action invalid")
        validate_lot35_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "candle-trade-book-reconciliation-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "lot34_state_checksum": self.lot34_state_checksum,
            "lot34_audit_checksum": self.lot34_audit_checksum,
            "report_count": self.report_count,
            "match_count": self.match_count,
            "tolerated_diff_count": self.tolerated_diff_count,
            "minor_divergence_count": self.minor_divergence_count,
            "critical_divergence_count": self.critical_divergence_count,
            "veto_action": self.veto_action,
            "validation_state": self.validation_state,
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["audit_checksum"] = self.audit_checksum
        return payload
