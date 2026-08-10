from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .book_integrity_desynchronization_detector_validation import (
    COMPONENT_NAMES,
    BookIntegrityValidationError,
    decimal_text,
    parse_utc_timestamp,
    require_boolean,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_consequence,
    validate_health_state,
    validate_lot40_safety,
    validate_reason_codes,
    validate_run_context,
)

VALIDATION_STATE = "VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY"


@dataclass(frozen=True, slots=True)
class Lot40RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        validate_run_context(
            self.run_id,
            self.runtime_mode,
            self.config_version,
            self.code_commit,
            self.correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot40-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot40LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot39_state_checksum: str
    lot39_audit_checksum: str
    lot39_reconstructed_book_checksum: str
    lot39_delta_fixture_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        for value, field in self._checksums():
            require_sha256(value, field)
        parse_utc_timestamp(self.available_at, "available_at")

    def _checksums(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.entry_gate_checksum, "entry_gate_checksum"),
            (self.lot39_state_checksum, "lot39_state_checksum"),
            (self.lot39_audit_checksum, "lot39_audit_checksum"),
            (self.lot39_reconstructed_book_checksum, "lot39_reconstructed_book_checksum"),
            (self.lot39_delta_fixture_checksum, "lot39_delta_fixture_checksum"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot40-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot39_state_checksum": self.lot39_state_checksum,
            "lot39_audit_checksum": self.lot39_audit_checksum,
            "lot39_reconstructed_book_checksum": self.lot39_reconstructed_book_checksum,
            "lot39_delta_fixture_checksum": self.lot39_delta_fixture_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class BookHealthComponentV1:
    name: str
    passed: bool
    critical: bool
    weight: Decimal
    score: Decimal
    reason_code: str

    def __post_init__(self) -> None:
        if self.name not in COMPONENT_NAMES:
            raise BookIntegrityValidationError("unknown Lot 40 health component")
        require_boolean(self.passed, "component passed")
        require_boolean(self.critical, "component critical")
        if not self.weight.is_finite() or self.weight <= 0 or self.weight > 100:
            raise BookIntegrityValidationError("component weight must be in (0,100]")
        expected_score = self.weight if self.passed else Decimal("0")
        if self.score != expected_score:
            raise BookIntegrityValidationError("component score must equal passed weight or zero")
        validate_reason_codes((self.reason_code,))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-health-component-v1",
            "name": self.name,
            "passed": self.passed,
            "critical": self.critical,
            "weight": decimal_text(self.weight),
            "score": decimal_text(self.score),
            "reason_code": self.reason_code,
        }


def _expected_health_status(components: tuple[BookHealthComponentV1, ...]) -> str:
    if any(component.critical and not component.passed for component in components):
        return "CRITICAL"
    if any(not component.passed for component in components):
        return "DEGRADED"
    return "HEALTHY"


@dataclass(frozen=True, slots=True)
class BookIntegrityStateV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    decision_time: str
    sequence_id: int
    synchronization_state: str
    stale_age_us: int
    bid_depth_levels: int
    ask_depth_levels: int
    crossed: bool
    locked: bool
    checksum_valid: bool
    level_monotonicity_valid: bool
    health_status: str
    book_health_score: Decimal
    components: tuple[BookHealthComponentV1, ...]
    reason_codes: tuple[str, ...]
    integrity_checksum: str

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_measurements()
        self._validate_components()
        require_sha256(self.integrity_checksum, "integrity_checksum")

    def _validate_identity(self) -> None:
        for value, field in (
            (self.source_id, "source_id"),
            (self.venue, "venue"),
            (self.instrument_id, "instrument_id"),
        ):
            require_text(value, field)
        if self.market_type != "SPOT":
            raise BookIntegrityValidationError("Lot 40 reference book must be SPOT")
        validate_causal_times(
            self.event_time,
            self.receive_time,
            self.decision_time,
            self.decision_time,
        )
        require_integer(self.sequence_id, "sequence_id")
        if self.synchronization_state != "SYNCED":
            raise BookIntegrityValidationError("Lot 40 cannot publish non-SYNCED integrity state")

    def _validate_measurements(self) -> None:
        require_integer(self.stale_age_us, "stale_age_us")
        require_integer(self.bid_depth_levels, "bid_depth_levels")
        require_integer(self.ask_depth_levels, "ask_depth_levels")
        require_boolean(self.crossed, "crossed")
        require_boolean(self.locked, "locked")
        require_boolean(self.checksum_valid, "checksum_valid")
        require_boolean(self.level_monotonicity_valid, "level_monotonicity_valid")
        validate_health_state(self.health_status)
        if not self.book_health_score.is_finite():
            raise BookIntegrityValidationError("book health score must be finite")
        if not Decimal("0") <= self.book_health_score <= Decimal("100"):
            raise BookIntegrityValidationError("book health score must be in [0,100]")

    def _validate_components(self) -> None:
        if {component.name for component in self.components} != COMPONENT_NAMES:
            raise BookIntegrityValidationError("Lot 40 health component set changed")
        if len(self.components) != len(COMPONENT_NAMES):
            raise BookIntegrityValidationError("Lot 40 health components must be unique")
        total_weight = sum((component.weight for component in self.components), Decimal("0"))
        total_score = sum((component.score for component in self.components), Decimal("0"))
        if total_weight != Decimal("100"):
            raise BookIntegrityValidationError("Lot 40 component weights must total 100")
        if total_score != self.book_health_score:
            raise BookIntegrityValidationError("book health score/component total mismatch")
        if self.health_status != _expected_health_status(self.components):
            raise BookIntegrityValidationError("book health status/component mismatch")
        validate_reason_codes(self.reason_codes)

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("integrity_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-integrity-state-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "decision_time": self.decision_time,
            "sequence_id": self.sequence_id,
            "synchronization_state": self.synchronization_state,
            "stale_age_us": self.stale_age_us,
            "bid_depth_levels": self.bid_depth_levels,
            "ask_depth_levels": self.ask_depth_levels,
            "crossed": self.crossed,
            "locked": self.locked,
            "checksum_valid": self.checksum_valid,
            "level_monotonicity_valid": self.level_monotonicity_valid,
            "health_status": self.health_status,
            "book_health_score": decimal_text(self.book_health_score),
            "components": [component.to_dict() for component in self.components],
            "reason_codes": list(self.reason_codes),
            "integrity_checksum": self.integrity_checksum,
        }


@dataclass(frozen=True, slots=True)
class BookHealthVetoV1:
    consequence: str
    veto_active: bool
    critical_veto_active: bool
    trade_health_threshold: Decimal
    system_health_threshold: Decimal
    critical_failure_consequence: str
    system_threshold_consequence: str
    book_health_score: Decimal
    reason_codes: tuple[str, ...]
    veto_checksum: str

    def __post_init__(self) -> None:
        validate_consequence(self.consequence)
        validate_consequence(self.critical_failure_consequence)
        validate_consequence(self.system_threshold_consequence)
        require_boolean(self.veto_active, "veto_active")
        require_boolean(self.critical_veto_active, "critical_veto_active")
        self._validate_thresholds()
        self._validate_consequence()
        validate_reason_codes(self.reason_codes)
        require_sha256(self.veto_checksum, "veto_checksum")

    def _validate_thresholds(self) -> None:
        values = (
            self.book_health_score,
            self.system_health_threshold,
            self.trade_health_threshold,
        )
        if any(not value.is_finite() for value in values):
            raise BookIntegrityValidationError("health thresholds and score must be finite")
        if not Decimal("0") <= self.system_health_threshold <= self.trade_health_threshold <= Decimal("100"):
            raise BookIntegrityValidationError("invalid Lot 40 health threshold ordering")
        if not Decimal("0") <= self.book_health_score <= Decimal("100"):
            raise BookIntegrityValidationError("veto score must be in [0,100]")
        if self.critical_failure_consequence != "BLOCK":
            raise BookIntegrityValidationError("critical Lot 40 failures must BLOCK")
        if self.system_threshold_consequence != "PAUSE":
            raise BookIntegrityValidationError("Lot 40 system threshold must PAUSE")

    def _validate_consequence(self) -> None:
        expected = "NONE"
        if self.critical_veto_active:
            expected = self.critical_failure_consequence
        elif self.book_health_score < self.system_health_threshold:
            expected = self.system_threshold_consequence
        elif self.book_health_score < self.trade_health_threshold:
            expected = "WAIT"
        if self.consequence != expected:
            raise BookIntegrityValidationError("Lot 40 veto consequence mismatch")
        if self.veto_active != (self.consequence != "NONE"):
            raise BookIntegrityValidationError("Lot 40 veto_active mismatch")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("veto_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-health-veto-v1",
            "consequence": self.consequence,
            "veto_active": self.veto_active,
            "critical_veto_active": self.critical_veto_active,
            "trade_health_threshold": decimal_text(self.trade_health_threshold),
            "system_health_threshold": decimal_text(self.system_health_threshold),
            "critical_failure_consequence": self.critical_failure_consequence,
            "system_threshold_consequence": self.system_threshold_consequence,
            "book_health_score": decimal_text(self.book_health_score),
            "reason_codes": list(self.reason_codes),
            "veto_checksum": self.veto_checksum,
        }


@dataclass(frozen=True, slots=True)
class Lot40MetricsV1:
    health_components_total: int
    health_components_failed_total: int
    critical_components_failed_total: int
    bid_depth_levels: int
    ask_depth_levels: int
    stale_age_us: int
    processing_latency_us: int | None = None
    latency_measurement_status: str = "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY"

    def __post_init__(self) -> None:
        for value, field in self._integer_fields():
            require_integer(value, field)
        if self.health_components_failed_total > self.health_components_total:
            raise BookIntegrityValidationError("failed components exceed component total")
        if self.critical_components_failed_total > self.health_components_failed_total:
            raise BookIntegrityValidationError("critical failures exceed total failures")
        if self.processing_latency_us is not None:
            require_integer(self.processing_latency_us, "processing_latency_us")
        require_text(self.latency_measurement_status, "latency_measurement_status")

    def _integer_fields(self) -> tuple[tuple[int, str], ...]:
        return (
            (self.health_components_total, "health_components_total"),
            (self.health_components_failed_total, "health_components_failed_total"),
            (self.critical_components_failed_total, "critical_components_failed_total"),
            (self.bid_depth_levels, "bid_depth_levels"),
            (self.ask_depth_levels, "ask_depth_levels"),
            (self.stale_age_us, "stale_age_us"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot40-metrics-v1",
            "lot_40_records_processed_total": 1,
            "lot_40_health_components_total": self.health_components_total,
            "lot_40_health_components_failed_total": self.health_components_failed_total,
            "lot_40_critical_components_failed_total": self.critical_components_failed_total,
            "lot_40_bid_depth_levels": self.bid_depth_levels,
            "lot_40_ask_depth_levels": self.ask_depth_levels,
            "lot_40_stale_age_us": self.stale_age_us,
            "lot_40_validation_failures_total": 0,
            "lot_40_processing_latency_us": self.processing_latency_us,
            "latency_measurement_status": self.latency_measurement_status,
        }


@dataclass(frozen=True, slots=True)
class BookIntegrityDesynchronizationDetectorStateV1:
    run_context: Lot40RunContextV1
    lineage: Lot40LineageEnvelopeV1
    event_time: str
    receive_time: str
    decision_time: str
    generated_at: str
    validation_state: str
    book_integrity: BookIntegrityStateV1
    book_health_veto: BookHealthVetoV1
    metrics: Lot40MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        validate_causal_times(
            self.event_time,
            self.receive_time,
            self.decision_time,
            self.generated_at,
        )
        if self.validation_state != VALIDATION_STATE:
            raise BookIntegrityValidationError("unknown Lot 40 validation state")
        if self.book_integrity.book_health_score != self.book_health_veto.book_health_score:
            raise BookIntegrityValidationError("Lot 40 integrity/veto score mismatch")
        validate_reason_codes(self.reason_codes)
        validate_lot40_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-integrity-desynchronization-detector-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "decision_time": self.decision_time,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "book_integrity": self.book_integrity.to_dict(),
            "book_health_veto": self.book_health_veto.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class BookIntegrityDesynchronizationDetectorAuditV1:
    code_commit: str
    config_checksum: str
    entry_gate_checksum: str
    lot39_state_checksum: str
    lot39_audit_checksum: str
    lot39_reconstructed_book_checksum: str
    lot39_delta_fixture_checksum: str
    state_output_checksum: str
    integrity_checksum: str
    veto_checksum: str
    health_status: str
    consequence: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit, "code_commit")
        for value, field in self._checksums():
            require_sha256(value, field)
        validate_health_state(self.health_status)
        validate_consequence(self.consequence)
        validate_lot40_safety(self.safety)

    def _checksums(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.config_checksum, "config_checksum"),
            (self.entry_gate_checksum, "entry_gate_checksum"),
            (self.lot39_state_checksum, "lot39_state_checksum"),
            (self.lot39_audit_checksum, "lot39_audit_checksum"),
            (self.lot39_reconstructed_book_checksum, "lot39_reconstructed_book_checksum"),
            (self.lot39_delta_fixture_checksum, "lot39_delta_fixture_checksum"),
            (self.state_output_checksum, "state_output_checksum"),
            (self.integrity_checksum, "integrity_checksum"),
            (self.veto_checksum, "veto_checksum"),
            (self.audit_checksum, "audit_checksum"),
        )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-integrity-desynchronization-detector-audit-v1",
            "code_commit": self.code_commit,
            "config_checksum": self.config_checksum,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot39_state_checksum": self.lot39_state_checksum,
            "lot39_audit_checksum": self.lot39_audit_checksum,
            "lot39_reconstructed_book_checksum": self.lot39_reconstructed_book_checksum,
            "lot39_delta_fixture_checksum": self.lot39_delta_fixture_checksum,
            "state_output_checksum": self.state_output_checksum,
            "integrity_checksum": self.integrity_checksum,
            "veto_checksum": self.veto_checksum,
            "health_status": self.health_status,
            "consequence": self.consequence,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }


__all__ = [
    "VALIDATION_STATE",
    "BookHealthComponentV1",
    "BookHealthVetoV1",
    "BookIntegrityDesynchronizationDetectorAuditV1",
    "BookIntegrityDesynchronizationDetectorStateV1",
    "BookIntegrityStateV1",
    "Lot40LineageEnvelopeV1",
    "Lot40MetricsV1",
    "Lot40RunContextV1",
]
