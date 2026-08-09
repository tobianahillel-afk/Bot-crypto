from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
    decimal_text,
    parse_utc_timestamp,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_lot39_safety,
    validate_reason_codes,
    validate_run_context,
    validate_sync_state,
)
from .order_book_l2_snapshot_engine_models import OrderBookLevelV1

SUCCESS_STATE = "VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY"
BLOCKED_STATE = "BLOCKED_RESYNC_REQUIRED"


@dataclass(frozen=True, slots=True)
class Lot39RunContextV1:
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
            "schema_version": "lot39-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot39LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot38_state_checksum: str
    lot38_audit_checksum: str
    lot38_snapshot_checksum: str
    lot38_health_checksum: str
    delta_fixture_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        for value, field in self._checksums():
            require_sha256(value, field)
        parse_utc_timestamp(self.available_at, "available_at")

    def _checksums(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.entry_gate_checksum, "entry_gate_checksum"),
            (self.lot38_state_checksum, "lot38_state_checksum"),
            (self.lot38_audit_checksum, "lot38_audit_checksum"),
            (self.lot38_snapshot_checksum, "lot38_snapshot_checksum"),
            (self.lot38_health_checksum, "lot38_health_checksum"),
            (self.delta_fixture_checksum, "delta_fixture_checksum"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot39-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot38_state_checksum": self.lot38_state_checksum,
            "lot38_audit_checksum": self.lot38_audit_checksum,
            "lot38_snapshot_checksum": self.lot38_snapshot_checksum,
            "lot38_health_checksum": self.lot38_health_checksum,
            "delta_fixture_checksum": self.delta_fixture_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class OrderBookDeltaV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    sequence_id: int
    prev_sequence: int
    bids: tuple[OrderBookLevelV1, ...]
    asks: tuple[OrderBookLevelV1, ...]
    expected_book_checksum: str | None
    used_for_decision: bool = False

    def __post_init__(self) -> None:
        _validate_delta_identity(self)
        validate_causal_times(self.event_time, self.receive_time, self.receive_time)
        require_integer(self.sequence_id, "sequence_id")
        require_integer(self.prev_sequence, "prev_sequence")
        if not self.bids and not self.asks:
            raise OrderBookDeltaSequenceValidationError(
                "Lot 39 delta must change at least one side"
            )
        if self.expected_book_checksum is not None:
            require_sha256(self.expected_book_checksum, "expected_book_checksum")
        if self.used_for_decision is not False:
            raise OrderBookDeltaSequenceValidationError(
                "Lot 39 delta cannot be decision data"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-delta-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "sequence_id": self.sequence_id,
            "prev_sequence": self.prev_sequence,
            "bids": [level.to_dict() for level in self.bids],
            "asks": [level.to_dict() for level in self.asks],
            "expected_book_checksum": self.expected_book_checksum,
            "used_for_decision": False,
        }


def _validate_delta_identity(delta: OrderBookDeltaV1) -> None:
    for value, field in (
        (delta.source_id, "source_id"),
        (delta.venue, "venue"),
        (delta.instrument_id, "instrument_id"),
    ):
        require_text(value, field)
    if delta.market_type != "SPOT":
        raise OrderBookDeltaSequenceValidationError(
            "Lot 39 delta market_type must be SPOT"
        )


@dataclass(frozen=True, slots=True)
class ReconstructedOrderBookV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    base_snapshot_checksum: str
    base_sequence_id: int
    sequence_id: int
    sequence_anchor: str
    synchronization_state: str
    bids: tuple[OrderBookLevelV1, ...]
    asks: tuple[OrderBookLevelV1, ...]
    applied_delta_count: int
    book_checksum: str

    def __post_init__(self) -> None:
        _validate_reconstructed_identity(self)
        _validate_reconstructed_sequence(self)
        _validate_reconstructed_levels(self)
        require_sha256(self.book_checksum, "book_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("book_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "reconstructed-order-book-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "base_snapshot_checksum": self.base_snapshot_checksum,
            "base_sequence_id": self.base_sequence_id,
            "sequence_id": self.sequence_id,
            "sequence_anchor": self.sequence_anchor,
            "synchronization_state": self.synchronization_state,
            "bids": [level.to_dict() for level in self.bids],
            "asks": [level.to_dict() for level in self.asks],
            "applied_delta_count": self.applied_delta_count,
            "book_checksum": self.book_checksum,
        }


def _validate_reconstructed_identity(book: ReconstructedOrderBookV1) -> None:
    for value, field in (
        (book.source_id, "source_id"),
        (book.venue, "venue"),
        (book.instrument_id, "instrument_id"),
    ):
        require_text(value, field)
    if book.market_type != "SPOT":
        raise OrderBookDeltaSequenceValidationError(
            "reconstructed market_type must be SPOT"
        )
    validate_causal_times(book.event_time, book.receive_time, book.receive_time)


def _validate_reconstructed_sequence(book: ReconstructedOrderBookV1) -> None:
    require_sha256(book.base_snapshot_checksum, "base_snapshot_checksum")
    require_integer(book.base_sequence_id, "base_sequence_id")
    require_integer(book.sequence_id, "sequence_id")
    if book.sequence_id <= book.base_sequence_id:
        raise OrderBookDeltaSequenceValidationError(
            "reconstructed sequence must advance"
        )
    require_sha256(book.sequence_anchor, "sequence_anchor")
    if book.synchronization_state != "SYNCED":
        raise OrderBookDeltaSequenceValidationError(
            "only SYNCED books may be published"
        )
    require_integer(book.applied_delta_count, "applied_delta_count", minimum=1)


def _validate_reconstructed_levels(book: ReconstructedOrderBookV1) -> None:
    if not book.bids or not book.asks:
        raise OrderBookDeltaSequenceValidationError(
            "reconstructed book sides must be non-empty"
        )
    if tuple(sorted(book.bids, key=lambda level: level.price, reverse=True)) != book.bids:
        raise OrderBookDeltaSequenceValidationError(
            "reconstructed bids must be descending"
        )
    if tuple(sorted(book.asks, key=lambda level: level.price)) != book.asks:
        raise OrderBookDeltaSequenceValidationError(
            "reconstructed asks must be ascending"
        )
    if book.bids[0].price >= book.asks[0].price:
        raise OrderBookDeltaSequenceValidationError(
            "crossed or locked reconstructed book forbidden"
        )


@dataclass(frozen=True, slots=True)
class SequenceGapEventV1:
    gap_detected: bool
    synchronization_state: str
    expected_sequence: int
    observed_sequence: int | None
    observed_prev_sequence: int | None
    event_time: str
    reason_codes: tuple[str, ...]
    event_checksum: str

    def __post_init__(self) -> None:
        _validate_gap_event(self)
        require_sha256(self.event_checksum, "event_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("event_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "sequence-gap-event-v1",
            "gap_detected": self.gap_detected,
            "synchronization_state": self.synchronization_state,
            "expected_sequence": self.expected_sequence,
            "observed_sequence": self.observed_sequence,
            "observed_prev_sequence": self.observed_prev_sequence,
            "event_time": self.event_time,
            "reason_codes": list(self.reason_codes),
            "event_checksum": self.event_checksum,
        }


def _validate_gap_event(event: SequenceGapEventV1) -> None:
    if not isinstance(event.gap_detected, bool):
        raise OrderBookDeltaSequenceValidationError("gap_detected must be boolean")
    validate_sync_state(event.synchronization_state)
    require_integer(event.expected_sequence, "expected_sequence")
    parse_utc_timestamp(event.event_time, "event_time")
    validate_reason_codes(event.reason_codes)
    observed = (event.observed_sequence, event.observed_prev_sequence)
    if event.gap_detected:
        if event.synchronization_state != "RESYNC_REQUIRED" or None in observed:
            raise OrderBookDeltaSequenceValidationError(
                "detected gap requires resync and observed sequence"
            )
        require_integer(event.observed_sequence, "observed_sequence")
        require_integer(event.observed_prev_sequence, "observed_prev_sequence")
    elif event.synchronization_state != "SYNCED" or observed != (None, None):
        raise OrderBookDeltaSequenceValidationError(
            "no-gap event must remain SYNCED without observed gap"
        )


@dataclass(frozen=True, slots=True)
class Lot39MetricsV1:
    deltas_received_total: int
    deltas_applied_total: int
    levels_deleted_total: int
    levels_upserted_total: int
    sequence_gap_events_total: int
    final_sequence_id: int
    processing_latency_us: int | None = None
    latency_measurement_status: str = "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY"

    def __post_init__(self) -> None:
        for value, field in self._integer_fields():
            require_integer(value, field)
        if self.deltas_applied_total > self.deltas_received_total:
            raise OrderBookDeltaSequenceValidationError(
                "applied deltas exceed received deltas"
            )
        if self.processing_latency_us is not None:
            require_integer(self.processing_latency_us, "processing_latency_us")
        require_text(self.latency_measurement_status, "latency_measurement_status")

    def _integer_fields(self) -> tuple[tuple[int, str], ...]:
        return (
            (self.deltas_received_total, "deltas_received_total"),
            (self.deltas_applied_total, "deltas_applied_total"),
            (self.levels_deleted_total, "levels_deleted_total"),
            (self.levels_upserted_total, "levels_upserted_total"),
            (self.sequence_gap_events_total, "sequence_gap_events_total"),
            (self.final_sequence_id, "final_sequence_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot39-metrics-v1",
            "lot_39_deltas_received_total": self.deltas_received_total,
            "lot_39_deltas_applied_total": self.deltas_applied_total,
            "lot_39_levels_deleted_total": self.levels_deleted_total,
            "lot_39_levels_upserted_total": self.levels_upserted_total,
            "lot_39_sequence_gap_events_total": self.sequence_gap_events_total,
            "lot_39_final_sequence_id": self.final_sequence_id,
            "lot_39_processing_latency_us": self.processing_latency_us,
            "latency_measurement_status": self.latency_measurement_status,
        }


def _validate_state_outcome(
    validation_state: str,
    synchronization_state: str,
    reconstructed_book: ReconstructedOrderBookV1 | None,
    sequence_gap_event: SequenceGapEventV1 | None,
) -> None:
    validate_sync_state(synchronization_state)
    if synchronization_state == "SYNCED":
        if validation_state != SUCCESS_STATE or reconstructed_book is None:
            raise OrderBookDeltaSequenceValidationError(
                "SYNCED Lot 39 state requires validated reconstructed book"
            )
        if reconstructed_book.synchronization_state != "SYNCED":
            raise OrderBookDeltaSequenceValidationError(
                "state/book synchronization mismatch"
            )
        if sequence_gap_event is not None:
            raise OrderBookDeltaSequenceValidationError(
                "SYNCED Lot 39 state cannot carry gap event"
            )
        return
    if validation_state != BLOCKED_STATE or reconstructed_book is not None:
        raise OrderBookDeltaSequenceValidationError(
            "RESYNC_REQUIRED Lot 39 state must be blocked without book"
        )
    if sequence_gap_event is None or not sequence_gap_event.gap_detected:
        raise OrderBookDeltaSequenceValidationError(
            "RESYNC_REQUIRED Lot 39 state requires gap evidence"
        )
    if sequence_gap_event.synchronization_state != "RESYNC_REQUIRED":
        raise OrderBookDeltaSequenceValidationError(
            "state/gap synchronization mismatch"
        )


@dataclass(frozen=True, slots=True)
class OrderBookDeltaSequenceReconstructorStateV1:
    run_context: Lot39RunContextV1
    lineage: Lot39LineageEnvelopeV1
    event_time: str
    receive_time: str
    generated_at: str
    validation_state: str
    synchronization_state: str
    base_snapshot_checksum: str
    delta_fixture_checksum: str
    reconstructed_book: ReconstructedOrderBookV1 | None
    sequence_gap_event: SequenceGapEventV1 | None
    metrics: Lot39MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        validate_causal_times(self.event_time, self.receive_time, self.generated_at)
        require_sha256(self.base_snapshot_checksum, "base_snapshot_checksum")
        require_sha256(self.delta_fixture_checksum, "delta_fixture_checksum")
        _validate_state_outcome(
            self.validation_state,
            self.synchronization_state,
            self.reconstructed_book,
            self.sequence_gap_event,
        )
        validate_reason_codes(self.reason_codes)
        validate_lot39_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-delta-sequence-reconstructor-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "synchronization_state": self.synchronization_state,
            "base_snapshot_checksum": self.base_snapshot_checksum,
            "delta_fixture_checksum": self.delta_fixture_checksum,
            "reconstructed_book": (
                None if self.reconstructed_book is None else self.reconstructed_book.to_dict()
            ),
            "sequence_gap_event": (
                None if self.sequence_gap_event is None else self.sequence_gap_event.to_dict()
            ),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


def _validate_audit_outcome(
    validation_state: str,
    synchronization_state: str,
    reconstructed_book_checksum: str | None,
    sequence_gap_event_checksum: str | None,
) -> None:
    validate_sync_state(synchronization_state)
    if synchronization_state == "SYNCED":
        if validation_state != SUCCESS_STATE or reconstructed_book_checksum is None:
            raise OrderBookDeltaSequenceValidationError(
                "SYNCED Lot 39 audit requires validated book checksum"
            )
        require_sha256(reconstructed_book_checksum, "reconstructed_book_checksum")
        if sequence_gap_event_checksum is not None:
            raise OrderBookDeltaSequenceValidationError(
                "SYNCED Lot 39 audit cannot carry gap checksum"
            )
        return
    if validation_state != BLOCKED_STATE or reconstructed_book_checksum is not None:
        raise OrderBookDeltaSequenceValidationError(
            "RESYNC_REQUIRED Lot 39 audit must be blocked without book checksum"
        )
    if sequence_gap_event_checksum is None:
        raise OrderBookDeltaSequenceValidationError(
            "RESYNC_REQUIRED Lot 39 audit requires gap checksum"
        )
    require_sha256(sequence_gap_event_checksum, "sequence_gap_event_checksum")


@dataclass(frozen=True, slots=True)
class OrderBookDeltaSequenceReconstructorAuditV1:
    code_commit: str
    config_checksum: str
    entry_gate_checksum: str
    lot38_state_checksum: str
    lot38_snapshot_checksum: str
    delta_fixture_checksum: str
    state_output_checksum: str
    reconstructed_book_checksum: str | None
    sequence_gap_event_checksum: str | None
    validation_state: str
    synchronization_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit, "code_commit")
        for value, field in self._required_checksums():
            require_sha256(value, field)
        _validate_audit_outcome(
            self.validation_state,
            self.synchronization_state,
            self.reconstructed_book_checksum,
            self.sequence_gap_event_checksum,
        )
        validate_lot39_safety(self.safety)

    def _required_checksums(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.config_checksum, "config_checksum"),
            (self.entry_gate_checksum, "entry_gate_checksum"),
            (self.lot38_state_checksum, "lot38_state_checksum"),
            (self.lot38_snapshot_checksum, "lot38_snapshot_checksum"),
            (self.delta_fixture_checksum, "delta_fixture_checksum"),
            (self.state_output_checksum, "state_output_checksum"),
            (self.audit_checksum, "audit_checksum"),
        )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-delta-sequence-reconstructor-audit-v1",
            "code_commit": self.code_commit,
            "config_checksum": self.config_checksum,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot38_state_checksum": self.lot38_state_checksum,
            "lot38_snapshot_checksum": self.lot38_snapshot_checksum,
            "delta_fixture_checksum": self.delta_fixture_checksum,
            "state_output_checksum": self.state_output_checksum,
            "reconstructed_book_checksum": self.reconstructed_book_checksum,
            "sequence_gap_event_checksum": self.sequence_gap_event_checksum,
            "validation_state": self.validation_state,
            "synchronization_state": self.synchronization_state,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
