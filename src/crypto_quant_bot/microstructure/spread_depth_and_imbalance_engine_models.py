from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise
from typing import Any

from .book_integrity_desynchronization_detector_validation import (
    decimal_text,
    require_integer,
    require_sha256,
    require_text,
    validate_reason_codes,
    validate_run_context,
)
from .spread_depth_and_imbalance_engine_validation import (
    COVERAGE_STATUS,
    IMBALANCE_DEFINED,
    IMBALANCE_UNDEFINED,
    RUNTIME_MODE,
    VALIDATION_STATE,
    Lot41ValidationError,
    validate_lot41_safety,
)


@dataclass(frozen=True, slots=True)
class Lot41RunContextV1:
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
            "schema_version": "lot41-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": RUNTIME_MODE,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot41LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot40_state_checksum: str
    lot40_audit_checksum: str
    lot40_integrity_checksum: str
    lot40_veto_checksum: str
    reconstructed_book_checksum: str
    config_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        require_text(self.available_at, "available_at")
        for value, field in self._checksums():
            require_sha256(value, field)

    def _checksums(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.entry_gate_checksum, "entry_gate_checksum"),
            (self.lot40_state_checksum, "lot40_state_checksum"),
            (self.lot40_audit_checksum, "lot40_audit_checksum"),
            (self.lot40_integrity_checksum, "lot40_integrity_checksum"),
            (self.lot40_veto_checksum, "lot40_veto_checksum"),
            (self.reconstructed_book_checksum, "reconstructed_book_checksum"),
            (self.config_checksum, "config_checksum"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot41-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot40_state_checksum": self.lot40_state_checksum,
            "lot40_audit_checksum": self.lot40_audit_checksum,
            "lot40_integrity_checksum": self.lot40_integrity_checksum,
            "lot40_veto_checksum": self.lot40_veto_checksum,
            "reconstructed_book_checksum": self.reconstructed_book_checksum,
            "config_checksum": self.config_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class TopOfBookV1:
    best_bid_price: Decimal
    best_bid_quantity: Decimal
    best_ask_price: Decimal
    best_ask_quantity: Decimal

    def __post_init__(self) -> None:
        values = (
            self.best_bid_price,
            self.best_bid_quantity,
            self.best_ask_price,
            self.best_ask_quantity,
        )
        if any(not value.is_finite() or value <= 0 for value in values):
            raise Lot41ValidationError(
                "top-of-book values must be finite and positive"
            )
        if self.best_bid_price >= self.best_ask_price:
            raise Lot41ValidationError("top-of-book must be open and uncrossed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot41-top-of-book-v1",
            "best_bid_price": decimal_text(self.best_bid_price),
            "best_bid_quantity": decimal_text(self.best_bid_quantity),
            "best_ask_price": decimal_text(self.best_ask_price),
            "best_ask_quantity": decimal_text(self.best_ask_quantity),
        }


@dataclass(frozen=True, slots=True)
class DepthBandV1:
    band_bps: Decimal
    bid_quantity: Decimal
    ask_quantity: Decimal
    bid_levels_observed: int
    ask_levels_observed: int
    imbalance: Decimal | None
    imbalance_status: str

    def __post_init__(self) -> None:
        if not self.band_bps.is_finite() or self.band_bps <= 0:
            raise Lot41ValidationError("depth band must be finite and positive")
        quantities = (self.bid_quantity, self.ask_quantity)
        if any(not value.is_finite() or value < 0 for value in quantities):
            raise Lot41ValidationError(
                "depth quantities must be finite and non-negative"
            )
        require_integer(self.bid_levels_observed, "bid_levels_observed")
        require_integer(self.ask_levels_observed, "ask_levels_observed")
        self._validate_imbalance()

    def _validate_imbalance(self) -> None:
        denominator = self.bid_quantity + self.ask_quantity
        if denominator == 0:
            if (
                self.imbalance is not None
                or self.imbalance_status != IMBALANCE_UNDEFINED
            ):
                raise Lot41ValidationError(
                    "zero depth requires undefined imbalance"
                )
            return
        expected = (self.bid_quantity - self.ask_quantity) / denominator
        if self.imbalance != expected or self.imbalance_status != IMBALANCE_DEFINED:
            raise Lot41ValidationError("depth/imbalance mismatch")
        if not Decimal("-1") <= expected <= Decimal("1"):
            raise Lot41ValidationError("imbalance escaped [-1,1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot41-depth-band-v1",
            "band_bps": decimal_text(self.band_bps),
            "bid_quantity": decimal_text(self.bid_quantity),
            "ask_quantity": decimal_text(self.ask_quantity),
            "bid_levels_observed": self.bid_levels_observed,
            "ask_levels_observed": self.ask_levels_observed,
            "imbalance": (
                None
                if self.imbalance is None
                else decimal_text(self.imbalance)
            ),
            "imbalance_status": self.imbalance_status,
            "coverage_status": COVERAGE_STATUS,
        }


@dataclass(frozen=True, slots=True)
class CumulativeDepthLevelV1:
    price: Decimal
    quantity: Decimal
    cumulative_quantity: Decimal
    distance_bps: Decimal

    def __post_init__(self) -> None:
        values = (
            self.price,
            self.quantity,
            self.cumulative_quantity,
            self.distance_bps,
        )
        if any(not value.is_finite() for value in values):
            raise Lot41ValidationError("cumulative depth values must be finite")
        if self.price <= 0 or self.quantity <= 0 or self.cumulative_quantity <= 0:
            raise Lot41ValidationError(
                "cumulative price/quantities must be positive"
            )
        if self.distance_bps < 0:
            raise Lot41ValidationError("distance_bps cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "price": decimal_text(self.price),
            "quantity": decimal_text(self.quantity),
            "cumulative_quantity": decimal_text(self.cumulative_quantity),
            "distance_bps": decimal_text(self.distance_bps),
        }


@dataclass(frozen=True, slots=True)
class BookQualityBindingV1:
    health_status: str
    book_health_score: Decimal
    consequence: str
    sequence_id: int
    integrity_checksum: str
    veto_checksum: str

    def __post_init__(self) -> None:
        if (
            self.health_status != "HEALTHY"
            or self.book_health_score != Decimal("100")
        ):
            raise Lot41ValidationError("Lot 41 requires certified healthy book")
        if self.consequence != "NONE":
            raise Lot41ValidationError(
                "Lot 41 refuses active book-health consequence"
            )
        require_integer(self.sequence_id, "sequence_id", minimum=1)
        require_sha256(self.integrity_checksum, "integrity_checksum")
        require_sha256(self.veto_checksum, "veto_checksum")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot41-book-quality-binding-v1",
            "health_status": self.health_status,
            "book_health_score": decimal_text(self.book_health_score),
            "consequence": self.consequence,
            "sequence_id": self.sequence_id,
            "integrity_checksum": self.integrity_checksum,
            "veto_checksum": self.veto_checksum,
        }


@dataclass(frozen=True, slots=True)
class BookFeatureStateV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    event_time: str
    receive_time: str
    decision_time: str
    sequence_id: int
    horizon: str
    spread_absolute: Decimal
    spread_bps: Decimal
    mid_price: Decimal
    microprice: Decimal
    top_of_book: TopOfBookV1
    depth_bands: tuple[DepthBandV1, ...]
    cumulative_bids: tuple[CumulativeDepthLevelV1, ...]
    cumulative_asks: tuple[CumulativeDepthLevelV1, ...]
    book_quality: BookQualityBindingV1
    reason_codes: tuple[str, ...]
    feature_checksum: str

    def __post_init__(self) -> None:
        for value, field in self._identity_fields():
            require_text(value, field)
        require_integer(self.sequence_id, "sequence_id", minimum=1)
        if self.market_type != "SPOT" or self.horizon != "BOOK_SNAPSHOT":
            raise Lot41ValidationError("Lot 41 market type or horizon changed")
        self._validate_features()
        validate_reason_codes(self.reason_codes)
        require_sha256(self.feature_checksum, "feature_checksum")

    def _identity_fields(self) -> tuple[tuple[str, str], ...]:
        return (
            (self.source_id, "source_id"),
            (self.venue, "venue"),
            (self.instrument_id, "instrument_id"),
            (self.event_time, "event_time"),
            (self.receive_time, "receive_time"),
            (self.decision_time, "decision_time"),
        )

    def _validate_features(self) -> None:
        values = (
            self.spread_absolute,
            self.spread_bps,
            self.mid_price,
            self.microprice,
        )
        if any(not value.is_finite() or value <= 0 for value in values):
            raise Lot41ValidationError(
                "spread/mid/microprice must be finite and positive"
            )
        if (
            not self.depth_bands
            or not self.cumulative_bids
            or not self.cumulative_asks
        ):
            raise Lot41ValidationError(
                "Lot 41 requires bilateral observed depth"
            )
        bands = tuple(item.band_bps for item in self.depth_bands)
        if any(left >= right for left, right in pairwise(bands)):
            raise Lot41ValidationError(
                "published depth bands are not increasing"
            )
        if self.book_quality.sequence_id != self.sequence_id:
            raise Lot41ValidationError(
                "book quality/feature sequence mismatch"
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("feature_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "book-feature-state-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "decision_time": self.decision_time,
            "sequence_id": self.sequence_id,
            "horizon": self.horizon,
            "spread_absolute": decimal_text(self.spread_absolute),
            "spread_bps": decimal_text(self.spread_bps),
            "mid_price": decimal_text(self.mid_price),
            "microprice": decimal_text(self.microprice),
            "top_of_book": self.top_of_book.to_dict(),
            "depth_bands": [item.to_dict() for item in self.depth_bands],
            "cumulative_depth": {
                "bids": [item.to_dict() for item in self.cumulative_bids],
                "asks": [item.to_dict() for item in self.cumulative_asks],
            },
            "book_quality": self.book_quality.to_dict(),
            "observed_depth_only": True,
            "extrapolated": False,
            "reason_codes": list(self.reason_codes),
            "feature_checksum": self.feature_checksum,
        }


@dataclass(frozen=True, slots=True)
class Lot41MetricsV1:
    depth_bands_total: int
    undefined_imbalance_total: int
    bid_levels_observed: int
    ask_levels_observed: int

    def __post_init__(self) -> None:
        fields = (
            (self.depth_bands_total, "depth_bands_total"),
            (self.undefined_imbalance_total, "undefined_imbalance_total"),
            (self.bid_levels_observed, "bid_levels_observed"),
            (self.ask_levels_observed, "ask_levels_observed"),
        )
        for value, field in fields:
            require_integer(value, field)
        if self.undefined_imbalance_total > self.depth_bands_total:
            raise Lot41ValidationError(
                "undefined imbalance count exceeds band count"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot41-metrics-v1",
            "lot_41_records_processed_total": 1,
            "lot_41_depth_bands_total": self.depth_bands_total,
            "lot_41_undefined_imbalance_total": self.undefined_imbalance_total,
            "lot_41_bid_levels_observed": self.bid_levels_observed,
            "lot_41_ask_levels_observed": self.ask_levels_observed,
            "lot_41_validation_failures_total": 0,
            "lot_41_processing_latency_us": None,
            "latency_measurement_status": (
                "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY"
            ),
        }


@dataclass(frozen=True, slots=True)
class SpreadDepthImbalanceEngineStateV1:
    run_context: Lot41RunContextV1
    lineage: Lot41LineageEnvelopeV1
    generated_at: str
    book_features: BookFeatureStateV1
    metrics: Lot41MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        require_text(self.generated_at, "generated_at")
        validate_reason_codes(self.reason_codes)
        validate_lot41_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "spread-depth-imbalance-engine-state-v1",
            "validation_state": VALIDATION_STATE,
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.book_features.event_time,
            "receive_time": self.book_features.receive_time,
            "decision_time": self.book_features.decision_time,
            "generated_at": self.generated_at,
            "book_features": self.book_features.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class SpreadDepthImbalanceEngineAuditV1:
    run_context: Lot41RunContextV1
    state_output_checksum: str
    feature_checksum: str
    lineage: Lot41LineageEnvelopeV1
    validation_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        checksums = (
            (self.state_output_checksum, "state_output_checksum"),
            (self.feature_checksum, "feature_checksum"),
            (self.audit_checksum, "audit_checksum"),
        )
        for value, field in checksums:
            require_sha256(value, field)
        if not self.validation_checks:
            raise Lot41ValidationError(
                "Lot 41 audit requires validation checks"
            )
        for value in self.validation_checks:
            require_text(value, "validation_check")
        validate_reason_codes(self.reason_codes)
        validate_lot41_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "spread-depth-imbalance-engine-audit-v1",
            "validation_state": VALIDATION_STATE,
            "run_context": self.run_context.to_dict(),
            "state_output_checksum": self.state_output_checksum,
            "feature_checksum": self.feature_checksum,
            "lineage": self.lineage.to_dict(),
            "validation_checks": list(self.validation_checks),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
