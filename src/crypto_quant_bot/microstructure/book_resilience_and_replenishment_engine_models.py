from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .book_resilience_and_replenishment_engine_validation import (
    PARTICIPANT_INTENT,
    REGIME_METHOD,
    RUNTIME_MODE,
    VALIDATION_STATE,
    Lot43ValidationError,
    decimal_text,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_checksum_fields,
    validate_event_semantics,
    validate_horizons,
    validate_identity_fields,
    validate_lot43_safety,
    validate_nonnegative,
    validate_positive,
    validate_ratio,
    validate_reason_codes,
    validate_resilience_status,
    validate_run_context,
    validate_sequence_ids,
    validate_side,
    validate_slice_counts,
    validate_volatility_regime,
)


@dataclass(frozen=True, slots=True)
class Lot43RunContextV1:
    run_id: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        validate_run_context(
            self.run_id,
            RUNTIME_MODE,
            self.config_version,
            self.code_commit,
            self.correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot43-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": RUNTIME_MODE,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot43LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot42_state_checksum: str
    lot42_audit_checksum: str
    lot42_zone_set_checksum: str
    lot39_book_checksum: str
    lot39_delta_fixture_checksum: str
    lot38_snapshot_checksum: str
    config_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        require_text(self.available_at, "available_at")
        validate_checksum_fields(self._checksums())

    def _checksums(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.entry_gate_checksum, "entry_gate_checksum"),
            (self.lot42_state_checksum, "lot42_state_checksum"),
            (self.lot42_audit_checksum, "lot42_audit_checksum"),
            (self.lot42_zone_set_checksum, "lot42_zone_set_checksum"),
            (self.lot39_book_checksum, "lot39_book_checksum"),
            (self.lot39_delta_fixture_checksum, "lot39_delta_fixture_checksum"),
            (self.lot38_snapshot_checksum, "lot38_snapshot_checksum"),
            (self.config_checksum, "config_checksum"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot43-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot42_state_checksum": self.lot42_state_checksum,
            "lot42_audit_checksum": self.lot42_audit_checksum,
            "lot42_zone_set_checksum": self.lot42_zone_set_checksum,
            "lot39_book_checksum": self.lot39_book_checksum,
            "lot39_delta_fixture_checksum": self.lot39_delta_fixture_checksum,
            "lot38_snapshot_checksum": self.lot38_snapshot_checksum,
            "config_checksum": self.config_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class BookDepletionEventV1:
    event_id: str
    side: str
    depleted_price: Decimal
    previous_quantity: Decimal
    post_depletion_quantity: Decimal
    depleted_quantity: Decimal
    depletion_ratio: Decimal
    depletion_sequence_id: int
    depletion_event_time: str
    depletion_receive_time: str
    replenishment_kind: str
    replenishment_sequence_id: int | None
    replenishment_time_us: int | None
    replenished_quantity: Decimal
    recovered_fraction: Decimal
    directional_mid_shift_bps: Decimal
    max_window_status: str
    participant_intent: str
    reason_codes: tuple[str, ...]
    event_checksum: str

    def __post_init__(self) -> None:
        require_text(self.event_id, "event_id")
        validate_side(self.side)
        validate_positive(self.depleted_price, "depleted_price")
        validate_positive(self.previous_quantity, "previous_quantity")
        validate_nonnegative(self.post_depletion_quantity, "post_depletion_quantity")
        validate_positive(self.depleted_quantity, "depleted_quantity")
        validate_ratio(self.depletion_ratio, "depletion_ratio")
        require_integer(self.depletion_sequence_id, "depletion_sequence_id", minimum=1)
        require_text(self.depletion_event_time, "depletion_event_time")
        require_text(self.depletion_receive_time, "depletion_receive_time")
        if self.depleted_quantity != self.previous_quantity - self.post_depletion_quantity:
            raise Lot43ValidationError("depleted quantity/count mismatch")
        if self.depletion_ratio != self.depleted_quantity / self.previous_quantity:
            raise Lot43ValidationError("depletion ratio/count mismatch")
        validate_event_semantics(
            replenishment_kind=self.replenishment_kind,
            replenishment_sequence_id=self.replenishment_sequence_id,
            replenishment_time_us=self.replenishment_time_us,
            replenished_quantity=self.replenished_quantity,
            recovered_fraction=self.recovered_fraction,
            mid_shift_bps=self.directional_mid_shift_bps,
            max_window_status=self.max_window_status,
        )
        if self.participant_intent != PARTICIPANT_INTENT:
            raise Lot43ValidationError("participant intent must remain NOT_INFERRED")
        validate_reason_codes(self.reason_codes)
        require_sha256(self.event_checksum, "event_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("event_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-depletion-event-v1",
            "event_id": self.event_id,
            "side": self.side,
            "depleted_price": decimal_text(self.depleted_price),
            "previous_quantity": decimal_text(self.previous_quantity),
            "post_depletion_quantity": decimal_text(self.post_depletion_quantity),
            "depleted_quantity": decimal_text(self.depleted_quantity),
            "depletion_ratio": decimal_text(self.depletion_ratio),
            "depletion_sequence_id": self.depletion_sequence_id,
            "depletion_event_time": self.depletion_event_time,
            "depletion_receive_time": self.depletion_receive_time,
            "replenishment_kind": self.replenishment_kind,
            "replenishment_sequence_id": self.replenishment_sequence_id,
            "replenishment_time_us": self.replenishment_time_us,
            "replenished_quantity": decimal_text(self.replenished_quantity),
            "recovered_fraction": decimal_text(self.recovered_fraction),
            "directional_mid_shift_bps": decimal_text(self.directional_mid_shift_bps),
            "max_window_status": self.max_window_status,
            "participant_intent": self.participant_intent,
            "reason_codes": list(self.reason_codes),
            "event_checksum": self.event_checksum,
        }


def _validate_slice_means(
    depletion_events_total: int,
    recovered_events_total: int,
    mean_recovered_fraction: Decimal | None,
    mean_replenishment_time_us: Decimal | None,
) -> None:
    if mean_recovered_fraction is not None:
        validate_ratio(mean_recovered_fraction, "mean_recovered_fraction")
    if mean_replenishment_time_us is not None:
        validate_positive(mean_replenishment_time_us, "mean_replenishment_time_us")
    if recovered_events_total == 0 and mean_replenishment_time_us is not None:
        raise Lot43ValidationError("mean replenishment time requires recovered events")
    if recovered_events_total > 0 and mean_replenishment_time_us is None:
        raise Lot43ValidationError("recovered events require mean replenishment time")
    if depletion_events_total == 0 and mean_recovered_fraction is not None:
        raise Lot43ValidationError("empty slice cannot carry mean recovered fraction")
    if depletion_events_total > 0 and mean_recovered_fraction is None:
        raise Lot43ValidationError("non-empty slice requires mean recovered fraction")


@dataclass(frozen=True, slots=True)
class BookResilienceSliceV1:
    side: str
    horizon_us: int
    volatility_regime: str
    volatility_method: str
    depletion_events_total: int
    recovered_events_total: int
    mid_shift_events_total: int
    expired_events_total: int
    pending_events_total: int
    mean_recovered_fraction: Decimal | None
    mean_replenishment_time_us: Decimal | None
    resilience_status: str
    reason_codes: tuple[str, ...]
    slice_checksum: str

    def __post_init__(self) -> None:
        validate_side(self.side)
        require_integer(self.horizon_us, "horizon_us", minimum=1)
        validate_volatility_regime(self.volatility_regime)
        if self.volatility_method != REGIME_METHOD:
            raise Lot43ValidationError("volatility method changed")
        validate_slice_counts(
            self.depletion_events_total,
            self.recovered_events_total,
            self.mid_shift_events_total,
            self.expired_events_total,
            self.pending_events_total,
        )
        _validate_slice_means(
            self.depletion_events_total,
            self.recovered_events_total,
            self.mean_recovered_fraction,
            self.mean_replenishment_time_us,
        )
        validate_resilience_status(self.resilience_status)
        validate_reason_codes(self.reason_codes)
        require_sha256(self.slice_checksum, "slice_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("slice_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-resilience-slice-v1",
            "side": self.side,
            "horizon_us": self.horizon_us,
            "volatility_regime": self.volatility_regime,
            "volatility_method": self.volatility_method,
            "depletion_events_total": self.depletion_events_total,
            "recovered_events_total": self.recovered_events_total,
            "mid_shift_events_total": self.mid_shift_events_total,
            "expired_events_total": self.expired_events_total,
            "pending_events_total": self.pending_events_total,
            "mean_recovered_fraction": (
                None
                if self.mean_recovered_fraction is None
                else decimal_text(self.mean_recovered_fraction)
            ),
            "mean_replenishment_time_us": (
                None
                if self.mean_replenishment_time_us is None
                else decimal_text(self.mean_replenishment_time_us)
            ),
            "resilience_status": self.resilience_status,
            "reason_codes": list(self.reason_codes),
            "slice_checksum": self.slice_checksum,
        }


@dataclass(frozen=True, slots=True)
class BookResilienceStateV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    decision_time: str
    sequence_id: int
    history_sequence_ids: tuple[int, ...]
    volatility_measure_bps: Decimal
    volatility_regime: str
    volatility_method: str
    depletion_events: tuple[BookDepletionEventV1, ...]
    resilience_slices: tuple[BookResilienceSliceV1, ...]
    reason_codes: tuple[str, ...]
    resilience_checksum: str

    def __post_init__(self) -> None:
        validate_identity_fields(self._identity_fields())
        validate_causal_times(
            self.event_time,
            self.receive_time,
            self.decision_time,
            self.decision_time,
        )
        require_integer(self.sequence_id, "sequence_id", minimum=1)
        validate_sequence_ids(self.history_sequence_ids)
        if self.sequence_id != self.history_sequence_ids[-1]:
            raise Lot43ValidationError("resilience sequence must be latest history sequence")
        validate_nonnegative(self.volatility_measure_bps, "volatility_measure_bps")
        validate_volatility_regime(self.volatility_regime)
        if self.volatility_method != REGIME_METHOD:
            raise Lot43ValidationError("volatility method changed")
        horizons = tuple(sorted({item.horizon_us for item in self.resilience_slices}))
        if horizons:
            validate_horizons(horizons)
        validate_reason_codes(self.reason_codes)
        require_sha256(self.resilience_checksum, "resilience_checksum")

    def _identity_fields(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.source_id, "source_id"),
            (self.venue, "venue"),
            (self.instrument_id, "instrument_id"),
            (self.market_type, "market_type"),
            (self.event_time, "event_time"),
            (self.receive_time, "receive_time"),
            (self.decision_time, "decision_time"),
        )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("resilience_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-resilience-state-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "decision_time": self.decision_time,
            "sequence_id": self.sequence_id,
            "history_sequence_ids": list(self.history_sequence_ids),
            "volatility_measure_bps": decimal_text(self.volatility_measure_bps),
            "volatility_regime": self.volatility_regime,
            "volatility_method": self.volatility_method,
            "depletion_events": [item.to_dict() for item in self.depletion_events],
            "resilience_slices": [item.to_dict() for item in self.resilience_slices],
            "observed_book_only": True,
            "participant_intent_inferred": False,
            "reason_codes": list(self.reason_codes),
            "resilience_checksum": self.resilience_checksum,
        }


@dataclass(frozen=True, slots=True)
class Lot43MetricsV1:
    observations_total: int
    depletion_events_total: int
    same_price_replenishments_total: int
    adjacent_price_replenishments_total: int
    mid_shift_events_total: int
    expired_max_window_events_total: int
    pending_max_window_events_total: int

    def __post_init__(self) -> None:
        values = (
            (self.observations_total, "observations_total"),
            (self.depletion_events_total, "depletion_events_total"),
            (self.same_price_replenishments_total, "same_price_replenishments_total"),
            (self.adjacent_price_replenishments_total, "adjacent_price_replenishments_total"),
            (self.mid_shift_events_total, "mid_shift_events_total"),
            (self.expired_max_window_events_total, "expired_max_window_events_total"),
            (self.pending_max_window_events_total, "pending_max_window_events_total"),
        )
        for value, field in values:
            require_integer(value, field, minimum=0)
        if self.observations_total == 0:
            raise Lot43ValidationError("Lot 43 metrics require observations")
        outcomes = (
            self.same_price_replenishments_total
            + self.adjacent_price_replenishments_total
            + self.mid_shift_events_total
            + self.expired_max_window_events_total
            + self.pending_max_window_events_total
        )
        if outcomes != self.depletion_events_total:
            raise Lot43ValidationError("Lot 43 metric outcomes must partition depletion events")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot43-metrics-v1",
            "lot_43_records_processed_total": 1,
            "lot_43_observations_total": self.observations_total,
            "lot_43_depletion_events_total": self.depletion_events_total,
            "lot_43_same_price_replenishments_total": self.same_price_replenishments_total,
            "lot_43_adjacent_price_replenishments_total": self.adjacent_price_replenishments_total,
            "lot_43_mid_shift_events_total": self.mid_shift_events_total,
            "lot_43_expired_max_window_events_total": self.expired_max_window_events_total,
            "lot_43_pending_max_window_events_total": self.pending_max_window_events_total,
            "lot_43_validation_failures_total": 0,
            "lot_43_processing_latency_us": None,
            "latency_measurement_status": "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY",
        }


@dataclass(frozen=True, slots=True)
class BookResilienceReplenishmentEngineStateV1:
    run_context: Lot43RunContextV1
    lineage: Lot43LineageEnvelopeV1
    generated_at: str
    book_resilience: BookResilienceStateV1
    metrics: Lot43MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        require_text(self.generated_at, "generated_at")
        validate_reason_codes(self.reason_codes)
        validate_lot43_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-resilience-replenishment-engine-state-v1",
            "validation_state": VALIDATION_STATE,
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.book_resilience.event_time,
            "receive_time": self.book_resilience.receive_time,
            "decision_time": self.book_resilience.decision_time,
            "generated_at": self.generated_at,
            "book_resilience": self.book_resilience.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class BookResilienceReplenishmentEngineAuditV1:
    run_context: Lot43RunContextV1
    state_output_checksum: str
    resilience_checksum: str
    lineage: Lot43LineageEnvelopeV1
    validation_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        validate_checksum_fields(
            (
                (self.state_output_checksum, "state_output_checksum"),
                (self.resilience_checksum, "resilience_checksum"),
                (self.audit_checksum, "audit_checksum"),
            )
        )
        if not self.validation_checks or len(set(self.validation_checks)) != len(
            self.validation_checks
        ):
            raise Lot43ValidationError("audit validation checks must be non-empty and unique")
        validate_reason_codes(self.reason_codes)
        validate_lot43_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-resilience-replenishment-engine-audit-v1",
            "run_context": self.run_context.to_dict(),
            "state_output_checksum": self.state_output_checksum,
            "resilience_checksum": self.resilience_checksum,
            "lineage": self.lineage.to_dict(),
            "validation_checks": list(self.validation_checks),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
