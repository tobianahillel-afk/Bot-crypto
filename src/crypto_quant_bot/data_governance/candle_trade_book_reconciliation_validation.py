from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from . import market_data_quality_engine_validation as _base_validation

MICROSECONDS_PER_SECOND = 1_000_000


class ReconciliationError(_base_validation.MarketDataQualityError):
    """Fail-closed validation error for Lot 35 reconciliation contracts."""


def _translate_validation_error(
    exc: _base_validation.MarketDataQualityError,
) -> ReconciliationError:
    return ReconciliationError(str(exc))


def require_text(value: object, field: str) -> str:
    try:
        return _base_validation.require_text(value, field)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def require_identifier(value: object, field: str) -> str:
    try:
        return _base_validation.require_identifier(value, field)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def require_integer(value: object, field: str, *, minimum: int | None = None) -> int:
    try:
        return _base_validation.require_integer(value, field, minimum=minimum)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def require_sha256(value: object, field: str) -> str:
    try:
        return _base_validation.require_sha256(value, field)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def require_git_sha(value: object, field: str = "code_commit") -> str:
    try:
        return _base_validation.require_git_sha(value, field)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def parse_utc_timestamp(value: object, field: str) -> datetime:
    try:
        return _base_validation.parse_utc_timestamp(value, field)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def decimal_from_string(value: object, field: str) -> Decimal:
    try:
        return _base_validation.decimal_from_string(value, field)
    except _base_validation.MarketDataQualityError as exc:
        raise _translate_validation_error(exc) from exc


def duration_us(left: datetime, right: datetime) -> int:
    delta = right - left
    value = (
        delta.days * 86_400_000_000
        + delta.seconds * MICROSECONDS_PER_SECOND
        + delta.microseconds
    )
    return abs(value)


def absolute_decimal_delta(left: object, right: object, field: str) -> Decimal:
    return abs(decimal_from_string(left, field) - decimal_from_string(right, field))


def canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise ReconciliationError("reconciliation delta must be finite")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def non_negative_decimal_string(value: object, field: str) -> str:
    decimal = decimal_from_string(value, field)
    if decimal < Decimal("0"):
        raise ReconciliationError(f"{field} must be non-negative")
    return require_text(value, field)


def lot35_safety() -> dict[str, object]:
    return {
        "analysis_only": True,
        "used_for_decision": False,
        "external_connectivity_allowed": False,
        "network_ingestion_allowed": False,
        "real_credentials_allowed": False,
        "market_event_publication_allowed": False,
        "raw_data_mutation_allowed": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def validate_lot35_safety(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or value != lot35_safety():
        raise ReconciliationError("Lot 35 safety boundary must remain exactly fail-closed")
    return dict(value)


__all__ = [
    "MICROSECONDS_PER_SECOND",
    "ReconciliationError",
    "absolute_decimal_delta",
    "canonical_decimal",
    "decimal_from_string",
    "duration_us",
    "lot35_safety",
    "non_negative_decimal_string",
    "parse_utc_timestamp",
    "require_git_sha",
    "require_identifier",
    "require_integer",
    "require_sha256",
    "require_text",
    "validate_lot35_safety",
]
