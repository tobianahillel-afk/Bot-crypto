from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise
from typing import Any

from .order_book_l2_snapshot_engine_validation import (
    OrderBookL2SnapshotValidationError,
    decimal_text,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_lot38_run_context,
    validate_lot38_safety,
    validate_reason_codes,
    validate_venue_state,
)


@dataclass(frozen=True, slots=True)
class Lot38RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        validate_lot38_run_context(
            self.run_id,
            self.runtime_mode,
            self.config_version,
            self.code_commit,
            self.correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot38-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot38LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot37_state_checksum: str
    lot37_audit_checksum: str
    lot37_contract_registry_checksum: str
    lot37_capability_matrix_checksum: str
    input_fixture_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        for field, value in (
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("lot37_state_checksum", self.lot37_state_checksum),
            ("lot37_audit_checksum", self.lot37_audit_checksum),
            ("lot37_contract_registry_checksum", self.lot37_contract_registry_checksum),
            ("lot37_capability_matrix_checksum", self.lot37_capability_matrix_checksum),
            ("input_fixture_checksum", self.input_fixture_checksum),
        ):
            require_sha256(value, field)
        validate_causal_times(self.available_at, self.available_at, self.available_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot38-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot37_state_checksum": self.lot37_state_checksum,
            "lot37_audit_checksum": self.lot37_audit_checksum,
            "lot37_contract_registry_checksum": self.lot37_contract_registry_checksum,
            "lot37_capability_matrix_checksum": self.lot37_capability_matrix_checksum,
            "input_fixture_checksum": self.input_fixture_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class OrderBookLevelV1:
    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if not self.price.is_finite() or self.price <= 0:
            raise OrderBookL2SnapshotValidationError(
                "book price must be positive finite Decimal"
            )
        if not self.quantity.is_finite() or self.quantity < 0:
            raise OrderBookL2SnapshotValidationError(
                "book quantity must be non-negative finite Decimal"
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "price": decimal_text(self.price),
            "quantity": decimal_text(self.quantity),
        }


@dataclass(frozen=True, slots=True)
class OrderBookSnapshotRawV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    sequence_id: int
    venue_state: str
    bids: tuple[OrderBookLevelV1, ...]
    asks: tuple[OrderBookLevelV1, ...]
    used_for_decision: bool

    def __post_init__(self) -> None:
        for field, value in (
            ("source_id", self.source_id),
            ("venue", self.venue),
            ("instrument_id", self.instrument_id),
        ):
            require_text(value, field)
        if self.market_type != "SPOT":
            raise OrderBookL2SnapshotValidationError(
                "Lot 38 reference contract is SPOT only"
            )
        validate_causal_times(self.event_time, self.receive_time, self.receive_time)
        require_integer(self.sequence_id, "sequence_id")
        validate_venue_state(self.venue_state)
        if not self.bids or not self.asks:
            raise OrderBookL2SnapshotValidationError(
                "raw snapshot requires bid and ask levels"
            )
        if self.used_for_decision is not False:
            raise OrderBookL2SnapshotValidationError(
                "Lot 38 raw snapshot cannot be decision data"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-snapshot-raw-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "sequence_id": self.sequence_id,
            "venue_state": self.venue_state,
            "bids": [level.to_dict() for level in self.bids],
            "asks": [level.to_dict() for level in self.asks],
            "used_for_decision": self.used_for_decision,
        }


@dataclass(frozen=True, slots=True)
class OrderBookSnapshotV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    sequence_id: int
    sequence_anchor: str
    venue_state: str
    bids: tuple[OrderBookLevelV1, ...]
    asks: tuple[OrderBookLevelV1, ...]
    source_bid_depth: int
    source_ask_depth: int
    normalized_bid_depth: int
    normalized_ask_depth: int
    published_bid_depth: int
    published_ask_depth: int
    snapshot_checksum: str

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_depths()
        self._validate_ordering()
        self._validate_book_state()
        require_sha256(self.sequence_anchor, "sequence_anchor")
        require_sha256(self.snapshot_checksum, "snapshot_checksum")

    def _validate_identity(self) -> None:
        for field, value in (
            ("source_id", self.source_id),
            ("venue", self.venue),
            ("instrument_id", self.instrument_id),
        ):
            require_text(value, field)
        if self.market_type != "SPOT":
            raise OrderBookL2SnapshotValidationError("canonical snapshot must be SPOT")
        validate_causal_times(self.event_time, self.receive_time, self.receive_time)
        require_integer(self.sequence_id, "sequence_id")
        validate_venue_state(self.venue_state)
        if not self.bids or not self.asks:
            raise OrderBookL2SnapshotValidationError(
                "canonical snapshot cannot be empty"
            )

    def _validate_depths(self) -> None:
        for field, value in (
            ("source_bid_depth", self.source_bid_depth),
            ("source_ask_depth", self.source_ask_depth),
            ("normalized_bid_depth", self.normalized_bid_depth),
            ("normalized_ask_depth", self.normalized_ask_depth),
            ("published_bid_depth", self.published_bid_depth),
            ("published_ask_depth", self.published_ask_depth),
        ):
            require_integer(value, field, minimum=1)
        if self.published_bid_depth != len(self.bids):
            raise OrderBookL2SnapshotValidationError("published bid depth mismatch")
        if self.published_ask_depth != len(self.asks):
            raise OrderBookL2SnapshotValidationError("published ask depth mismatch")
        if self.published_bid_depth > self.normalized_bid_depth:
            raise OrderBookL2SnapshotValidationError(
                "published bid depth exceeds normalized depth"
            )
        if self.published_ask_depth > self.normalized_ask_depth:
            raise OrderBookL2SnapshotValidationError(
                "published ask depth exceeds normalized depth"
            )

    def _validate_ordering(self) -> None:
        bid_prices = tuple(level.price for level in self.bids)
        ask_prices = tuple(level.price for level in self.asks)
        if any(left <= right for left, right in pairwise(bid_prices)):
            raise OrderBookL2SnapshotValidationError(
                "bids must be strictly descending"
            )
        if any(left >= right for left, right in pairwise(ask_prices)):
            raise OrderBookL2SnapshotValidationError(
                "asks must be strictly ascending"
            )

    def _validate_book_state(self) -> None:
        best_bid = self.bids[0].price
        best_ask = self.asks[0].price
        if best_bid > best_ask:
            raise OrderBookL2SnapshotValidationError("crossed book is forbidden")
        locked = best_bid == best_ask
        if locked != (self.venue_state == "LOCKED"):
            raise OrderBookL2SnapshotValidationError(
                "locked book requires explicit and exact LOCKED venue state"
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("snapshot_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-snapshot-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "sequence_id": self.sequence_id,
            "sequence_anchor": self.sequence_anchor,
            "venue_state": self.venue_state,
            "bids": [level.to_dict() for level in self.bids],
            "asks": [level.to_dict() for level in self.asks],
            "source_bid_depth": self.source_bid_depth,
            "source_ask_depth": self.source_ask_depth,
            "normalized_bid_depth": self.normalized_bid_depth,
            "normalized_ask_depth": self.normalized_ask_depth,
            "published_bid_depth": self.published_bid_depth,
            "published_ask_depth": self.published_ask_depth,
            "snapshot_checksum": self.snapshot_checksum,
        }


@dataclass(frozen=True, slots=True)
class BookHealthStateV1:
    health_status: str
    venue_state: str
    crossed: bool
    locked: bool
    sequence_present: bool
    source_bid_depth: int
    source_ask_depth: int
    normalized_bid_depth: int
    normalized_ask_depth: int
    published_bid_depth: int
    published_ask_depth: int
    reason_codes: tuple[str, ...]
    health_checksum: str

    def __post_init__(self) -> None:
        validate_venue_state(self.venue_state)
        expected_status = "LOCKED" if self.venue_state == "LOCKED" else "HEALTHY"
        if self.health_status != expected_status:
            raise OrderBookL2SnapshotValidationError("book health status mismatch")
        if self.crossed is not False:
            raise OrderBookL2SnapshotValidationError(
                "crossed health state cannot be published"
            )
        if self.locked != (self.venue_state == "LOCKED"):
            raise OrderBookL2SnapshotValidationError("book health lock flag mismatch")
        if self.sequence_present is not True:
            raise OrderBookL2SnapshotValidationError("sequence anchor is required")
        for field, value in self._depth_items():
            require_integer(value, field, minimum=1)
        validate_reason_codes(self.reason_codes)
        require_sha256(self.health_checksum, "health_checksum")

    def _depth_items(self) -> tuple[tuple[str, int], ...]:
        return (
            ("source_bid_depth", self.source_bid_depth),
            ("source_ask_depth", self.source_ask_depth),
            ("normalized_bid_depth", self.normalized_bid_depth),
            ("normalized_ask_depth", self.normalized_ask_depth),
            ("published_bid_depth", self.published_bid_depth),
            ("published_ask_depth", self.published_ask_depth),
        )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("health_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-health-state-v1",
            "health_status": self.health_status,
            "venue_state": self.venue_state,
            "crossed": self.crossed,
            "locked": self.locked,
            "sequence_present": self.sequence_present,
            **dict(self._depth_items()),
            "reason_codes": list(self.reason_codes),
            "health_checksum": self.health_checksum,
        }


@dataclass(frozen=True, slots=True)
class Lot38MetricsV1:
    source_levels_total: int
    normalized_levels_total: int
    duplicate_levels_aggregated_total: int
    published_levels_total: int

    def __post_init__(self) -> None:
        for field, value in (
            ("source_levels_total", self.source_levels_total),
            ("normalized_levels_total", self.normalized_levels_total),
            (
                "duplicate_levels_aggregated_total",
                self.duplicate_levels_aggregated_total,
            ),
            ("published_levels_total", self.published_levels_total),
        ):
            require_integer(value, field)
        if self.source_levels_total < self.normalized_levels_total:
            raise OrderBookL2SnapshotValidationError(
                "normalized levels exceed source levels"
            )
        if self.normalized_levels_total < self.published_levels_total:
            raise OrderBookL2SnapshotValidationError(
                "published levels exceed normalized levels"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot38-metrics-v1",
            "lot_38_records_processed_total": 1,
            "lot_38_source_levels_total": self.source_levels_total,
            "lot_38_normalized_levels_total": self.normalized_levels_total,
            "lot_38_duplicate_levels_aggregated_total": (
                self.duplicate_levels_aggregated_total
            ),
            "lot_38_published_levels_total": self.published_levels_total,
            "lot_38_validation_failures_total": 0,
            "lot_38_processing_latency_us": None,
            "latency_measurement_status": (
                "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY"
            ),
        }


@dataclass(frozen=True, slots=True)
class OrderBookL2SnapshotEngineStateV1:
    run_context: Lot38RunContextV1
    lineage: Lot38LineageEnvelopeV1
    event_time: str
    receive_time: str
    generated_at: str
    validation_state: str
    input_fixture_checksum: str
    snapshot: OrderBookSnapshotV1
    book_health: BookHealthStateV1
    metrics: Lot38MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        validate_causal_times(self.event_time, self.receive_time, self.generated_at)
        if self.validation_state != "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY":
            raise OrderBookL2SnapshotValidationError(
                "unknown Lot 38 validation state"
            )
        require_sha256(self.input_fixture_checksum, "input_fixture_checksum")
        if self.lineage.input_fixture_checksum != self.input_fixture_checksum:
            raise OrderBookL2SnapshotValidationError(
                "state lineage input checksum mismatch"
            )
        validate_reason_codes(self.reason_codes)
        validate_lot38_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-l2-snapshot-engine-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "input_fixture_checksum": self.input_fixture_checksum,
            "snapshot": self.snapshot.to_dict(),
            "book_health": self.book_health.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class OrderBookL2SnapshotEngineAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    entry_gate_checksum: str
    input_fixture_checksum: str
    snapshot_checksum: str
    health_checksum: str
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit, "code_commit")
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("input_fixture_checksum", self.input_fixture_checksum),
            ("snapshot_checksum", self.snapshot_checksum),
            ("health_checksum", self.health_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        if self.validation_state != "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY":
            raise OrderBookL2SnapshotValidationError(
                "unknown Lot 38 audit state"
            )
        validate_lot38_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-book-l2-snapshot-engine-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "entry_gate_checksum": self.entry_gate_checksum,
            "input_fixture_checksum": self.input_fixture_checksum,
            "snapshot_checksum": self.snapshot_checksum,
            "health_checksum": self.health_checksum,
            "validation_state": self.validation_state,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
