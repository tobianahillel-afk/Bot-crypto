from __future__ import annotations

from decimal import Decimal
from itertools import pairwise
from typing import Any

from .book_integrity_desynchronization_detector_validation import (
    BookIntegrityValidationError,
    decimal_from_text,
    lot40_safety,
    require_integer as _require_integer,
    require_text,
    validate_causal_times,
)

Lot41ValidationError = BookIntegrityValidationError
require_integer = _require_integer
RUNTIME_MODE = "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
VALIDATION_STATE = "VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY"
IMBALANCE_DEFINED = "DEFINED"
IMBALANCE_UNDEFINED = "UNDEFINED_ZERO_DENOMINATOR"
COVERAGE_STATUS = "OBSERVED_LEVELS_ONLY"


def lot41_safety() -> dict[str, object]:
    return dict(lot40_safety())


def validate_lot41_safety(value: dict[str, object]) -> None:
    if value != lot41_safety():
        raise Lot41ValidationError("Lot 41 safety boundary changed")


def positive_decimal_text(value: Any, field: str) -> Decimal:
    return decimal_from_text(value, field, allow_zero=False)


def parse_book_levels(
    raw: Any,
    side: str,
) -> tuple[tuple[Decimal, Decimal], ...]:
    if not isinstance(raw, list) or not raw:
        raise Lot41ValidationError(f"{side} book levels must be a non-empty list")
    parsed: list[tuple[Decimal, Decimal]] = []
    for index, level in enumerate(raw):
        if not isinstance(level, dict) or set(level) != {"price", "quantity"}:
            raise Lot41ValidationError(f"{side}[{index}] level fields changed")
        price = positive_decimal_text(level.get("price"), f"{side}[{index}].price")
        quantity = positive_decimal_text(
            level.get("quantity"),
            f"{side}[{index}].quantity",
        )
        parsed.append((price, quantity))
    validate_level_order(tuple(parsed), side)
    return tuple(parsed)


def validate_level_order(
    levels: tuple[tuple[Decimal, Decimal], ...],
    side: str,
) -> None:
    prices = tuple(price for price, _ in levels)
    if len(set(prices)) != len(prices):
        raise Lot41ValidationError(f"{side} prices must be unique")
    if side == "bids":
        ordered = all(left > right for left, right in pairwise(prices))
    elif side == "asks":
        ordered = all(left < right for left, right in pairwise(prices))
    else:
        raise Lot41ValidationError("unknown book side")
    if not ordered and len(prices) > 1:
        raise Lot41ValidationError(f"{side} levels are not strictly monotonic")


def parse_depth_bands(raw: Any) -> tuple[Decimal, ...]:
    if not isinstance(raw, list) or not raw:
        raise Lot41ValidationError("depth_bands_bps must be a non-empty list")
    bands = tuple(
        positive_decimal_text(value, "depth band bps")
        for value in raw
    )
    if len(set(bands)) != len(bands):
        raise Lot41ValidationError("depth bands must be unique")
    if any(left >= right for left, right in pairwise(bands)):
        raise Lot41ValidationError("depth bands must be strictly increasing")
    return bands


def validate_reference_identity(
    book: dict[str, Any],
    integrity: dict[str, Any],
) -> None:
    fields = ("source_id", "venue", "instrument_id", "market_type", "sequence_id")
    for field in fields:
        if book.get(field) != integrity.get(field):
            raise Lot41ValidationError(
                f"Lot 40/book identity mismatch: {field}"
            )
    if book.get("synchronization_state") != "SYNCED":
        raise Lot41ValidationError("Lot 41 requires SYNCED reconstructed book")
    if integrity.get("synchronization_state") != "SYNCED":
        raise Lot41ValidationError("Lot 41 requires SYNCED integrity state")


def validate_reference_times(
    book: dict[str, Any],
    integrity: dict[str, Any],
    decision_time: str,
    generated_at: str,
) -> None:
    event_time = require_text(book.get("event_time"), "book event_time")
    receive_time = require_text(book.get("receive_time"), "book receive_time")
    if (
        integrity.get("event_time") != event_time
        or integrity.get("receive_time") != receive_time
    ):
        raise Lot41ValidationError("Lot 40/book timestamps mismatch")
    if integrity.get("decision_time") != decision_time:
        raise Lot41ValidationError("Lot 40/config decision_time mismatch")
    validate_causal_times(
        event_time,
        receive_time,
        decision_time,
        generated_at,
    )


def symmetric_imbalance(
    bid_depth: Decimal,
    ask_depth: Decimal,
) -> tuple[Decimal | None, str]:
    if bid_depth < 0 or ask_depth < 0:
        raise Lot41ValidationError("depth cannot be negative")
    denominator = bid_depth + ask_depth
    if denominator == 0:
        return None, IMBALANCE_UNDEFINED
    value = (bid_depth - ask_depth) / denominator
    if not Decimal("-1") <= value <= Decimal("1"):
        raise Lot41ValidationError("imbalance escaped [-1,1]")
    return value, IMBALANCE_DEFINED


def validate_book_open(best_bid: Decimal, best_ask: Decimal) -> None:
    if best_bid >= best_ask:
        raise Lot41ValidationError("Lot 41 refuses crossed or locked book")
