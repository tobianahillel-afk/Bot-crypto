from __future__ import annotations

import subprocess
from collections.abc import Mapping, Set
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from . import trades_and_aggressor_classification_schema_validation as lot44_validation

RUNTIME_MODE = "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
CONFIG_VERSION = "lot45-order-flow-delta-cvd-config-v1"
POLICY_VERSION = "lot45-order-flow-delta-cvd-policy-v1"
WINDOW_POLICY_VERSION = "lot45-event-time-tumbling-v1"
SESSION_POLICY_VERSION = "lot45-utc-day-session-v1"
VALIDATION_STATE = "VALIDATED_OFFLINE_ORDER_FLOW_DELTA_CVD_ONLY"
CALCULATION_DECIMAL_PRECISION = 50
WINDOW_SIZE_US = 1_000_000
CLASSIFICATIONS = frozenset({"BUY_AGGRESSOR", "SELL_AGGRESSOR", "UNKNOWN"})


class Lot45ValidationError(RuntimeError):
    """Raised when a Lot 45 contract or invariant is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot45ValidationError(message)


def require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Lot45ValidationError(f"{field} must be non-empty text")
    return value


def require_integer(value: object, field: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Lot45ValidationError(f"{field} must be integer")
    require(value >= minimum, f"{field} must be >= {minimum}")
    return value


def require_sha256(value: object, field: str) -> str:
    text = require_text(value, field)
    require(
        len(text) == 64 and all(ch in "0123456789abcdef" for ch in text),
        f"{field} must be lowercase sha256",
    )
    return text


def _git_commit_exists(root: Path, commit: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def executable_sources_absent_from_commit(
    root: Path,
    tracked_python: Set[str],
) -> tuple[str, ...]:
    """Return live Python files under ``src`` that are absent from the claimed tree."""

    src_root = root / "src"
    try:
        live_python = {
            path.relative_to(root).as_posix()
            for path in src_root.rglob("*.py")
            if path.is_file()
        }
    except OSError as exc:
        raise Lot45ValidationError("Lot45 executable source inventory unavailable") from exc
    return tuple(sorted(live_python - set(tracked_python)))


def reject_untracked_executable_sources(root: Path, code_commit: str) -> None:
    """Bind every live Python source under ``src`` to the claimed Git commit.

    Filesystem enumeration intentionally catches ignored and untracked Python files,
    including ``src/sitecustomize.py``. Comparing against ``git ls-tree`` rather than
    the current index also rejects sources added or staged after the claimed commit.
    """

    try:
        tracked = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", code_commit, "--", "src"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise Lot45ValidationError("Lot45 source tracking verification unavailable") from exc
    if tracked.returncode != 0:
        raise Lot45ValidationError("Lot45 source tracking verification unavailable")

    tracked_python = {
        line.strip().replace("\\", "/")
        for line in tracked.stdout.splitlines()
        if line.strip().endswith(".py")
    }
    unexpected = executable_sources_absent_from_commit(root, tracked_python)
    require(
        not unexpected,
        "Lot45 executable source absent from code_commit: " + ", ".join(unexpected),
    )


def require_git_sha(value: object, field: str) -> str:
    text = require_text(value, field)
    require(
        len(text) == 40 and all(ch in "0123456789abcdef" for ch in text),
        f"{field} must be git sha",
    )
    if field == "code_commit":
        root = Path(__file__).resolve().parents[3]
        if (root / ".git").exists() and _git_commit_exists(root, text):
            reject_untracked_executable_sources(root, text)
    return text


def decimal_from_text(
    value: object,
    field: str,
    *,
    allow_negative: bool = False,
) -> Decimal:
    if not isinstance(value, str):
        raise Lot45ValidationError(f"{field} must be decimal text")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise Lot45ValidationError(f"{field} invalid decimal") from exc
    require(number.is_finite(), f"{field} must be finite")
    if not allow_negative:
        require(number >= 0, f"{field} must be non-negative")
    return number


def decimal_text(value: Decimal) -> str:
    try:
        return lot44_validation.decimal_text(value)
    except RuntimeError as exc:
        raise Lot45ValidationError(str(exc)) from exc


def parse_utc_timestamp(value: object, field: str) -> datetime:
    text = require_text(value, field)
    require(text.endswith("Z"), f"{field} must use UTC Z suffix")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise Lot45ValidationError(f"{field} invalid UTC timestamp") from exc
    require(parsed.tzinfo == UTC, f"{field} must be UTC")
    require(text == timestamp_text(parsed), f"{field} must use canonical UTC timestamp text")
    return parsed


def timestamp_text(value: datetime) -> str:
    require(value.tzinfo == UTC, "timestamp must be UTC")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def validate_causal_times(event_time: str, receive_time: str, generated_at: str) -> None:
    try:
        lot44_validation.validate_causal_times(event_time, receive_time, generated_at)
    except RuntimeError as exc:
        raise Lot45ValidationError(str(exc)) from exc


def duration_us(earlier: str, later: str) -> int:
    left = parse_utc_timestamp(earlier, "earlier_time")
    right = parse_utc_timestamp(later, "later_time")
    require(left <= right, "duration cannot be negative")
    delta = right - left
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def epoch_us(value: datetime) -> int:
    require(value.tzinfo == UTC, "epoch conversion requires UTC")
    delta = value - datetime(1970, 1, 1, tzinfo=UTC)
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def from_epoch_us(value: int) -> datetime:
    require_integer(value, "epoch_us")
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=value)


def event_window_bounds(event_time: str, window_size_us: int) -> tuple[str, str]:
    require_integer(window_size_us, "window_size_us", 1)
    event = parse_utc_timestamp(event_time, "event_time")
    raw_us = epoch_us(event)
    start_us = (raw_us // window_size_us) * window_size_us
    end_us = start_us + window_size_us
    return timestamp_text(from_epoch_us(start_us)), timestamp_text(from_epoch_us(end_us))


def session_id_for_event(event_time: str, session_policy_version: str) -> str:
    require(
        session_policy_version == SESSION_POLICY_VERSION,
        "Lot45 session policy version changed",
    )
    event = parse_utc_timestamp(event_time, "event_time")
    return event.date().isoformat()


def validate_ratio(value: Decimal, field: str) -> None:
    require(value.is_finite(), f"{field} must be finite")
    require(Decimal("0") <= value <= Decimal("1"), f"{field} outside [0,1]")


def require_reason_codes(value: tuple[str, ...]) -> None:
    try:
        lot44_validation.require_reason_codes(value)
    except RuntimeError as exc:
        raise Lot45ValidationError(str(exc)) from exc


def validate_run_context(
    run_id: str,
    runtime_mode: str,
    config_version: str,
    code_commit: str,
    correlation_id: str,
) -> None:
    require_text(run_id, "run_id")
    require(runtime_mode == RUNTIME_MODE, "Lot45 runtime mode changed")
    require(config_version == CONFIG_VERSION, "Lot45 config version changed")
    require_git_sha(code_commit, "code_commit")
    require_text(correlation_id, "correlation_id")


def lot45_safety() -> dict[str, object]:
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


def validate_safety(value: Mapping[str, object]) -> None:
    expected = lot45_safety()
    require(set(value) == set(expected), "Lot45 safety fields changed")
    for field, expected_value in expected.items():
        actual_value = value[field]
        require(
            type(actual_value) is type(expected_value),
            f"Lot45 safety type changed: {field}",
        )
        require(actual_value == expected_value, f"Lot45 safety value changed: {field}")


def require_closed_mapping(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be object")
    require(set(value) == fields, f"{label} fields differ from contract")
    return dict(value)
