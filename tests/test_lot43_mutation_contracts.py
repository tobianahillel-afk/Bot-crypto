from __future__ import annotations

from decimal import Decimal

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    Lot43ValidationError,
    age_us,
    bounded_recovery_fraction,
    bps_distance,
    directional_mid_shift_bps,
    elapsed_us,
    validate_event_semantics,
    validate_horizons,
    validate_max_window_status,
    validate_ratio,
    validate_regime_thresholds,
    validate_replenishment_kind,
    validate_resilience_status,
    validate_slice_counts,
    validate_volatility_regime,
)


def _assert_error(expected: str, function: object, *args: object, **kwargs: object) -> None:
    assert callable(function)
    with pytest.raises(Lot43ValidationError) as exc_info:
        function(*args, **kwargs)
    assert str(exc_info.value) == expected


def _event_kwargs(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "replenishment_kind": "SAME_PRICE",
        "replenishment_sequence_id": 1004,
        "replenishment_time_us": 5000,
        "replenished_quantity": Decimal("1"),
        "recovered_fraction": Decimal("0.8"),
        "mid_shift_bps": Decimal("0"),
        "max_window_status": "REPLENISHED",
    }
    values.update(changes)
    return values


def test_numeric_helpers_preserve_exact_math_and_direction() -> None:
    assert bps_distance(Decimal("100"), Decimal("101"), Decimal("100")) == Decimal("100")
    assert bps_distance(Decimal("101"), Decimal("100"), Decimal("100")) == Decimal("100")
    assert bounded_recovery_fraction(Decimal("0.25"), Decimal("1")) == Decimal("0.25")
    assert bounded_recovery_fraction(Decimal("2"), Decimal("1")) == Decimal("1")
    assert directional_mid_shift_bps("BID", Decimal("100"), Decimal("99")) == Decimal("100")
    assert directional_mid_shift_bps("BID", Decimal("100"), Decimal("101")) == Decimal("0")
    assert directional_mid_shift_bps("ASK", Decimal("100"), Decimal("101")) == Decimal("100")
    assert directional_mid_shift_bps("ASK", Decimal("100"), Decimal("99")) == Decimal("0")


def test_elapsed_and_age_microseconds_are_exact() -> None:
    start = "2026-08-06T19:18:40.000001Z"
    later = "2026-08-06T19:18:41.000003Z"
    assert elapsed_us(start, later) == 1_000_002
    assert age_us(start, later) == 1_000_002
    _assert_error("elapsed-time end must be strictly after start", elapsed_us, start, start)
    _assert_error("available_at cannot exceed decision_time", age_us, later, start)


def test_ratio_horizon_and_regime_boundaries_fail_closed_exactly() -> None:
    _assert_error("ratio must be within [0, 1]", validate_ratio, Decimal("-0.01"), "ratio")
    _assert_error("ratio must be within [0, 1]", validate_ratio, Decimal("1.01"), "ratio")
    _assert_error("resilience horizons cannot be empty", validate_horizons, ())
    _assert_error(
        "resilience horizons must be unique and strictly increasing",
        validate_horizons,
        (10_000, 10_000),
    )
    _assert_error(
        "resilience horizons must be unique and strictly increasing",
        validate_horizons,
        (25_000, 10_000),
    )
    _assert_error(
        "quiet volatility threshold must be below stressed threshold",
        validate_regime_thresholds,
        Decimal("1"),
        Decimal("1"),
    )


@pytest.mark.parametrize(
    ("function", "value", "message"),
    (
        (validate_volatility_regime, "UNKNOWN", "unknown Lot 43 volatility regime"),
        (validate_replenishment_kind, "UNKNOWN", "unknown Lot 43 replenishment kind"),
        (validate_max_window_status, "UNKNOWN", "unknown Lot 43 maximum-window status"),
        (validate_resilience_status, "UNKNOWN", "unknown Lot 43 resilience status"),
    ),
)
def test_enum_contract_messages_are_exact(function: object, value: str, message: str) -> None:
    _assert_error(message, function, value)


def test_replenishment_sequence_and_time_presence_must_match() -> None:
    values = _event_kwargs(replenishment_time_us=None)
    _assert_error(
        "replenishment sequence/time presence must match",
        validate_event_semantics,
        **values,
    )
    values = _event_kwargs(replenishment_sequence_id=None)
    _assert_error(
        "replenishment sequence/time presence must match",
        validate_event_semantics,
        **values,
    )


@pytest.mark.parametrize("kind", ("SAME_PRICE", "ADJACENT_PRICE"))
def test_quantity_replenishment_semantics_are_exact(kind: str) -> None:
    validate_event_semantics(**_event_kwargs(replenishment_kind=kind))  # type: ignore[arg-type]
    _assert_error(
        "quantity replenishment evidence is incomplete",
        validate_event_semantics,
        **_event_kwargs(
            replenishment_kind=kind,
            replenishment_sequence_id=None,
            replenishment_time_us=None,
        ),
    )
    _assert_error(
        "quantity replenishment evidence is incomplete",
        validate_event_semantics,
        **_event_kwargs(replenishment_kind=kind, replenished_quantity=Decimal("0")),
    )
    _assert_error(
        "quantity replenishment evidence is incomplete",
        validate_event_semantics,
        **_event_kwargs(replenishment_kind=kind, recovered_fraction=Decimal("0")),
    )
    _assert_error(
        "quantity replenishment requires REPLENISHED status",
        validate_event_semantics,
        **_event_kwargs(replenishment_kind=kind, max_window_status="MID_SHIFTED"),
    )
    _assert_error(
        "quantity replenishment cannot carry mid-shift evidence",
        validate_event_semantics,
        **_event_kwargs(replenishment_kind=kind, mid_shift_bps=Decimal("0.1")),
    )


def test_mid_shift_semantics_are_exact() -> None:
    valid = _event_kwargs(
        replenishment_kind="MID_SHIFT",
        replenished_quantity=Decimal("0"),
        recovered_fraction=Decimal("0"),
        mid_shift_bps=Decimal("1"),
        max_window_status="MID_SHIFTED",
    )
    validate_event_semantics(**valid)  # type: ignore[arg-type]
    _assert_error(
        "mid-shift evidence is incomplete",
        validate_event_semantics,
        **dict(valid, replenishment_sequence_id=None, replenishment_time_us=None),
    )
    _assert_error(
        "mid-shift evidence is incomplete",
        validate_event_semantics,
        **dict(valid, mid_shift_bps=Decimal("0")),
    )
    _assert_error(
        "mid shift cannot fabricate quantity recovery",
        validate_event_semantics,
        **dict(valid, replenished_quantity=Decimal("0.1")),
    )
    _assert_error(
        "mid shift cannot fabricate quantity recovery",
        validate_event_semantics,
        **dict(valid, recovered_fraction=Decimal("0.1")),
    )
    _assert_error(
        "mid shift requires MID_SHIFTED status",
        validate_event_semantics,
        **dict(valid, max_window_status="REPLENISHED"),
    )


def test_none_replenishment_semantics_are_exact() -> None:
    valid = _event_kwargs(
        replenishment_kind="NONE",
        replenishment_sequence_id=None,
        replenishment_time_us=None,
        replenished_quantity=Decimal("0"),
        recovered_fraction=Decimal("0"),
        mid_shift_bps=Decimal("0"),
        max_window_status="EXPIRED_NO_REPLENISHMENT",
    )
    validate_event_semantics(**valid)  # type: ignore[arg-type]
    validate_event_semantics(**dict(valid, max_window_status="PENDING_WINDOW"))  # type: ignore[arg-type]
    _assert_error(
        "NONE replenishment must carry no recovery evidence",
        validate_event_semantics,
        **dict(valid, replenished_quantity=Decimal("0.1")),
    )
    _assert_error(
        "NONE replenishment must carry no recovery evidence",
        validate_event_semantics,
        **dict(valid, recovered_fraction=Decimal("0.1")),
    )
    _assert_error(
        "NONE replenishment must carry no recovery evidence",
        validate_event_semantics,
        **dict(valid, mid_shift_bps=Decimal("0.1")),
    )
    _assert_error(
        "NONE replenishment has invalid window status",
        validate_event_semantics,
        **dict(valid, max_window_status="REPLENISHED"),
    )


def test_slice_count_partition_is_exact() -> None:
    validate_slice_counts(4, 1, 1, 1, 1)
    _assert_error(
        "resilience slice outcome counts must partition events",
        validate_slice_counts,
        4,
        1,
        1,
        1,
        0,
    )
