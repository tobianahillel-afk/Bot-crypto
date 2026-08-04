from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from crypto_quant_bot.market_analysis.technical_indicators import (
    _bollinger,
    _clamp,
    _rate_of_change,
    _rsi,
)

FINITE_FLOATS = st.floats(
    min_value=-1e12,
    max_value=1e12,
    allow_nan=False,
    allow_infinity=False,
    width=64,
)
POSITIVE_PRICES = st.lists(
    st.floats(
        min_value=1e-6,
        max_value=1e9,
        allow_nan=False,
        allow_infinity=False,
        width=64,
    ),
    min_size=7,
    max_size=50,
)


@given(FINITE_FLOATS)
def test_clamp_is_finite_and_bounded(value: float) -> None:
    result = _clamp(value)
    assert math.isfinite(result)
    assert 0.0 <= result <= 1.0


def test_clamp_exact_identity_and_saturation() -> None:
    assert _clamp(-2.0) == 0.0
    assert _clamp(2.0) == 1.0
    assert _clamp(0.25) == 0.25
    assert _clamp(-2.0, -1.0, 1.0) == -1.0
    assert _clamp(2.0, -1.0, 1.0) == 1.0
    assert _clamp(0.25, -1.0, 1.0) == 0.25


@given(POSITIVE_PRICES)
def test_rsi_is_bounded(values: list[float]) -> None:
    result = _rsi(values, 5)
    assert result is not None
    assert 0.0 <= result <= 100.0


def test_rsi_exact_analytic_cases() -> None:
    assert _rsi([1, 2, 3, 4, 5, 6], 5) == 100.0
    assert _rsi([6, 5, 4, 3, 2, 1], 5) == 0.0
    assert _rsi([5, 5, 5, 5, 5, 5], 5) == 50.0
    assert _rsi([10, 12, 11, 14, 13, 15], 5) == pytest.approx(77.77777777777777)


def test_rsi_uses_only_the_requested_recent_window() -> None:
    assert _rsi([1000, 0, 10, 20, 30], 3) == 100.0
    assert _rsi([1, 2, 3, 4, 5], 5) is None
    assert _rsi([1, 2], 1) == 100.0
    assert _rsi([2, 1], 1) == 0.0


@given(POSITIVE_PRICES)
def test_bollinger_order_and_non_negative_width(values: list[float]) -> None:
    mid, upper, lower, width = _bollinger(values, 5)
    assert mid is not None and upper is not None and lower is not None and width is not None
    assert lower <= mid <= upper
    assert width >= 0.0


def test_bollinger_exact_population_statistics() -> None:
    mid, upper, lower, width = _bollinger([1, 2, 3, 4, 5], 5)
    deviation = math.sqrt(2.0)
    assert mid == 3.0
    assert upper == pytest.approx(3.0 + (2.0 * deviation))
    assert lower == pytest.approx(3.0 - (2.0 * deviation))
    assert width == pytest.approx(((4.0 * deviation) / 3.0) * 100.0)


def test_bollinger_constant_zero_mid_and_recent_window_cases() -> None:
    assert _bollinger([5, 5, 5, 5, 5], 5) == (5.0, 5.0, 5.0, 0.0)
    mid, upper, lower, width = _bollinger([-2, -1, 0, 1, 2], 5)
    assert mid == 0.0
    assert upper == pytest.approx(2.0 * math.sqrt(2.0))
    assert lower == pytest.approx(-2.0 * math.sqrt(2.0))
    assert width == 0.0
    assert _bollinger([1000, 1, 2, 3, 4, 5], 5) == pytest.approx(
        _bollinger([1, 2, 3, 4, 5], 5)
    )
    assert _bollinger([1, 2, 3, 4], 5) == (None, None, None, None)


@given(POSITIVE_PRICES)
def test_rate_of_change_is_finite_for_positive_prices(values: list[float]) -> None:
    result = _rate_of_change(values, 3)
    assert result is not None
    assert math.isfinite(result)


def test_rate_of_change_exact_signed_and_boundary_cases() -> None:
    assert _rate_of_change([100.0, 110.0], 1) == pytest.approx(10.0)
    assert _rate_of_change([100.0, 90.0], 1) == pytest.approx(-10.0)
    assert _rate_of_change([50.0, 100.0, 110.0], 1) == pytest.approx(10.0)
    assert _rate_of_change([100.0, 105.0, 110.0, 120.0], 3) == pytest.approx(20.0)
    assert _rate_of_change([0.0, 10.0], 1) is None
    assert _rate_of_change([100.0], 1) is None
