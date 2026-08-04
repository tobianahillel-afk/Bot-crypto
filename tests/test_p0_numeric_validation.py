from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from crypto_quant_bot.market_analysis import (
    technical_indicators,
    trend_range_momentum,
    volatility_regime_confluence,
)
from crypto_quant_bot.market_analysis.numeric import (
    DATA_QUALITY_ERROR_CODE,
    DataQualityError,
    require_finite_float,
)

MODULES = (
    technical_indicators,
    trend_range_momentum,
    volatility_regime_confluence,
)


@given(
    st.floats(
        min_value=-1e15,
        max_value=1e15,
        allow_nan=False,
        allow_infinity=False,
        width=64,
    )
)
def test_require_finite_float_round_trip(value: float) -> None:
    result = require_finite_float(value, field_name="property_value")
    assert result == float(value)
    assert math.isfinite(result)


def test_require_finite_float_exact_integer_float_and_negative_zero() -> None:
    assert require_finite_float(7, field_name="integer") == 7.0
    assert require_finite_float(-2.5, field_name="float") == -2.5
    result = require_finite_float(-0.0, field_name="negative_zero")
    assert result == 0.0
    assert math.copysign(1.0, result) == -1.0


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "expected_int_or_float"),
        ("1.25", "expected_int_or_float"),
        ("", "expected_int_or_float"),
        (True, "boolean_is_not_numeric_market_data"),
        (False, "boolean_is_not_numeric_market_data"),
        (float("nan"), "non_finite_numeric_value"),
        (float("inf"), "non_finite_numeric_value"),
        (float("-inf"), "non_finite_numeric_value"),
    ],
)
def test_require_finite_float_rejects_invalid_values_with_auditable_reason(
    value: object, reason: str
) -> None:
    with pytest.raises(DataQualityError) as captured:
        require_finite_float(value, field_name="market_input")
    error = captured.value
    assert error.field_name == "market_input"
    assert error.value is value
    assert error.reason == reason
    assert str(error).startswith(f"{DATA_QUALITY_ERROR_CODE}:market_input:{reason}:")


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("value", [None, "0", True, float("nan"), float("inf")])
def test_market_modules_fail_closed_instead_of_returning_zero(module: object, value: object) -> None:
    with pytest.raises(DataQualityError):
        module._as_float(value)  # type: ignore[attr-defined]


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("value", [-12, 0, 1.25])
def test_market_module_numeric_wrappers_preserve_valid_values(module: object, value: object) -> None:
    assert module._as_float(value) == float(value)  # type: ignore[attr-defined]
