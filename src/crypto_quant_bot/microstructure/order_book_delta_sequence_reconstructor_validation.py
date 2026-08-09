from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

MICROSECONDS_PER_SECOND = 1_000_000
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE = re.compile(r"^[A-Z0-9_]+$")
ALLOWED_SYNC_STATES = {"SYNCED", "RESYNC_REQUIRED"}


class OrderBookDeltaSequenceValidationError(RuntimeError):
    """Raised when Lot 39 cannot prove a valid offline reconstructed book."""


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OrderBookDeltaSequenceValidationError(f"{field} must be non-empty text")
    return value


def require_integer(value: Any, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise OrderBookDeltaSequenceValidationError(
            f"{field} must be an integer >= {minimum}"
        )
    return value


def require_git_sha(value: str, field: str) -> None:
    if _GIT_SHA.fullmatch(value) is None:
        raise OrderBookDeltaSequenceValidationError(
            f"{field} must be a lowercase git SHA"
        )


def require_sha256(value: str, field: str) -> None:
    if _SHA256.fullmatch(value) is None:
        raise OrderBookDeltaSequenceValidationError(
            f"{field} must be a lowercase sha256"
        )


def parse_utc_timestamp(value: str, field: str) -> datetime:
    require_text(value, field)
    if not value.endswith("Z"):
        raise OrderBookDeltaSequenceValidationError(f"{field} must use UTC Z notation")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise OrderBookDeltaSequenceValidationError(
            f"{field} is not an ISO timestamp"
        ) from exc


def duration_us(start: datetime, end: datetime) -> int:
    if end < start:
        raise OrderBookDeltaSequenceValidationError("duration cannot run backwards")
    delta = end - start
    return (
        delta.days * 86_400_000_000
        + delta.seconds * MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


def validate_causal_times(event_time: str, receive_time: str, generated_at: str) -> None:
    event = parse_utc_timestamp(event_time, "event_time")
    received = parse_utc_timestamp(receive_time, "receive_time")
    generated = parse_utc_timestamp(generated_at, "generated_at")
    if not event <= received <= generated:
        raise OrderBookDeltaSequenceValidationError(
            "Lot 39 violates causal event/receive/generated ordering"
        )


def decimal_from_text(value: Any, field: str, *, allow_zero: bool) -> Decimal:
    if not isinstance(value, str):
        raise OrderBookDeltaSequenceValidationError(f"{field} must be decimal text")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise OrderBookDeltaSequenceValidationError(f"{field} invalid decimal") from exc
    if not number.is_finite():
        raise OrderBookDeltaSequenceValidationError(f"{field} must be finite")
    if number < 0 or (not allow_zero and number == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise OrderBookDeltaSequenceValidationError(f"{field} must be {qualifier}")
    return number


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise OrderBookDeltaSequenceValidationError("decimal output must be finite")
    return format(value.normalize(), "f")


def validate_reason_codes(reason_codes: tuple[str, ...]) -> None:
    if not reason_codes:
        raise OrderBookDeltaSequenceValidationError("Lot 39 requires reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise OrderBookDeltaSequenceValidationError("reason codes must be unique")
    for reason in reason_codes:
        if _REASON_CODE.fullmatch(reason) is None:
            raise OrderBookDeltaSequenceValidationError("invalid reason code")


def validate_runtime_mode(runtime_mode: str) -> None:
    if runtime_mode != "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY":
        raise OrderBookDeltaSequenceValidationError(
            "Lot 39 runtime must be OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
        )


def validate_sync_state(state: str) -> None:
    if state not in ALLOWED_SYNC_STATES:
        raise OrderBookDeltaSequenceValidationError("unknown synchronization_state")


def lot39_safety() -> dict[str, object]:
    return {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "participant_behavior_inference_explicitly_labeled": True,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "scenario_score_is_signal": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }


def validate_lot39_safety(value: dict[str, object]) -> None:
    if value != lot39_safety():
        raise OrderBookDeltaSequenceValidationError("Lot 39 safety boundary changed")


def validate_run_context(
    run_id: str,
    runtime_mode: str,
    config_version: str,
    code_commit: str,
    correlation_id: str,
) -> None:
    require_text(run_id, "run_id")
    validate_runtime_mode(runtime_mode)
    require_text(config_version, "config_version")
    require_git_sha(code_commit, "code_commit")
    require_text(correlation_id, "correlation_id")
