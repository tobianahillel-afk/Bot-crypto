from decimal import Decimal, localcontext

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
    analyze_book_resilience,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_models import (
    BookDepletionEventV1,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    DECIMAL_PRECISION,
    Lot43ValidationError,
    directional_mid_shift_bps,
    nonnegative_decimal_text,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis import (
    BookObservation,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)


def _policy(*, adjacent_bps: Decimal, mid_shift_bps: Decimal) -> BookResiliencePolicy:
    return BookResiliencePolicy(
        50,
        Decimal("0.1"),
        Decimal("0.25"),
        Decimal("0.25"),
        adjacent_bps,
        mid_shift_bps,
        (10_000, 25_000),
        Decimal("0.05"),
        Decimal("0.5"),
    )


def _observation(sequence: int, receive_time: str, bid_quantity: str) -> BookObservation:
    return BookObservation(
        "source",
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        "2026-08-06T19:18:40.000001Z",
        receive_time,
        (OrderBookLevelV1(Decimal("100"), Decimal(bid_quantity)),),
        (OrderBookLevelV1(Decimal("102"), Decimal("1")),),
    )


def _priced_observation(
    sequence: int,
    receive_time: str,
    bids: tuple[tuple[str, str], ...],
    asks: tuple[tuple[str, str], ...],
) -> BookObservation:
    return BookObservation(
        "source",
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        "2026-08-06T19:18:40.000001Z",
        receive_time,
        tuple(OrderBookLevelV1(Decimal(price), Decimal(quantity)) for price, quantity in bids),
        tuple(OrderBookLevelV1(Decimal(price), Decimal(quantity)) for price, quantity in asks),
    )


def _reference_policy() -> BookResiliencePolicy:
    return _policy(adjacent_bps=Decimal("0.05"), mid_shift_bps=Decimal("0.05"))


@pytest.mark.parametrize(
    "field",
    ("adjacent_replenishment_distance_bps", "mid_shift_min_bps"),
)
def test_config_parser_rejects_zero_replenishment_thresholds(field: str) -> None:
    with pytest.raises(Lot43ValidationError, match="positive"):
        nonnegative_decimal_text("0", field)


@pytest.mark.parametrize(
    ("adjacent_bps", "mid_shift_bps"),
    ((Decimal("0"), Decimal("0.05")), (Decimal("0.05"), Decimal("0"))),
)
def test_policy_rejects_zero_replenishment_thresholds(
    adjacent_bps: Decimal,
    mid_shift_bps: Decimal,
) -> None:
    with pytest.raises(Lot43ValidationError, match="positive"):
        _policy(adjacent_bps=adjacent_bps, mid_shift_bps=mid_shift_bps)


def test_nonterminating_depletion_ratio_uses_certified_precision() -> None:
    observations = (
        _observation(1, "2026-08-06T19:18:40.050000Z", "3"),
        _observation(2, "2026-08-06T19:18:40.070000Z", "2"),
    )
    result = analyze_book_resilience(
        observations,
        _reference_policy(),
        "2026-08-06T19:18:40.100000Z",
    )
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        expected_ratio = Decimal("1") / Decimal("3")
    assert len(result.depletion_events) == 1
    event = result.depletion_events[0]
    assert event.depleted_quantity == Decimal("1")
    assert event.depletion_ratio == expected_ratio
    assert event.max_window_status == "EXPIRED_NO_REPLENISHMENT"


def test_high_precision_quantity_subtraction_is_not_rounded_to_default_context() -> None:
    previous = Decimal("1.23456789012345678901234567890123456789")
    current = Decimal("0.12345678901234567890123456789012345678")
    observations = (
        _observation(1, "2026-08-06T19:18:40.050000Z", str(previous)),
        _observation(2, "2026-08-06T19:18:40.070000Z", str(current)),
    )
    result = analyze_book_resilience(
        observations,
        _reference_policy(),
        "2026-08-06T19:18:40.100000Z",
    )
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        expected_depleted = previous - current
        expected_ratio = expected_depleted / previous
    event = result.depletion_events[0]
    assert event.depleted_quantity == expected_depleted
    assert event.depletion_ratio == expected_ratio


def test_nonterminating_recovery_fraction_and_mean_keep_certified_precision() -> None:
    observations = (
        _observation(1, "2026-08-06T19:18:40.050000Z", "3"),
        _observation(2, "2026-08-06T19:18:40.060000Z", "0"),
        _observation(3, "2026-08-06T19:18:40.070000Z", "1"),
    )
    result = analyze_book_resilience(
        observations,
        _reference_policy(),
        "2026-08-06T19:18:40.100000Z",
    )
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        expected_fraction = Decimal("1") / Decimal("3")
    event = result.depletion_events[0]
    assert event.replenishment_kind == "SAME_PRICE"
    assert event.recovered_fraction == expected_fraction
    bid_slice = next(
        item
        for item in result.resilience_slices
        if item.side == "BID" and item.horizon_us == 10_000
    )
    assert bid_slice.mean_recovered_fraction == expected_fraction


def test_recovered_fraction_must_match_replenished_and_depleted_quantities() -> None:
    with pytest.raises(Lot43ValidationError, match="recovered fraction/quantity mismatch"):
        BookDepletionEventV1(
            "event",
            "BID",
            Decimal("100"),
            Decimal("8"),
            Decimal("0"),
            Decimal("8"),
            Decimal("1"),
            1,
            "2026-08-06T19:18:40.000001Z",
            "2026-08-06T19:18:40.050000Z",
            "SAME_PRICE",
            2,
            10_000,
            Decimal("1"),
            Decimal("1"),
            Decimal("0"),
            "REPLENISHED",
            "NOT_INFERRED",
            ("LOT43_TEST_RECOVERY_ARITHMETIC",),
            "0" * 64,
        )


def test_directional_mid_shift_subtraction_uses_certified_precision() -> None:
    baseline_mid = Decimal("100.12345678901234567890123456789012345678")
    future_mid = Decimal("99.01234567890123456789012345678901234567")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        expected = (baseline_mid - future_mid) / baseline_mid * Decimal("10000")
    assert directional_mid_shift_bps("BID", baseline_mid, future_mid) == expected


def test_mid_shift_caller_evaluates_book_midpoints_at_certified_precision() -> None:
    depleted_price = "100.00000000000000000000000000000000000001"
    resting_bid = "99.99999999999999999999999999999999999990"
    old_ask = "100.00000000000000000000000000000000000030"
    new_ask = "100.00000000000000000000000000000000000010"
    observations = (
        _priced_observation(
            1,
            "2026-08-06T19:18:40.050000Z",
            ((depleted_price, "1"), (resting_bid, "2")),
            ((old_ask, "2"),),
        ),
        _priced_observation(
            2,
            "2026-08-06T19:18:40.060000Z",
            ((resting_bid, "2"),),
            ((old_ask, "2"),),
        ),
        _priced_observation(
            3,
            "2026-08-06T19:18:40.070000Z",
            ((resting_bid, "2"),),
            ((new_ask, "2"), (old_ask, "2")),
        ),
    )
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        baseline_mid = observations[1].mid_price
        future_mid = observations[2].mid_price
        exact_shift = (baseline_mid - future_mid) / baseline_mid * Decimal("10000")
        threshold = exact_shift / Decimal("2")
    assert exact_shift > 0
    result = analyze_book_resilience(
        observations,
        _policy(adjacent_bps=Decimal("0.05"), mid_shift_bps=threshold),
        "2026-08-06T19:18:40.100000Z",
    )
    event = next(item for item in result.depletion_events if item.depleted_price == Decimal(depleted_price))
    assert event.replenishment_kind == "MID_SHIFT"
    assert event.directional_mid_shift_bps == exact_shift
