from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .candle_trade_book_reconciliation_models import ReconciliationVetoV1
from .freshness_gap_outage_audit_and_v3_closure_validation import (
    V3ClosureError,
    require_basis_points,
    require_non_empty_string_tuple,
    validate_causal_times,
    validate_git_and_sha256,
    validate_lot36_safety,
    validate_reason_codes,
    validate_runtime_mode,
)
from .market_data_quality_engine_models import (
    DataAnomalyV1,
    DataQualityStateV1,
    DataQualityVetoV1,
)
from .candle_trade_book_reconciliation_validation import (
    parse_utc_timestamp,
    require_identifier,
    require_integer,
    require_sha256,
)

FRESHNESS_STATUSES = {"PASS", "BLOCKED", "UNKNOWN"}
CLOSURE_VALIDATION_STATES = {
    "VALIDATED_V3_CLOSURE_CANDIDATE",
    "BLOCKED_V3_CLOSURE",
}
CLOSURE_MANIFEST_STATES = {
    "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT",
    "BLOCKED",
}
REPLAY_STATUSES = {"REPLAY_MATCH", "REPLAY_DIVERGENCE", "REPLAY_IMPOSSIBLE"}


@dataclass(frozen=True, slots=True)
class Lot36RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        require_identifier(self.run_id, "run_id")
        require_identifier(self.config_version, "config_version")
        require_identifier(self.correlation_id, "correlation_id")
        validate_runtime_mode(self.runtime_mode)
        validate_git_and_sha256(self.code_commit, {})

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
class Lot36LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    canonical_roadmap_blob_sha: str
    lot34_state_checksum: str
    lot34_audit_checksum: str
    lot35_state_checksum: str
    lot35_audit_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_identifier(self.lineage_id, "lineage_id")
        validate_git_and_sha256(
            "0" * 40,
            {
                "entry_gate_checksum": self.entry_gate_checksum,
                "lot34_state_checksum": self.lot34_state_checksum,
                "lot34_audit_checksum": self.lot34_audit_checksum,
                "lot35_state_checksum": self.lot35_state_checksum,
                "lot35_audit_checksum": self.lot35_audit_checksum,
            },
        )
        if len(self.canonical_roadmap_blob_sha) != 40:
            raise V3ClosureError("canonical roadmap blob SHA must be a Git SHA")
        int(self.canonical_roadmap_blob_sha, 16)
        parse_utc_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot36-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "canonical_roadmap_blob_sha": self.canonical_roadmap_blob_sha,
            "lot34_state_checksum": self.lot34_state_checksum,
            "lot34_audit_checksum": self.lot34_audit_checksum,
            "lot35_state_checksum": self.lot35_state_checksum,
            "lot35_audit_checksum": self.lot35_audit_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class FreshnessGapOutageEvidenceV1:
    source_id: str
    instrument_id: str
    timeframe: str
    record_count: int
    expected_interval_count: int
    observed_interval_count: int
    missing_interval_count: int
    gap_count: int
    outage_count: int
    stale_record_count: int
    latest_event_time: str
    reference_time: str
    freshness_age_us: int
    max_staleness_us: int
    freshness_bps: int
    status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        require_identifier(self.source_id, "source_id")
        require_identifier(self.instrument_id, "instrument_id")
        require_identifier(self.timeframe, "timeframe")
        for field, value in (
            ("record_count", self.record_count),
            ("expected_interval_count", self.expected_interval_count),
            ("observed_interval_count", self.observed_interval_count),
            ("missing_interval_count", self.missing_interval_count),
            ("gap_count", self.gap_count),
            ("outage_count", self.outage_count),
            ("stale_record_count", self.stale_record_count),
            ("freshness_age_us", self.freshness_age_us),
            ("max_staleness_us", self.max_staleness_us),
        ):
            require_integer(value, field, minimum=0)
        parse_utc_timestamp(self.latest_event_time, "latest_event_time")
        parse_utc_timestamp(self.reference_time, "reference_time")
        require_basis_points(self.freshness_bps, "freshness_bps")
        if self.status not in FRESHNESS_STATUSES:
            raise V3ClosureError("unknown freshness/gap/outage status")
        validate_reason_codes(self.reason_codes, "freshness audit")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "freshness-gap-outage-evidence-v1",
            "source_id": self.source_id,
            "instrument_id": self.instrument_id,
            "timeframe": self.timeframe,
            "record_count": self.record_count,
            "expected_interval_count": self.expected_interval_count,
            "observed_interval_count": self.observed_interval_count,
            "missing_interval_count": self.missing_interval_count,
            "gap_count": self.gap_count,
            "outage_count": self.outage_count,
            "stale_record_count": self.stale_record_count,
            "latest_event_time": self.latest_event_time,
            "reference_time": self.reference_time,
            "freshness_age_us": self.freshness_age_us,
            "max_staleness_us": self.max_staleness_us,
            "freshness_bps": self.freshness_bps,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class LotValidationReportV1:
    validated_lots: tuple[int, ...]
    required_validator_count: int
    closure_candidate_ready: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.validated_lots != tuple(range(31, 37)):
            raise V3ClosureError("Lot 36 validation report must cover Lots 31-36")
        require_integer(self.required_validator_count, "required_validator_count", minimum=1)
        validate_reason_codes(self.reason_codes, "Lot validation report")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot-validation-report-v1",
            "validated_lots": list(self.validated_lots),
            "required_validator_count": self.required_validator_count,
            "closure_candidate_ready": self.closure_candidate_ready,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class ClosureManifestV1:
    version_id: str
    lots_included: tuple[int, ...]
    closure_status: str
    v3_closed: bool
    post_merge_audit_required: bool
    human_review_required: bool
    next_lot: int
    next_lot_status: str
    reason_codes: tuple[str, ...]
    manifest_checksum: str

    def __post_init__(self) -> None:
        if self.version_id != "V3_MARKET_DATA_GOVERNANCE":
            raise V3ClosureError("closure manifest version changed")
        if self.lots_included != tuple(range(31, 37)):
            raise V3ClosureError("closure manifest must cover Lots 31-36")
        if self.closure_status not in CLOSURE_MANIFEST_STATES:
            raise V3ClosureError("unknown closure manifest status")
        if self.v3_closed:
            raise V3ClosureError("implementation cannot finalize V3 before post-merge audit")
        if not self.post_merge_audit_required or not self.human_review_required:
            raise V3ClosureError("Lot 36 closure requires post-merge audit and human review")
        if self.next_lot != 37 or self.next_lot_status != "PLANNED_LOCKED":
            raise V3ClosureError("Lot 37 must remain locked")
        validate_reason_codes(self.reason_codes, "closure manifest")
        require_sha256(self.manifest_checksum, "manifest_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "closure-manifest-v1",
            "version_id": self.version_id,
            "lots_included": list(self.lots_included),
            "closure_status": self.closure_status,
            "v3_closed": self.v3_closed,
            "post_merge_audit_required": self.post_merge_audit_required,
            "human_review_required": self.human_review_required,
            "next_lot": self.next_lot,
            "next_lot_status": self.next_lot_status,
            "reason_codes": list(self.reason_codes),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["manifest_checksum"] = self.manifest_checksum
        return payload


@dataclass(frozen=True, slots=True)
class ReplayEvidenceV1:
    run1_checksum: str
    run2_checksum: str
    replay_status: str
    match: bool
    reason_codes: tuple[str, ...]
    replay_checksum: str

    def __post_init__(self) -> None:
        for field, value in (
            ("run1_checksum", self.run1_checksum),
            ("run2_checksum", self.run2_checksum),
            ("replay_checksum", self.replay_checksum),
        ):
            require_sha256(value, field)
        if self.replay_status not in REPLAY_STATUSES:
            raise V3ClosureError("unknown replay status")
        if self.match != (self.run1_checksum == self.run2_checksum):
            raise V3ClosureError("replay match flag contradicts checksums")
        if self.replay_status == "REPLAY_MATCH" and not self.match:
            raise V3ClosureError("REPLAY_MATCH requires identical checksums")
        validate_reason_codes(self.reason_codes, "replay evidence")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "replay-evidence-v1",
            "run1_checksum": self.run1_checksum,
            "run2_checksum": self.run2_checksum,
            "replay_status": self.replay_status,
            "match": self.match,
            "reason_codes": list(self.reason_codes),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["replay_checksum"] = self.replay_checksum
        return payload


@dataclass(frozen=True, slots=True)
class Lot36MetricsV1:
    records_processed_total: int
    validation_failures_total: int
    gap_total: int
    outage_total: int
    stale_record_total: int
    anomaly_total: int
    processing_latency_us: int

    def __post_init__(self) -> None:
        for field, value in (
            ("records_processed_total", self.records_processed_total),
            ("validation_failures_total", self.validation_failures_total),
            ("gap_total", self.gap_total),
            ("outage_total", self.outage_total),
            ("stale_record_total", self.stale_record_total),
            ("anomaly_total", self.anomaly_total),
            ("processing_latency_us", self.processing_latency_us),
        ):
            require_integer(value, field, minimum=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot36-metrics-v1",
            "lot_36_records_processed_total": self.records_processed_total,
            "lot_36_validation_failures_total": self.validation_failures_total,
            "lot_36_gap_total": self.gap_total,
            "lot_36_outage_total": self.outage_total,
            "lot_36_stale_record_total": self.stale_record_total,
            "lot_36_anomaly_total": self.anomaly_total,
            "lot_36_processing_latency_us": self.processing_latency_us,
        }


@dataclass(frozen=True, slots=True)
class FreshnessGapOutageAuditV3ClosureStateV1:
    run_context: Lot36RunContextV1
    lineage: Lot36LineageEnvelopeV1
    event_time: str
    available_at: str
    generated_at: str
    validation_state: str
    freshness_audits: tuple[FreshnessGapOutageEvidenceV1, ...]
    quality_states: tuple[DataQualityStateV1, ...]
    anomalies: tuple[DataAnomalyV1, ...]
    data_quality_veto: DataQualityVetoV1
    reconciliation_veto: ReconciliationVetoV1
    validation_report: LotValidationReportV1
    closure_manifest: ClosureManifestV1
    metrics: Lot36MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        validate_causal_times(self.event_time, self.available_at, self.generated_at)
        if self.validation_state not in CLOSURE_VALIDATION_STATES:
            raise V3ClosureError("unknown Lot 36 validation state")
        if not self.freshness_audits or not self.quality_states:
            raise V3ClosureError("Lot 36 requires freshness and quality evidence")
        validate_reason_codes(self.reason_codes, "Lot 36 state")
        validate_lot36_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "freshness-gap-outage-audit-v3-closure-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "available_at": self.available_at,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "freshness_audits": [item.to_dict() for item in self.freshness_audits],
            "quality_states": [item.to_dict() for item in self.quality_states],
            "anomalies": [item.to_dict() for item in self.anomalies],
            "data_quality_veto": self.data_quality_veto.to_dict(),
            "reconciliation_veto": self.reconciliation_veto.to_dict(),
            "validation_report": self.validation_report.to_dict(),
            "closure_manifest": self.closure_manifest.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload


@dataclass(frozen=True, slots=True)
class FreshnessGapOutageAuditV3ClosureAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    closure_manifest_checksum: str
    lot34_state_checksum: str
    lot34_audit_checksum: str
    lot35_state_checksum: str
    lot35_audit_checksum: str
    freshness_audit_count: int
    anomaly_count: int
    data_quality_veto_action: str
    reconciliation_veto_action: str
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        validate_git_and_sha256(
            self.code_commit,
            {
                "state_output_checksum": self.state_output_checksum,
                "config_checksum": self.config_checksum,
                "closure_manifest_checksum": self.closure_manifest_checksum,
                "lot34_state_checksum": self.lot34_state_checksum,
                "lot34_audit_checksum": self.lot34_audit_checksum,
                "lot35_state_checksum": self.lot35_state_checksum,
                "lot35_audit_checksum": self.lot35_audit_checksum,
                "audit_checksum": self.audit_checksum,
            },
        )
        require_integer(self.freshness_audit_count, "freshness_audit_count", minimum=1)
        require_integer(self.anomaly_count, "anomaly_count", minimum=0)
        if self.validation_state not in CLOSURE_VALIDATION_STATES:
            raise V3ClosureError("unknown Lot 36 audit validation state")
        validate_lot36_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "freshness-gap-outage-audit-v3-closure-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "closure_manifest_checksum": self.closure_manifest_checksum,
            "lot34_state_checksum": self.lot34_state_checksum,
            "lot34_audit_checksum": self.lot34_audit_checksum,
            "lot35_state_checksum": self.lot35_state_checksum,
            "lot35_audit_checksum": self.lot35_audit_checksum,
            "freshness_audit_count": self.freshness_audit_count,
            "anomaly_count": self.anomaly_count,
            "data_quality_veto_action": self.data_quality_veto_action,
            "reconciliation_veto_action": self.reconciliation_veto_action,
            "validation_state": self.validation_state,
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["audit_checksum"] = self.audit_checksum
        return payload
