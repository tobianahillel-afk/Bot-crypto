from __future__ import annotations

from datetime import datetime
from typing import Any

from .candle_trade_book_reconciliation_validation import (
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_sha256,
    require_text,
)

MICROSECONDS_PER_SECOND = 1_000_000


class V3ClosureError(RuntimeError):
    """Raised when Lot 36 cannot produce an auditable V3 closure candidate."""


def duration_us(start: datetime, end: datetime) -> int:
    if end < start:
        raise V3ClosureError("duration cannot run backwards")
    delta = end - start
    return (
        delta.days * 86_400_000_000
        + delta.seconds * MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


def lot36_safety() -> dict[str, object]:
    return {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }


def validate_lot36_safety(value: dict[str, object]) -> None:
    if value != lot36_safety():
        raise V3ClosureError("Lot 36 safety boundary changed")


def validate_reason_codes(reason_codes: tuple[str, ...], label: str) -> None:
    if not reason_codes:
        raise V3ClosureError(f"{label} requires reason codes")
    for reason in reason_codes:
        require_identifier(reason, "reason_code")


def validate_causal_times(event_time: str, available_at: str, generated_at: str) -> None:
    event = parse_utc_timestamp(event_time, "event_time")
    available = parse_utc_timestamp(available_at, "available_at")
    generated = parse_utc_timestamp(generated_at, "generated_at")
    if not event <= available <= generated:
        raise V3ClosureError("Lot 36 state violates causal availability")


def require_basis_points(value: object, field: str) -> int:
    number = require_integer(value, field, minimum=0)
    if number > 10_000:
        raise V3ClosureError(f"{field} must be between 0 and 10000")
    return number


def require_non_empty_string_tuple(values: tuple[str, ...], field: str) -> None:
    if not values:
        raise V3ClosureError(f"{field} cannot be empty")
    for value in values:
        require_identifier(value, field)


def validate_git_and_sha256(code_commit: str, checksums: dict[str, str]) -> None:
    require_git_sha(code_commit)
    for field, checksum in checksums.items():
        require_sha256(checksum, field)


def validate_runtime_mode(runtime_mode: str) -> None:
    if runtime_mode != "DATA_GOVERNANCE_ONLY":
        raise V3ClosureError("Lot 36 runtime must be DATA_GOVERNANCE_ONLY")


def validate_text_identity(value: Any, field: str, expected: str) -> str:
    text = require_text(value, field)
    if text != expected:
        raise V3ClosureError(f"{field} changed")
    return text
