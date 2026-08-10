from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

MICROSECONDS_PER_SECOND = 1_000_000
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE = re.compile(r"^[A-Z0-9_]+$")
ALLOWED_HEALTH_STATES = {"HEALTHY", "DEGRADED", "CRITICAL"}
ALLOWED_CONSEQUENCES = {"NONE", "WAIT", "PAUSE", "BLOCK"}
COMPONENT_NAMES = {
    "SEQUENCE_CONTINUITY",
    "CROSSED_LOCKED_STATE",
    "FRESHNESS",
    "CHECKSUM_INTEGRITY",
    "DEPTH_INTEGRITY",
    "LEVEL_MONOTONICITY",
}


class BookIntegrityValidationError(RuntimeError):
    """Raised when Lot 40 cannot prove an auditable offline book-health state."""


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BookIntegrityValidationError(f"{field} must be non-empty text")
    return value


def require_integer(value: Any, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BookIntegrityValidationError(f"{field} must be an integer >= {minimum}")
    return value


def require_boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise BookIntegrityValidationError(f"{field} must be boolean")
    return value


def require_git_sha(value: str, field: str) -> None:
    if _GIT_SHA.fullmatch(value) is None:
        raise BookIntegrityValidationError(f"{field} must be a lowercase git SHA")


def require_sha256(value: str, field: str) -> None:
    if _SHA256.fullmatch(value) is None:
        raise BookIntegrityValidationError(f"{field} must be a lowercase sha256")


def parse_utc_timestamp(value: str, field: str) -> datetime:
    require_text(value, field)
    if not value.endswith("Z"):
        raise BookIntegrityValidationError(f"{field} must use UTC Z notation")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise BookIntegrityValidationError(f"{field} is not an ISO timestamp") from exc


def duration_us(start: datetime, end: datetime) -> int:
    if end < start:
        raise BookIntegrityValidationError("duration cannot run backwards")
    delta = end - start
    return delta.days * 86_400_000_000 + delta.seconds * MICROSECONDS_PER_SECOND + delta.microseconds


def validate_causal_times(
    event_time: str,
    receive_time: str,
    decision_time: str,
    generated_at: str,
) -> None:
    event = parse_utc_timestamp(event_time, "event_time")
    received = parse_utc_timestamp(receive_time, "receive_time")
    decision = parse_utc_timestamp(decision_time, "decision_time")
    generated = parse_utc_timestamp(generated_at, "generated_at")
    if not event <= received <= decision <= generated:
        raise BookIntegrityValidationError(
            "Lot 40 violates causal event/receive/decision/generated ordering"
        )


def decimal_from_text(value: Any, field: str, *, allow_zero: bool = True) -> Decimal:
    if not isinstance(value, str):
        raise BookIntegrityValidationError(f"{field} must be decimal text")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise BookIntegrityValidationError(f"{field} invalid decimal") from exc
    if not number.is_finite():
        raise BookIntegrityValidationError(f"{field} must be finite")
    if number < 0 or (not allow_zero and number == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise BookIntegrityValidationError(f"{field} must be {qualifier}")
    return number


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise BookIntegrityValidationError("decimal output must be finite")
    return format(value.normalize(), "f")


def validate_reason_codes(reason_codes: tuple[str, ...]) -> None:
    if not reason_codes:
        raise BookIntegrityValidationError("Lot 40 requires reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise BookIntegrityValidationError("reason codes must be unique")
    for reason in reason_codes:
        if _REASON_CODE.fullmatch(reason) is None:
            raise BookIntegrityValidationError("invalid reason code")


def validate_runtime_mode(runtime_mode: str) -> None:
    if runtime_mode != "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY":
        raise BookIntegrityValidationError(
            "Lot 40 runtime must be OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
        )


def validate_health_state(value: str) -> None:
    if value not in ALLOWED_HEALTH_STATES:
        raise BookIntegrityValidationError("unknown book health state")


def validate_consequence(value: str) -> None:
    if value not in ALLOWED_CONSEQUENCES:
        raise BookIntegrityValidationError("unknown book-health consequence")


def derive_health_status(component_states: tuple[tuple[bool, bool], ...]) -> str:
    if any(critical and not passed for critical, passed in component_states):
        return "CRITICAL"
    return "DEGRADED" if any(not passed for _, passed in component_states) else "HEALTHY"


def derive_health_consequence(
    *,
    critical_veto_active: bool,
    score: Decimal,
    system_threshold: Decimal,
    trade_threshold: Decimal,
    critical_consequence: str,
    system_consequence: str,
) -> str:
    if not score.is_finite() or not system_threshold.is_finite() or not trade_threshold.is_finite():
        raise BookIntegrityValidationError("book-health policy inputs must be finite")
    if not Decimal("0") <= score <= Decimal("100"):
        raise BookIntegrityValidationError("book-health score must be within 0..100")
    if not Decimal("0") <= system_threshold <= trade_threshold <= Decimal("100"):
        raise BookIntegrityValidationError("book-health threshold ordering invalid")
    validate_consequence(critical_consequence)
    validate_consequence(system_consequence)
    if critical_veto_active:
        return critical_consequence
    if score < system_threshold:
        return system_consequence
    return "WAIT" if score < trade_threshold else "NONE"


def lot40_safety() -> dict[str, object]:
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


def validate_lot40_safety(value: dict[str, object]) -> None:
    if value != lot40_safety():
        raise BookIntegrityValidationError("Lot 40 safety boundary changed")


def validate_run_context(
    run_id: str,
    runtime_mode: str,
    config_version: str,
    code_commit: str,
    correlation_id: str,
) -> None:
    text_fields = ((run_id, "run_id"), (config_version, "config_version"), (correlation_id, "correlation_id"))
    for value, field in text_fields:
        require_text(value, field)
    validate_runtime_mode(runtime_mode)
    require_git_sha(code_commit, "code_commit")
