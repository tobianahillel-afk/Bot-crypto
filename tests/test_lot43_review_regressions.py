from decimal import Decimal

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    Lot43ValidationError,
    nonnegative_decimal_text,
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
