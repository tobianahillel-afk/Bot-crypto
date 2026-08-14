from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import OrderFlowPolicy
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    CALCULATION_DECIMAL_PRECISION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    decimal_from_text,
    decimal_text,
    duration_us,
    epoch_us,
    parse_utc_timestamp,
    require_integer,
    require_reason_codes,
    require_text,
    timestamp_text,
    validate_causal_times,
)


def _policy(precision: int) -> OrderFlowPolicy:
    return OrderFlowPolicy(
        precision,
        1_000_000,
        2_000_000,
        Decimal("0.5"),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def test_calculation_decimal_precision_is_exactly_frozen() -> None:
    assert _policy(CALCULATION_DECIMAL_PRECISION).decimal_precision == 50
    with pytest.raises(Lot45ValidationError, match="precision"):
        _policy(49)
    with pytest.raises(Lot45ValidationError, match="precision"):
        _policy(51)


def test_validation_primitives_fail_closed_on_invalid_types_and_decimals() -> None:
    with pytest.raises(Lot45ValidationError, match="non-empty text"):
        require_text("", "field")
    with pytest.raises(Lot45ValidationError, match="must be integer"):
        require_integer(True, "count")
    with pytest.raises(Lot45ValidationError, match="decimal text"):
        decimal_from_text(1, "value")
    with pytest.raises(Lot45ValidationError, match="invalid decimal"):
        decimal_from_text("garbage", "value")
    with pytest.raises(Lot45ValidationError, match="must be finite"):
        decimal_from_text("NaN", "value")
    with pytest.raises(Lot45ValidationError, match="non-negative"):
        decimal_from_text("-1", "value")
    assert decimal_from_text("-1", "value", allow_negative=True) == Decimal("-1")


def test_decimal_and_timestamp_wrappers_translate_failures() -> None:
    with pytest.raises(Lot45ValidationError):
        decimal_text(Decimal("NaN"))
    with pytest.raises(Lot45ValidationError, match="UTC Z suffix"):
        parse_utc_timestamp("2026-08-14T00:00:00+00:00", "timestamp")
    with pytest.raises(Lot45ValidationError, match="invalid UTC timestamp"):
        parse_utc_timestamp("not-a-timeZ", "timestamp")
    with pytest.raises(Lot45ValidationError, match="timestamp must be UTC"):
        timestamp_text(datetime(2026, 8, 14))
    with pytest.raises(Lot45ValidationError, match="epoch conversion requires UTC"):
        epoch_us(datetime(2026, 8, 14))
    with pytest.raises(Lot45ValidationError, match="duration cannot be negative"):
        duration_us("2026-08-14T00:00:01Z", "2026-08-14T00:00:00Z")


def test_causal_and_reason_code_errors_are_fail_closed() -> None:
    with pytest.raises(Lot45ValidationError):
        validate_causal_times(
            "2026-08-14T00:00:02Z",
            "2026-08-14T00:00:01Z",
            "2026-08-14T00:00:03Z",
        )
    with pytest.raises(Lot45ValidationError):
        require_reason_codes(())
    assert timestamp_text(datetime(2026, 8, 14, tzinfo=UTC)) == "2026-08-14T00:00:00.000000Z"
