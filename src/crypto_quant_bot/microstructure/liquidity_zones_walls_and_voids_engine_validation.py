from __future__ import annotations

from datetime import datetime, UTC
from decimal import Decimal, localcontext
from typing import Any

from .book_integrity_desynchronization_detector_validation import (
    BookIntegrityValidationError,
    decimal_from_text,
    decimal_text as decimal_text,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times as validate_causal_times,
    validate_reason_codes as validate_reason_codes,
    validate_run_context as validate_run_context,
)
from .spread_depth_and_imbalance_engine_validation import lot41_safety, Lot41ValidationError

RUNTIME_MODE = "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
VALIDATION_STATE = "VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY"
DISPLAYED_WALL = "DISPLAYED_WALL"
PERSISTENT_ZONE = "PERSISTENT_ZONE"
LIQUIDITY_VOID = "LIQUIDITY_VOID"
ACTIVE = "ACTIVE"
HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
NOT_APPLICABLE = "NOT_APPLICABLE"
PARTICIPANT_INTENT = "NOT_INFERRED"
SIDES = frozenset({"BID", "ASK"})
ZONE_CLASSIFICATIONS = frozenset({DISPLAYED_WALL, PERSISTENT_ZONE})
CONFIDENCE_STATUSES = frozenset({HIGH_CONFIDENCE, LOW_CONFIDENCE, NOT_APPLICABLE})
DECIMAL_PRECISION = 50


class Lot42ValidationError(Lot41ValidationError):
    """Raised when a Lot 42 contract, invariant or safety boundary is invalid."""


def lot42_safety() -> dict[str, object]:
    return dict(lot41_safety())


def validate_lot42_safety(value: dict[str, object]) -> None:
    if value != lot42_safety():
        raise Lot42ValidationError("Lot 42 safety boundary changed")


def nonnegative_decimal_text(value: Any, field: str) -> Decimal:
    try:
        return decimal_from_text(value, field, allow_zero=True)
    except BookIntegrityValidationError as exc:
        raise Lot42ValidationError(str(exc)) from exc


def positive_decimal_text(value: Any, field: str) -> Decimal:
    try:
        return decimal_from_text(value, field, allow_zero=False)
    except BookIntegrityValidationError as exc:
        raise Lot42ValidationError(str(exc)) from exc


def validate_ratio(value: Decimal, field: str) -> None:
    if not value.is_finite() or value < 0 or value > 1:
        raise Lot42ValidationError(f"{field} must be within [0, 1]")


def validate_nonnegative(value: Decimal, field: str) -> None:
    if not value.is_finite() or value < 0:
        raise Lot42ValidationError(f"{field} must be finite and non-negative")


def validate_positive(value: Decimal, field: str) -> None:
    if not value.is_finite() or value <= 0:
        raise Lot42ValidationError(f"{field} must be finite and positive")


def validate_side(side: str) -> None:
    if side not in SIDES:
        raise Lot42ValidationError("liquidity side must be BID or ASK")


def validate_classifications(values: tuple[str, ...]) -> None:
    if not values or len(set(values)) != len(values):
        raise Lot42ValidationError("zone classifications must be non-empty and unique")
    if any(value not in ZONE_CLASSIFICATIONS for value in values):
        raise Lot42ValidationError("unknown Lot 42 zone classification")


def validate_confidence(value: str) -> None:
    if value not in CONFIDENCE_STATUSES:
        raise Lot42ValidationError("unknown Lot 42 confidence status")


def parse_utc_timestamp(value: str, field: str) -> datetime:
    require_text(value, field)
    if not value.endswith("Z"):
        raise Lot42ValidationError(f"{field} must be UTC with Z suffix")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Lot42ValidationError(f"{field} must be valid ISO-8601 UTC") from exc
    if parsed.tzinfo != UTC:
        raise Lot42ValidationError(f"{field} must be UTC")
    return parsed


def age_us(available_at: str, decision_time: str) -> int:
    available = parse_utc_timestamp(available_at, "available_at")
    decision = parse_utc_timestamp(decision_time, "decision_time")
    if available > decision:
        raise Lot42ValidationError("available_at cannot exceed decision_time")
    delta = decision - available
    return ((delta.days * 86_400 + delta.seconds) * 1_000_000) + delta.microseconds


def bps_distance(left: Decimal, right: Decimal, reference: Decimal) -> Decimal:
    validate_positive(left, "left price")
    validate_positive(right, "right price")
    validate_positive(reference, "reference price")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        return abs(left - right) / reference * Decimal("10000")


def validate_identity_fields(values: tuple[tuple[str, str], ...]) -> None:
    for value, field in values:
        require_text(value, field)


def validate_sequence_ids(values: tuple[int, ...]) -> None:
    if not values:
        raise Lot42ValidationError("history sequence ids cannot be empty")
    for value in values:
        require_integer(value, "history sequence id", minimum=1)
    if tuple(sorted(values)) != values or len(set(values)) != len(values):
        raise Lot42ValidationError("history sequence ids must be strictly increasing")


def validate_checksum_fields(values: tuple[tuple[str, str], ...]) -> None:
    for value, field in values:
        require_sha256(value, field)
