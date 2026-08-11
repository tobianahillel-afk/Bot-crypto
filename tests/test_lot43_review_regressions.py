from decimal import Decimal, localcontext

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
    analyze_book_resilience,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    DECIMAL_PRECISION,
    Lot43ValidationError,
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
    policy = _policy(adjacent_bps=Decimal("0.05"), mid_shift_bps=Decimal("0.05"))
    observations = (
        _observation(1, "2026-08-06T19:18:40.050000Z", "3"),
        _observation(2, "2026-08-06T19:18:40.070000Z", "2"),
    )

    result = analyze_book_resilience(
        observations,
        policy,
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
