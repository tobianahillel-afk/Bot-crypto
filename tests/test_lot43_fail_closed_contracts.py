from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_models import (
    BookDepletionEventV1,
    BookResilienceSliceV1,
    Lot43MetricsV1,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    Lot43ValidationError,
    age_us,
    bounded_recovery_fraction,
    bps_distance,
    directional_mid_shift_bps,
    elapsed_us,
    lot43_safety,
    nonnegative_decimal_text,
    validate_event_semantics,
    validate_horizons,
    validate_lot43_safety,
    validate_regime_thresholds,
    validate_slice_counts,
)

ZERO_SHA256 = "0" * 64


def _event(**changes: object) -> BookDepletionEventV1:
    values: dict[str, object] = {
        "event_id": "event-1",
        "side": "BID",
        "depleted_price": Decimal("100"),
        "previous_quantity": Decimal("10"),
        "post_depletion_quantity": Decimal("2"),
        "depleted_quantity": Decimal("8"),
        "depletion_ratio": Decimal("0.8"),
        "depletion_sequence_id": 2,
        "depletion_event_time": "2026-08-06T19:18:40.000019Z",
        "depletion_receive_time": "2026-08-06T19:18:40.000020Z",
        "replenishment_kind": "NONE",
        "replenishment_sequence_id": None,
        "replenishment_time_us": None,
        "replenished_quantity": Decimal("0"),
        "recovered_fraction": Decimal("0"),
        "directional_mid_shift_bps": Decimal("0"),
        "max_window_status": "EXPIRED_NO_REPLENISHMENT",
        "participant_intent": "NOT_INFERRED",
        "reason_codes": ("LOT43_TEST",),
        "event_checksum": ZERO_SHA256,
    }
    values.update(changes)
    return BookDepletionEventV1(**values)  # type: ignore[arg-type]


def test_elapsed_and_age_use_strict_certified_times() -> None:
    assert elapsed_us(
        "2026-08-06T19:18:40.000020Z",
        "2026-08-06T19:18:40.000030Z",
    ) == 10
    assert age_us(
        "2026-08-06T19:18:40.000020Z",
        "2026-08-06T19:18:40.000030Z",
    ) == 10
    with pytest.raises(Lot43ValidationError, match="strictly after"):
        elapsed_us(
            "2026-08-06T19:18:40.000020Z",
            "2026-08-06T19:18:40.000020Z",
        )
    with pytest.raises(Lot43ValidationError, match="cannot exceed"):
        age_us(
            "2026-08-06T19:18:40.000030Z",
            "2026-08-06T19:18:40.000020Z",
        )


def test_horizons_must_be_unique_sorted_and_positive() -> None:
    validate_horizons((10, 20))
    for invalid in ((), (20, 10), (10, 10), (0, 10)):
        with pytest.raises(Lot43ValidationError):
            validate_horizons(invalid)


def test_volatility_thresholds_must_be_ordered() -> None:
    validate_regime_thresholds(Decimal("0.05"), Decimal("0.5"))
    with pytest.raises(Lot43ValidationError, match="below"):
        validate_regime_thresholds(Decimal("0.5"), Decimal("0.5"))
    with pytest.raises(Exception):
        validate_regime_thresholds(Decimal("-1"), Decimal("0.5"))


def test_decimal_text_parser_rejects_numeric_coercion() -> None:
    assert nonnegative_decimal_text("0.25", "ratio") == Decimal("0.25")
    with pytest.raises(Lot43ValidationError):
        nonnegative_decimal_text(0.25, "ratio")
    with pytest.raises(Lot43ValidationError):
        nonnegative_decimal_text("NaN", "ratio")


def test_recovery_fraction_is_bounded_and_not_probability() -> None:
    assert bounded_recovery_fraction(Decimal("4"), Decimal("8")) == Decimal("0.5")
    assert bounded_recovery_fraction(Decimal("12"), Decimal("8")) == Decimal("1")
    with pytest.raises(Exception):
        bounded_recovery_fraction(Decimal("1"), Decimal("0"))


def test_bps_and_directional_mid_shift_are_side_specific() -> None:
    assert bps_distance(Decimal("100"), Decimal("101"), Decimal("100")) == Decimal("100")
    assert directional_mid_shift_bps("BID", Decimal("100"), Decimal("99")) == Decimal("100")
    assert directional_mid_shift_bps("BID", Decimal("100"), Decimal("101")) == Decimal("0")
    assert directional_mid_shift_bps("ASK", Decimal("100"), Decimal("101")) == Decimal("100")
    assert directional_mid_shift_bps("ASK", Decimal("100"), Decimal("99")) == Decimal("0")


def test_none_event_cannot_carry_recovery_evidence() -> None:
    with pytest.raises(Lot43ValidationError, match="NONE replenishment"):
        validate_event_semantics(
            replenishment_kind="NONE",
            replenishment_sequence_id=3,
            replenishment_time_us=10,
            replenished_quantity=Decimal("1"),
            recovered_fraction=Decimal("0.1"),
            mid_shift_bps=Decimal("0"),
            max_window_status="EXPIRED_NO_REPLENISHMENT",
        )


def test_quantity_replenishment_requires_sequence_time_and_replenished_status() -> None:
    with pytest.raises(Lot43ValidationError, match="presence must match"):
        validate_event_semantics(
            replenishment_kind="SAME_PRICE",
            replenishment_sequence_id=3,
            replenishment_time_us=None,
            replenished_quantity=Decimal("1"),
            recovered_fraction=Decimal("0.5"),
            mid_shift_bps=Decimal("0"),
            max_window_status="REPLENISHED",
        )
    with pytest.raises(Lot43ValidationError, match="REPLENISHED"):
        validate_event_semantics(
            replenishment_kind="ADJACENT_PRICE",
            replenishment_sequence_id=3,
            replenishment_time_us=10,
            replenished_quantity=Decimal("1"),
            recovered_fraction=Decimal("0.5"),
            mid_shift_bps=Decimal("0"),
            max_window_status="PENDING_WINDOW",
        )
    with pytest.raises(Lot43ValidationError, match="mid-shift"):
        validate_event_semantics(
            replenishment_kind="SAME_PRICE",
            replenishment_sequence_id=3,
            replenishment_time_us=10,
            replenished_quantity=Decimal("1"),
            recovered_fraction=Decimal("0.5"),
            mid_shift_bps=Decimal("1"),
            max_window_status="REPLENISHED",
        )


def test_mid_shift_cannot_fabricate_quantity_recovery() -> None:
    with pytest.raises(Lot43ValidationError, match="fabricate"):
        validate_event_semantics(
            replenishment_kind="MID_SHIFT",
            replenishment_sequence_id=3,
            replenishment_time_us=10,
            replenished_quantity=Decimal("1"),
            recovered_fraction=Decimal("0.5"),
            mid_shift_bps=Decimal("2"),
            max_window_status="MID_SHIFTED",
        )
    with pytest.raises(Lot43ValidationError, match="MID_SHIFTED"):
        validate_event_semantics(
            replenishment_kind="MID_SHIFT",
            replenishment_sequence_id=3,
            replenishment_time_us=10,
            replenished_quantity=Decimal("0"),
            recovered_fraction=Decimal("0"),
            mid_shift_bps=Decimal("2"),
            max_window_status="REPLENISHED",
        )


def test_depletion_event_rejects_arithmetic_and_intent_tamper() -> None:
    _event()
    with pytest.raises(Lot43ValidationError, match="quantity/count"):
        _event(depleted_quantity=Decimal("7"))
    with pytest.raises(Lot43ValidationError, match="ratio/count"):
        _event(depletion_ratio=Decimal("0.7"))
    with pytest.raises(Lot43ValidationError, match="NOT_INFERRED"):
        _event(participant_intent="KNOWN")


def test_slice_counts_must_partition_events() -> None:
    validate_slice_counts(2, 1, 0, 1, 0)
    with pytest.raises(Lot43ValidationError, match="partition"):
        validate_slice_counts(2, 1, 0, 0, 0)


def test_slice_rejects_invalid_mean_semantics() -> None:
    base = BookResilienceSliceV1(
        "BID",
        10,
        "QUIET",
        "OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS",
        1,
        0,
        0,
        1,
        0,
        Decimal("0"),
        None,
        "FRAGILE",
        ("LOT43_TEST",),
        ZERO_SHA256,
    )
    with pytest.raises(Lot43ValidationError, match="requires recovered"):
        replace(base, mean_replenishment_time_us=Decimal("10"))
    with pytest.raises(Lot43ValidationError, match="requires mean"):
        replace(
            base,
            recovered_events_total=1,
            expired_events_total=0,
            mean_replenishment_time_us=None,
        )


def test_metrics_must_partition_max_window_outcomes() -> None:
    Lot43MetricsV1(3, 1, 0, 0, 0, 1, 0)
    with pytest.raises(Lot43ValidationError, match="partition"):
        Lot43MetricsV1(3, 1, 0, 0, 0, 0, 0)


def test_safety_boundary_is_exact_and_fail_closed() -> None:
    safety = lot43_safety()
    validate_lot43_safety(safety)
    tampered = dict(safety)
    tampered["trade_allowed"] = True
    with pytest.raises(Lot43ValidationError, match="safety boundary"):
        validate_lot43_safety(tampered)


def test_policy_rejects_invalid_precision_ratios_and_horizons() -> None:
    with pytest.raises(Lot43ValidationError, match="precision"):
        BookResiliencePolicy(
            28,
            Decimal("0.1"),
            Decimal("0.25"),
            Decimal("0.25"),
            Decimal("0.05"),
            Decimal("0.05"),
            (10, 20),
            Decimal("0.05"),
            Decimal("0.5"),
        )
    with pytest.raises(Lot43ValidationError):
        BookResiliencePolicy(
            50,
            Decimal("0.1"),
            Decimal("1.1"),
            Decimal("0.25"),
            Decimal("0.05"),
            Decimal("0.05"),
            (20, 10),
            Decimal("0.05"),
            Decimal("0.5"),
        )
