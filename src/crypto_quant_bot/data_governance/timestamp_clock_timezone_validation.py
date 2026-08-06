from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .source_registry_validation import fail_closed_safety

PRECISION_DIGITS: Final[dict[str, int]] = {
    "SECONDS": 0,
    "MILLISECONDS": 3,
    "MICROSECONDS": 6,
}
TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.(\d+))?(?:Z|[+-]\d{2}:\d{2})$"
)
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TimestampGovernanceError(ValueError):
    """Fail-closed error for Lot 33 temporal governance."""


def require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TimestampGovernanceError(f"{field} must be explicit and trimmed")


def require_identifier(value: str, field: str) -> None:
    require_text(value, field)
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise TimestampGovernanceError(f"{field} must be canonical lowercase")


def require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise TimestampGovernanceError(f"{field} must be a lowercase sha256")


def require_git_sha(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise TimestampGovernanceError("code_commit must be a lowercase 40-character git sha")


def parse_aware_timestamp(value: str, field: str) -> datetime:
    require_text(value, field)
    if TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise TimestampGovernanceError(f"{field} must be an ISO-8601 timestamp with timezone")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TimestampGovernanceError(f"{field} cannot be timezone-naive")
    return parsed


def validate_precision(value: str, precision: str, field: str = "raw_timestamp") -> None:
    digits = PRECISION_DIGITS.get(precision)
    if digits is None:
        raise TimestampGovernanceError("timestamp_precision is unknown")
    match = TIMESTAMP_PATTERN.fullmatch(value)
    if match is None:
        raise TimestampGovernanceError(f"{field} must be timezone-aware ISO-8601")
    fraction = match.group(1) or ""
    if len(fraction) != digits:
        raise TimestampGovernanceError(f"{field} precision does not match declaration")


def validate_source_timezone(value: str, source_timezone: str) -> None:
    parsed = parse_aware_timestamp(value, "raw_timestamp")
    require_text(source_timezone, "source_timezone")
    try:
        expected_offset = parsed.astimezone(ZoneInfo(source_timezone)).utcoffset()
    except ZoneInfoNotFoundError as error:
        raise TimestampGovernanceError("source_timezone is unknown") from error
    if expected_offset != parsed.utcoffset():
        raise TimestampGovernanceError("raw timestamp offset differs from source_timezone")


def canonical_utc(value: str, precision: str, field: str) -> str:
    validate_precision(value, precision, field)
    parsed = parse_aware_timestamp(value, field).astimezone(timezone.utc)
    digits = PRECISION_DIGITS[precision]
    if digits == 0:
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
    fraction = f"{parsed.microsecond:06d}"[:digits]
    return parsed.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction}Z"


def duration_us(start: str, end: str, field: str) -> int:
    start_time = parse_aware_timestamp(start, f"{field}_start")
    end_time = parse_aware_timestamp(end, f"{field}_end")
    delta = end_time.astimezone(timezone.utc) - start_time.astimezone(timezone.utc)
    microseconds = delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    if microseconds < 0:
        raise TimestampGovernanceError(f"{field} cannot be negative")
    return microseconds


def signed_duration_us(start: str, end: str) -> int:
    start_time = parse_aware_timestamp(start, "signed_start")
    end_time = parse_aware_timestamp(end, "signed_end")
    delta = end_time.astimezone(timezone.utc) - start_time.astimezone(timezone.utc)
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def validate_fail_closed(values: dict[str, object]) -> None:
    if values != fail_closed_safety():
        raise TimestampGovernanceError("Lot 33 safety boundary must remain exactly fail-closed")
