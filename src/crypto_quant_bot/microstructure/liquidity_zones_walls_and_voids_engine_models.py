from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .liquidity_zones_walls_and_voids_engine_validation import (
    ACTIVE,
    DISPLAYED_WALL,
    LIQUIDITY_VOID,
    NOT_APPLICABLE,
    PARTICIPANT_INTENT,
    RUNTIME_MODE,
    VALIDATION_STATE,
    decimal_text,
    require_integer,
    require_sha256,
    require_text,
    validate_checksum_fields,
    validate_classifications,
    validate_confidence,
    validate_identity_fields,
    validate_lot42_safety,
    validate_nonnegative,
    validate_positive,
    validate_ratio,
    validate_reason_codes,
    validate_run_context,
    validate_sequence_ids,
    validate_side,
)


@dataclass(frozen=True, slots=True)
class Lot42RunContextV1:
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
            "schema_version": "lot42-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": RUNTIME_MODE,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot42LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot41_state_checksum: str
    lot41_audit_checksum: str
    lot41_feature_checksum: str
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
            (self.lot41_state_checksum, "lot41_state_checksum"),
            (self.lot41_audit_checksum, "lot41_audit_checksum"),
            (self.lot41_feature_checksum, "lot41_feature_checksum"),
            (self.lot39_book_checksum, "lot39_book_checksum"),
            (self.lot39_delta_fixture_checksum, "lot39_delta_fixture_checksum"),
            (self.lot38_snapshot_checksum, "lot38_snapshot_checksum"),
            (self.config_checksum, "config_checksum"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot42-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot41_state_checksum": self.lot41_state_checksum,
            "lot41_audit_checksum": self.lot41_audit_checksum,
            "lot41_feature_checksum": self.lot41_feature_checksum,
            "lot39_book_checksum": self.lot39_book_checksum,
            "lot39_delta_fixture_checksum": self.lot39_delta_fixture_checksum,
            "lot38_snapshot_checksum": self.lot38_snapshot_checksum,
            "config_checksum": self.config_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class LiquidityZoneV1:
    zone_id: str
    side: str
    lower_price: Decimal
    upper_price: Decimal
    anchor_price: Decimal
    level_count: int
    quantity: Decimal
    notional: Decimal
    persistence_observations: int
    total_observations: int
    persistence_ratio: Decimal
    replenished_quantity: Decimal
    replenishment_ratio: Decimal
    cancelled_quantity: Decimal
    cancellation_rate: Decimal
    distance_to_mid_bps: Decimal
    classifications: tuple[str, ...]
    confidence_status: str
    lifecycle_status: str
    participant_intent: str
    reason_codes: tuple[str, ...]
    zone_checksum: str

    def __post_init__(self) -> None:
        require_text(self.zone_id, "zone_id")
        validate_side(self.side)
        self._validate_numeric()
        self._validate_semantics()
        validate_reason_codes(self.reason_codes)
        require_sha256(self.zone_checksum, "zone_checksum")

    def _validate_numeric(self) -> None:
        for value, field in (
            (self.lower_price, "lower_price"),
            (self.upper_price, "upper_price"),
            (self.anchor_price, "anchor_price"),
            (self.quantity, "quantity"),
            (self.notional, "notional"),
        ):
            validate_positive(value, field)
        for value, field in (
            (self.replenished_quantity, "replenished_quantity"),
            (self.replenishment_ratio, "replenishment_ratio"),
            (self.cancelled_quantity, "cancelled_quantity"),
            (self.distance_to_mid_bps, "distance_to_mid_bps"),
        ):
            validate_nonnegative(value, field)
        validate_ratio(self.persistence_ratio, "persistence_ratio")
        validate_ratio(self.cancellation_rate, "cancellation_rate")

    def _validate_semantics(self) -> None:
        require_integer(self.level_count, "level_count", minimum=1)
        require_integer(self.persistence_observations, "persistence_observations", minimum=1)
        require_integer(self.total_observations, "total_observations", minimum=1)
        if self.persistence_observations > self.total_observations:
            raise ValueError("persistence observations exceed total observations")
        expected_ratio = Decimal(self.persistence_observations) / Decimal(self.total_observations)
        if self.persistence_ratio != expected_ratio:
            raise ValueError("persistence ratio/count mismatch")
        if self.lower_price > self.anchor_price or self.anchor_price > self.upper_price:
            raise ValueError("zone anchor outside price bounds")
        validate_classifications(self.classifications)
        validate_confidence(self.confidence_status)
        if self.lifecycle_status != ACTIVE or self.participant_intent != PARTICIPANT_INTENT:
            raise ValueError("Lot 42 active-zone lifecycle or intent changed")
        if DISPLAYED_WALL not in self.classifications and self.confidence_status != NOT_APPLICABLE:
            raise ValueError("non-wall zone confidence must be not applicable")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("zone_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity-zone-v1",
            "zone_id": self.zone_id,
            "side": self.side,
            "lower_price": decimal_text(self.lower_price),
            "upper_price": decimal_text(self.upper_price),
            "anchor_price": decimal_text(self.anchor_price),
            "level_count": self.level_count,
            "quantity": decimal_text(self.quantity),
            "notional": decimal_text(self.notional),
            "persistence_observations": self.persistence_observations,
            "total_observations": self.total_observations,
            "persistence_ratio": decimal_text(self.persistence_ratio),
            "replenished_quantity": decimal_text(self.replenished_quantity),
            "replenishment_ratio": decimal_text(self.replenishment_ratio),
            "cancelled_quantity": decimal_text(self.cancelled_quantity),
            "cancellation_rate": decimal_text(self.cancellation_rate),
            "distance_to_mid_bps": decimal_text(self.distance_to_mid_bps),
            "classifications": list(self.classifications),
            "confidence_status": self.confidence_status,
            "lifecycle_status": self.lifecycle_status,
            "participant_intent": self.participant_intent,
            "reason_codes": list(self.reason_codes),
            "zone_checksum": self.zone_checksum,
        }


@dataclass(frozen=True, slots=True)
class LiquidityVoidV1:
    void_id: str
    side: str
    near_price: Decimal
    far_price: Decimal
    gap_bps: Decimal
    distance_to_mid_bps: Decimal
    classification: str
    lifecycle_status: str
    participant_intent: str
    reason_codes: tuple[str, ...]
    void_checksum: str

    def __post_init__(self) -> None:
        require_text(self.void_id, "void_id")
        validate_side(self.side)
        validate_positive(self.near_price, "near_price")
        validate_positive(self.far_price, "far_price")
        validate_positive(self.gap_bps, "gap_bps")
        validate_nonnegative(self.distance_to_mid_bps, "distance_to_mid_bps")
        if self.classification != LIQUIDITY_VOID:
            raise ValueError("void classification changed")
        if self.lifecycle_status != ACTIVE or self.participant_intent != PARTICIPANT_INTENT:
            raise ValueError("Lot 42 void lifecycle or intent changed")
        validate_reason_codes(self.reason_codes)
        require_sha256(self.void_checksum, "void_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("void_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity-void-v1",
            "void_id": self.void_id,
            "side": self.side,
            "near_price": decimal_text(self.near_price),
            "far_price": decimal_text(self.far_price),
            "gap_bps": decimal_text(self.gap_bps),
            "distance_to_mid_bps": decimal_text(self.distance_to_mid_bps),
            "classification": self.classification,
            "lifecycle_status": self.lifecycle_status,
            "participant_intent": self.participant_intent,
            "reason_codes": list(self.reason_codes),
            "void_checksum": self.void_checksum,
        }


@dataclass(frozen=True, slots=True)
class LiquidityZoneSetV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    decision_time: str
    sequence_id: int
    mid_price: Decimal
    history_sequence_ids: tuple[int, ...]
    zones: tuple[LiquidityZoneV1, ...]
    voids: tuple[LiquidityVoidV1, ...]
    expired_candidates_total: int
    reason_codes: tuple[str, ...]
    zone_set_checksum: str

    def __post_init__(self) -> None:
        validate_identity_fields(self._identity_fields())
        require_integer(self.sequence_id, "sequence_id", minimum=1)
        validate_positive(self.mid_price, "mid_price")
        validate_sequence_ids(self.history_sequence_ids)
        require_integer(self.expired_candidates_total, "expired_candidates_total")
        if self.sequence_id != self.history_sequence_ids[-1]:
            raise ValueError("zone-set sequence must be latest history sequence")
        if not self.zones:
            raise ValueError("Lot 42 requires at least one active liquidity zone")
        validate_reason_codes(self.reason_codes)
        require_sha256(self.zone_set_checksum, "zone_set_checksum")

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
        payload.pop("zone_set_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity-zone-set-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "decision_time": self.decision_time,
            "sequence_id": self.sequence_id,
            "mid_price": decimal_text(self.mid_price),
            "history_sequence_ids": list(self.history_sequence_ids),
            "zones": [item.to_dict() for item in self.zones],
            "voids": [item.to_dict() for item in self.voids],
            "expired_candidates_total": self.expired_candidates_total,
            "observed_book_only": True,
            "participant_intent_inferred": False,
            "reason_codes": list(self.reason_codes),
            "zone_set_checksum": self.zone_set_checksum,
        }


@dataclass(frozen=True, slots=True)
class Lot42MetricsV1:
    observations_total: int
    active_zones_total: int
    displayed_walls_total: int
    persistent_zones_total: int
    low_confidence_walls_total: int
    liquidity_voids_total: int
    expired_candidates_total: int

    def __post_init__(self) -> None:
        values = (
            (self.observations_total, "observations_total"),
            (self.active_zones_total, "active_zones_total"),
            (self.displayed_walls_total, "displayed_walls_total"),
            (self.persistent_zones_total, "persistent_zones_total"),
            (self.low_confidence_walls_total, "low_confidence_walls_total"),
            (self.liquidity_voids_total, "liquidity_voids_total"),
            (self.expired_candidates_total, "expired_candidates_total"),
        )
        for value, field in values:
            require_integer(value, field)
        if self.displayed_walls_total > self.active_zones_total:
            raise ValueError("wall count exceeds active zones")
        if self.persistent_zones_total > self.active_zones_total:
            raise ValueError("persistent count exceeds active zones")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot42-metrics-v1",
            "lot_42_records_processed_total": 1,
            "lot_42_observations_total": self.observations_total,
            "lot_42_active_zones_total": self.active_zones_total,
            "lot_42_displayed_walls_total": self.displayed_walls_total,
            "lot_42_persistent_zones_total": self.persistent_zones_total,
            "lot_42_low_confidence_walls_total": self.low_confidence_walls_total,
            "lot_42_liquidity_voids_total": self.liquidity_voids_total,
            "lot_42_expired_candidates_total": self.expired_candidates_total,
            "lot_42_validation_failures_total": 0,
            "lot_42_processing_latency_us": None,
            "latency_measurement_status": "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY",
        }


@dataclass(frozen=True, slots=True)
class LiquidityZonesWallsVoidsEngineStateV1:
    run_context: Lot42RunContextV1
    lineage: Lot42LineageEnvelopeV1
    generated_at: str
    liquidity_zones: LiquidityZoneSetV1
    metrics: Lot42MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        require_text(self.generated_at, "generated_at")
        validate_reason_codes(self.reason_codes)
        validate_lot42_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity-zones-walls-voids-engine-state-v1",
            "validation_state": VALIDATION_STATE,
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.liquidity_zones.event_time,
            "receive_time": self.liquidity_zones.receive_time,
            "decision_time": self.liquidity_zones.decision_time,
            "generated_at": self.generated_at,
            "liquidity_zones": self.liquidity_zones.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class LiquidityZonesWallsVoidsEngineAuditV1:
    run_context: Lot42RunContextV1
    state_output_checksum: str
    zone_set_checksum: str
    lineage: Lot42LineageEnvelopeV1
    validation_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        validate_checksum_fields(
            (
                (self.state_output_checksum, "state_output_checksum"),
                (self.zone_set_checksum, "zone_set_checksum"),
                (self.audit_checksum, "audit_checksum"),
            )
        )
        if not self.validation_checks or len(set(self.validation_checks)) != len(self.validation_checks):
            raise ValueError("audit validation checks must be non-empty and unique")
        validate_reason_codes(self.reason_codes)
        validate_lot42_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity-zones-walls-voids-engine-audit-v1",
            "run_context": self.run_context.to_dict(),
            "state_output_checksum": self.state_output_checksum,
            "zone_set_checksum": self.zone_set_checksum,
            "lineage": self.lineage.to_dict(),
            "validation_checks": list(self.validation_checks),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
