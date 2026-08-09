from __future__ import annotations

import re
from datetime import datetime
from typing import Any

ALLOWED_CAPABILITY_CLASSIFICATIONS = {
    "REQUIRED",
    "OPTIONAL_RESEARCH",
    "DISABLED",
    "FORBIDDEN",
}
ALLOWED_CONTRACT_KINDS = {"INPUT", "OUTPUT"}
ALLOWED_CONTRACT_STATUSES = {"ACTIVE_LOT37_CONTRACT", "PLANNED_LOCKED"}
ALLOWED_API_KINDS = {"FUNCTION", "CONTRACT"}
ALLOWED_API_STATUSES = {"ACTIVE_LOT37_API"}
MICROSECONDS_PER_SECOND = 1_000_000
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CAPABILITY_ID = re.compile(r"^[A-Z0-9_]+$")


class MicrostructureScopeValidationError(RuntimeError):
    """Raised when Lot 37 cannot publish an unambiguous offline scope contract."""


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MicrostructureScopeValidationError(f"{field} must be non-empty text")
    return value


def require_integer(value: Any, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise MicrostructureScopeValidationError(
            f"{field} must be an integer >= {minimum}"
        )
    return value


def require_boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise MicrostructureScopeValidationError(f"{field} must be boolean")
    return value


def require_git_sha(value: str, field: str) -> None:
    if _GIT_SHA.fullmatch(value) is None:
        raise MicrostructureScopeValidationError(f"{field} must be a lowercase git SHA")


def require_sha256(value: str, field: str) -> None:
    if _SHA256.fullmatch(value) is None:
        raise MicrostructureScopeValidationError(f"{field} must be a lowercase sha256")


def require_capability_id(value: str) -> None:
    if _CAPABILITY_ID.fullmatch(value) is None:
        raise MicrostructureScopeValidationError("capability_id must use canonical uppercase form")


def parse_utc_timestamp(value: str, field: str) -> datetime:
    require_text(value, field)
    if not value.endswith("Z"):
        raise MicrostructureScopeValidationError(f"{field} must use UTC Z notation")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise MicrostructureScopeValidationError(f"{field} is not an ISO timestamp") from exc
    if parsed.utcoffset() is None:
        raise MicrostructureScopeValidationError(f"{field} must be timezone-aware")
    return parsed


def duration_us(start: datetime, end: datetime) -> int:
    if end < start:
        raise MicrostructureScopeValidationError("duration cannot run backwards")
    delta = end - start
    return (
        delta.days * 86_400_000_000
        + delta.seconds * MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


def validate_causal_times(event_time: str, available_at: str, generated_at: str) -> None:
    event = parse_utc_timestamp(event_time, "event_time")
    available = parse_utc_timestamp(available_at, "available_at")
    generated = parse_utc_timestamp(generated_at, "generated_at")
    if not event <= available <= generated:
        raise MicrostructureScopeValidationError("Lot 37 violates causal availability")


def lot37_safety() -> dict[str, object]:
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


def validate_lot37_safety(value: dict[str, object]) -> None:
    if value != lot37_safety():
        raise MicrostructureScopeValidationError("Lot 37 safety boundary changed")


def validate_reason_codes(reason_codes: tuple[str, ...]) -> None:
    if not reason_codes:
        raise MicrostructureScopeValidationError("Lot 37 requires reason codes")
    for reason in reason_codes:
        require_capability_id(reason)


def validate_runtime_mode(runtime_mode: str) -> None:
    if runtime_mode != "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY":
        raise MicrostructureScopeValidationError(
            "Lot 37 runtime must be OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
        )


def validate_contract_schema_path(path: str) -> None:
    if not path.startswith("contracts/schemas/") or not path.endswith(".schema.json"):
        raise MicrostructureScopeValidationError(
            "contract schema must remain under contracts/schemas"
        )


def require_unique(values: tuple[str, ...], field: str) -> None:
    if len(set(values)) != len(values):
        raise MicrostructureScopeValidationError(f"{field} values must be unique")
