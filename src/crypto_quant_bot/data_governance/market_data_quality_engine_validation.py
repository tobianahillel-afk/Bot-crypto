from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


class MarketDataQualityError(ValueError):
    """Fail-closed validation error for Lot 34 market-data quality contracts."""


def require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise MarketDataQualityError(f"{field} must be an explicit trimmed string")
    return value


def require_identifier(value: object, field: str) -> str:
    text = require_text(value, field)
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:")
    if any(character not in allowed for character in text):
        raise MarketDataQualityError(f"{field} contains unsupported characters")
    return text


def require_integer(value: object, field: str, *, minimum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MarketDataQualityError(f"{field} must be an integer")
    if minimum is not None and value < minimum:
        raise MarketDataQualityError(f"{field} must be >= {minimum}")
    return value


def require_sha256(value: object, field: str) -> str:
    text = require_text(value, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise MarketDataQualityError(f"{field} must be a lowercase sha256")
    return text


def require_git_sha(value: object, field: str = "code_commit") -> str:
    text = require_text(value, field)
    if len(text) != 40 or any(character not in "0123456789abcdef" for character in text):
        raise MarketDataQualityError(f"{field} must be a lowercase 40-character git sha")
    return text


def parse_utc_timestamp(value: object, field: str) -> datetime:
    text = require_text(value, field)
    if not text.endswith("Z"):
        raise MarketDataQualityError(f"{field} must be UTC and end with Z")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise MarketDataQualityError(f"{field} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise MarketDataQualityError(f"{field} must be timezone-aware UTC")
    return parsed


def decimal_from_string(value: object, field: str) -> Decimal:
    text = require_text(value, field)
    try:
        decimal = Decimal(text)
    except InvalidOperation as exc:
        raise MarketDataQualityError(f"{field} must be a decimal string") from exc
    if not decimal.is_finite():
        raise MarketDataQualityError(f"{field} must be finite")
    return decimal


def require_string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MarketDataQualityError(f"{field} must be a list")
    return tuple(require_text(item, field) for item in value)


def lot34_safety() -> dict[str, object]:
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


def validate_lot34_safety(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or value != lot34_safety():
        raise MarketDataQualityError("Lot 34 safety boundary must remain exactly fail-closed")
    return dict(value)
