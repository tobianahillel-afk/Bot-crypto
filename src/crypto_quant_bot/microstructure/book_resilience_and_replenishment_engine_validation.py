from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Any

from .book_integrity_desynchronization_detector_validation import BookIntegrityValidationError
from .liquidity_zones_walls_and_voids_engine_validation import (
    ACTIVE,
    PARTICIPANT_INTENT,
    Lot42ValidationError,
    decimal_from_text,
    decimal_text,
    lot42_safety,
    parse_utc_timestamp,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_checksum_fields,
    validate_identity_fields,
    validate_reason_codes,
    validate_run_context,
    validate_sequence_ids,
)
from .liquidity_zones_walls_and_voids_engine_validation import (
    bps_distance as _bps_distance,
)
from .liquidity_zones_walls_and_voids_engine_validation import (
    require_integer as _require_integer,
)
from .liquidity_zones_walls_and_voids_engine_validation import (
    validate_nonnegative as _validate_nonnegative,
)
from .liquidity_zones_walls_and_voids_engine_validation import (
    validate_positive as _validate_positive,
)
from .liquidity_zones_walls_and_voids_engine_validation import validate_side as _validate_side

RUNTIME_MODE = "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
VALIDATION_STATE = "VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY"
DECIMAL_PRECISION = 50
REGIME_METHOD = "OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS"
VOLATILITY_REGIMES = frozenset({"QUIET", "NORMAL", "STRESSED"})
REPLENISHMENT_KINDS = frozenset({"NONE", "SAME_PRICE", "ADJACENT_PRICE", "MID_SHIFT"})
MAX_WINDOW_STATUSES = frozenset(
    {"REPLENISHED", "MID_SHIFTED", "EXPIRED_NO_REPLENISHMENT", "PENDING_WINDOW"}
)
RESILIENCE_STATUSES = frozenset(
    {"NO_EVENTS", "RESILIENT", "FRAGILE", "SHIFTED", "PENDING", "PARTIAL"}
)


class Lot43ValidationError(Lot42ValidationError):
    """Raised when a Lot 43 contract, invariant, or safety boundary is invalid."""


def _translate(exc: Exception) -> Lot43ValidationError:
    return Lot43ValidationError(str(exc))


def lot43_safety() -> dict[str, object]:
    return dict(lot42_safety())


def validate_lot43_safety(value: dict[str, object]) -> None:
    if value != lot43_safety():
        raise Lot43ValidationError("Lot 43 safety boundary changed")


def require_integer(value: Any, field: str, minimum: int = 0) -> int:
    try:
        return _require_integer(value, field, minimum=minimum)
    except (Lot42ValidationError, BookIntegrityValidationError) as exc:
        raise _translate(exc) from exc


def validate_nonnegative(value: Decimal, field: str) -> None:
    try:
        _validate_nonnegative(value, field)
    except Lot42ValidationError as exc:
        raise _translate(exc) from exc


def validate_positive(value: Decimal, field: str) -> None:
    try:
        _validate_positive(value, field)
    except Lot42ValidationError as exc:
        raise _translate(exc) from exc


def validate_side(value: str) -> None:
    try:
        _validate_side(value)
    except Lot42ValidationError as exc:
        raise _translate(exc) from exc


def nonnegative_decimal_text(value: Any, field: str) -> Decimal:
    try:
        return decimal_from_text(value, field, allow_zero=True)
    except (Lot42ValidationError, BookIntegrityValidationError) as exc:
        raise _translate(exc) from exc


def positive_decimal_text(value: Any, field: str) -> Decimal:
    try:
        return decimal_from_text(value, field, allow_zero=False)
    except (Lot42ValidationError, BookIntegrityValidationError) as exc:
        raise _translate(exc) from exc


def validate_ratio(value: Decimal, field: str) -> None:
    if not value.is_finite() or value < 0 or value > 1:
        raise Lot43ValidationError(f"{field} must be within [0, 1]")


def validate_horizons(values: tuple[int, ...]) -> None:
    if not values:
        raise Lot43ValidationError("resilience horizons cannot be empty")
    for value in values:
        require_integer(value, "resilience horizon", minimum=1)
    if tuple(sorted(values)) != values or len(set(values)) != len(values):
        raise Lot43ValidationError("resilience horizons must be unique and strictly increasing")


def validate_regime_thresholds(quiet_max: Decimal, stressed_min: Decimal) -> None:
    validate_nonnegative(quiet_max, "quiet_max_mid_move_bps")
    validate_positive(stressed_min, "stressed_min_mid_move_bps")
    if quiet_max >= stressed_min:
        raise Lot43ValidationError("quiet volatility threshold must be below stressed threshold")


def validate_volatility_regime(value: str) -> None:
    if value not in VOLATILITY_REGIMES:
        raise Lot43ValidationError("unknown Lot 43 volatility regime")


def validate_replenishment_kind(value: str) -> None:
    if value not in REPLENISHMENT_KINDS:
        raise Lot43ValidationError("unknown Lot 43 replenishment kind")


def validate_max_window_status(value: str) -> None:
    if value not in MAX_WINDOW_STATUSES:
        raise Lot43ValidationError("unknown Lot 43 maximum-window status")


def validate_resilience_status(value: str) -> None:
    if value not in RESILIENCE_STATUSES:
        raise Lot43ValidationError("unknown Lot 43 resilience status")


def elapsed_us(start: str, end: str) -> int:
    try:
        start_time = parse_utc_timestamp(start, "start_time")
        end_time = parse_utc_timestamp(end, "end_time")
    except (Lot42ValidationError, BookIntegrityValidationError) as exc:
        raise _translate(exc) from exc
    if end_time <= start_time:
        raise Lot43ValidationError("elapsed-time end must be strictly after start")
    delta = end_time - start_time
    return ((delta.days * 86_400 + delta.seconds) * 1_000_000) + delta.microseconds


def age_us(available_at: str, decision_time: str) -> int:
    try:
        available = parse_utc_timestamp(available_at, "available_at")
        decision = parse_utc_timestamp(decision_time, "decision_time")
    except (Lot42ValidationError, BookIntegrityValidationError) as exc:
        raise _translate(exc) from exc
    if available > decision:
        raise Lot43ValidationError("available_at cannot exceed decision_time")
    delta = decision - available
    return ((delta.days * 86_400 + delta.seconds) * 1_000_000) + delta.microseconds


def bps_distance(left: Decimal, right: Decimal, reference: Decimal) -> Decimal:
    try:
        return _bps_distance(left, right, reference)
    except Lot42ValidationError as exc:
        raise _translate(exc) from exc


def bounded_recovery_fraction(replenished: Decimal, depleted: Decimal) -> Decimal:
    validate_nonnegative(replenished, "replenished quantity")
    validate_positive(depleted, "depleted quantity")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        return min(replenished, depleted) / depleted


def directional_mid_shift_bps(
    side: str,
    baseline_mid: Decimal,
    future_mid: Decimal,
) -> Decimal:
    validate_side(side)
    validate_positive(baseline_mid, "baseline_mid")
    validate_positive(future_mid, "future_mid")
    if side == "BID":
        move = max(baseline_mid - future_mid, Decimal("0"))
    else:
        move = max(future_mid - baseline_mid, Decimal("0"))
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        return move / baseline_mid * Decimal("10000")


def validate_nullable_positive_integer(value: int | None, field: str) -> None:
    if value is None:
        return
    require_integer(value, field, minimum=1)


def validate_nullable_nonnegative_decimal(value: Decimal | None, field: str) -> None:
    if value is None:
        return
    validate_nonnegative(value, field)


def validate_nullable_positive_decimal(value: Decimal | None, field: str) -> None:
    if value is None:
        return
    validate_positive(value, field)


def _validate_quantity_replenishment(
    *,
    has_sequence: bool,
    replenished_quantity: Decimal,
    recovered_fraction: Decimal,
    mid_shift_bps: Decimal,
    max_window_status: str,
) -> None:
    if not has_sequence or replenished_quantity <= 0 or recovered_fraction <= 0:
        raise Lot43ValidationError("quantity replenishment evidence is incomplete")
    if max_window_status != "REPLENISHED":
        raise Lot43ValidationError("quantity replenishment requires REPLENISHED status")
    if mid_shift_bps != 0:
        raise Lot43ValidationError("quantity replenishment cannot carry mid-shift evidence")


def _validate_mid_shift(
    *,
    has_sequence: bool,
    replenished_quantity: Decimal,
    recovered_fraction: Decimal,
    mid_shift_bps: Decimal,
    max_window_status: str,
) -> None:
    if not has_sequence or mid_shift_bps <= 0:
        raise Lot43ValidationError("mid-shift evidence is incomplete")
    if replenished_quantity != 0 or recovered_fraction != 0:
        raise Lot43ValidationError("mid shift cannot fabricate quantity recovery")
    if max_window_status != "MID_SHIFTED":
        raise Lot43ValidationError("mid shift requires MID_SHIFTED status")


def _validate_no_replenishment(
    *,
    has_sequence: bool,
    replenished_quantity: Decimal,
    recovered_fraction: Decimal,
    mid_shift_bps: Decimal,
    max_window_status: str,
) -> None:
    if has_sequence or replenished_quantity != 0 or recovered_fraction != 0 or mid_shift_bps != 0:
        raise Lot43ValidationError("NONE replenishment must carry no recovery evidence")
    if max_window_status not in {"EXPIRED_NO_REPLENISHMENT", "PENDING_WINDOW"}:
        raise Lot43ValidationError("NONE replenishment has invalid window status")


def validate_event_semantics(
    *,
    replenishment_kind: str,
    replenishment_sequence_id: int | None,
    replenishment_time_us: int | None,
    replenished_quantity: Decimal,
    recovered_fraction: Decimal,
    mid_shift_bps: Decimal,
    max_window_status: str,
) -> None:
    validate_replenishment_kind(replenishment_kind)
    validate_max_window_status(max_window_status)
    validate_nullable_positive_integer(replenishment_sequence_id, "replenishment_sequence_id")
    validate_nullable_positive_integer(replenishment_time_us, "replenishment_time_us")
    validate_nonnegative(replenished_quantity, "replenished_quantity")
    validate_ratio(recovered_fraction, "recovered_fraction")
    validate_nonnegative(mid_shift_bps, "mid_shift_bps")
    has_sequence = replenishment_sequence_id is not None
    if has_sequence != (replenishment_time_us is not None):
        raise Lot43ValidationError("replenishment sequence/time presence must match")
    if replenishment_kind in {"SAME_PRICE", "ADJACENT_PRICE"}:
        _validate_quantity_replenishment(
            has_sequence=has_sequence,
            replenished_quantity=replenished_quantity,
            recovered_fraction=recovered_fraction,
            mid_shift_bps=mid_shift_bps,
            max_window_status=max_window_status,
        )
    elif replenishment_kind == "MID_SHIFT":
        _validate_mid_shift(
            has_sequence=has_sequence,
            replenished_quantity=replenished_quantity,
            recovered_fraction=recovered_fraction,
            mid_shift_bps=mid_shift_bps,
            max_window_status=max_window_status,
        )
    else:
        _validate_no_replenishment(
            has_sequence=has_sequence,
            replenished_quantity=replenished_quantity,
            recovered_fraction=recovered_fraction,
            mid_shift_bps=mid_shift_bps,
            max_window_status=max_window_status,
        )


def validate_slice_counts(
    events: int,
    recovered: int,
    shifted: int,
    expired: int,
    pending: int,
) -> None:
    values = (
        (events, "depletion_events_total"),
        (recovered, "recovered_events_total"),
        (shifted, "mid_shift_events_total"),
        (expired, "expired_events_total"),
        (pending, "pending_events_total"),
    )
    for value, field in values:
        require_integer(value, field, minimum=0)
    if recovered + shifted + expired + pending != events:
        raise Lot43ValidationError("resilience slice outcome counts must partition events")


__all__ = [
    "ACTIVE",
    "DECIMAL_PRECISION",
    "PARTICIPANT_INTENT",
    "REGIME_METHOD",
    "RUNTIME_MODE",
    "VALIDATION_STATE",
    "Lot43ValidationError",
    "age_us",
    "bounded_recovery_fraction",
    "bps_distance",
    "decimal_text",
    "directional_mid_shift_bps",
    "elapsed_us",
    "lot43_safety",
    "nonnegative_decimal_text",
    "positive_decimal_text",
    "require_integer",
    "require_sha256",
    "require_text",
    "validate_causal_times",
    "validate_checksum_fields",
    "validate_event_semantics",
    "validate_horizons",
    "validate_identity_fields",
    "validate_lot43_safety",
    "validate_max_window_status",
    "validate_nonnegative",
    "validate_positive",
    "validate_ratio",
    "validate_reason_codes",
    "validate_replenishment_kind",
    "validate_resilience_status",
    "validate_run_context",
    "validate_sequence_ids",
    "validate_side",
    "validate_slice_counts",
    "validate_volatility_regime",
]
