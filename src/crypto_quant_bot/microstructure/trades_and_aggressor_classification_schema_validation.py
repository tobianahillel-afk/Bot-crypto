from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

RUNTIME_MODE = "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
CLASSIFICATIONS = frozenset({"BUY_AGGRESSOR", "SELL_AGGRESSOR", "UNKNOWN"})
METHODS = frozenset({"QUOTE_TEST", "TICK_RULE", "NONE"})
CONFIDENCE_SEMANTICS = "DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY"


class TradesAggressorClassificationValidationError(RuntimeError):
    """Raised when a Lot 44 contract or invariant is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TradesAggressorClassificationValidationError(message)


def require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TradesAggressorClassificationValidationError(
            f"{field} must be non-empty text"
        )
    return value


def require_integer(value: object, field: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TradesAggressorClassificationValidationError(
            f"{field} must be integer"
        )
    require(value >= minimum, f"{field} must be >= {minimum}")
    return value


def require_sha256(value: object, field: str) -> str:
    text = require_text(value, field)
    require(
        len(text) == 64 and all(ch in "0123456789abcdef" for ch in text),
        f"{field} must be lowercase sha256",
    )
    return text


def require_git_sha(value: object, field: str) -> str:
    text = require_text(value, field)
    require(
        len(text) == 40 and all(ch in "0123456789abcdef" for ch in text),
        f"{field} must be git sha",
    )
    return text


def decimal_from_text(
    value: object,
    field: str,
    *,
    allow_zero: bool = False,
) -> Decimal:
    if not isinstance(value, str):
        raise TradesAggressorClassificationValidationError(
            f"{field} must be decimal text"
        )
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise TradesAggressorClassificationValidationError(
            f"{field} invalid decimal"
        ) from exc
    require(number.is_finite(), f"{field} must be finite")
    require(
        number >= 0 if allow_zero else number > 0,
        f"{field} out of range",
    )
    return number


def decimal_text(value: Decimal) -> str:
    require(value.is_finite(), "decimal must be finite")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def parse_utc_timestamp(value: object, field: str) -> datetime:
    text = require_text(value, field)
    require(text.endswith("Z"), f"{field} must use UTC Z suffix")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise TradesAggressorClassificationValidationError(
            f"{field} invalid UTC timestamp"
        ) from exc
    require(parsed.tzinfo == UTC, f"{field} must be UTC")
    return parsed


def validate_causal_times(
    event_time: str,
    receive_time: str,
    generated_at: str,
) -> None:
    event = parse_utc_timestamp(event_time, "event_time")
    receive = parse_utc_timestamp(receive_time, "receive_time")
    generated = parse_utc_timestamp(generated_at, "generated_at")
    require(
        event <= receive <= generated,
        "causal timestamps require event <= receive <= generated",
    )


def duration_us(earlier: str, later: str) -> int:
    left = parse_utc_timestamp(earlier, "earlier_time")
    right = parse_utc_timestamp(later, "later_time")
    require(left <= right, "duration cannot be negative")
    return int((right - left).total_seconds() * 1_000_000)


def require_reason_codes(value: tuple[str, ...]) -> None:
    require(bool(value), "reason_codes cannot be empty")
    require(len(value) == len(set(value)), "reason_codes must be unique")
    for item in value:
        require_text(item, "reason_code")


def validate_run_context(
    run_id: str,
    runtime_mode: str,
    config_version: str,
    code_commit: str,
    correlation_id: str,
) -> None:
    require_text(run_id, "run_id")
    require(runtime_mode == RUNTIME_MODE, "Lot 44 runtime mode changed")
    require_text(config_version, "config_version")
    require_git_sha(code_commit, "code_commit")
    require_text(correlation_id, "correlation_id")


def lot44_safety() -> dict[str, object]:
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


def validate_safety(value: dict[str, object]) -> None:
    require(value == lot44_safety(), "Lot 44 safety boundary changed")


def require_closed_mapping(
    value: Any,
    fields: set[str],
    label: str,
) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be object")
    require(set(value) == fields, f"{label} fields differ from contract")
    return dict(value)
