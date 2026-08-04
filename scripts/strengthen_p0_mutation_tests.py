from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "apply_p0_hardening.py"

PROPERTY_BLOCK = r'''PROPERTY_TESTS = dedent(
    '''
    from __future__ import annotations

    import math

    import pytest
    from hypothesis import given, strategies as st

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
    '''
).lstrip()'''

NUMERIC_BLOCK = r'''NUMERIC_TESTS = dedent(
    '''
    from __future__ import annotations

    import math

    import pytest
    from hypothesis import given, strategies as st

    from crypto_quant_bot.market_analysis import technical_indicators
    from crypto_quant_bot.market_analysis import trend_range_momentum
    from crypto_quant_bot.market_analysis import volatility_regime_confluence
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
    '''
).lstrip()'''


def replace_section(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


def main() -> int:
    text = MIGRATOR.read_text(encoding="utf-8")
    text = replace_section(
        text,
        "PROPERTY_TESTS = dedent(",
        "\n\nNUMERIC_TESTS = dedent(",
        PROPERTY_BLOCK,
    )
    text = replace_section(
        text,
        "NUMERIC_TESTS = dedent(",
        "\n\nPARAMETER_TESTS = dedent(",
        NUMERIC_BLOCK,
    )

    old = """              mutmut run 2>&1 | tee reports/quality/mutation_run.txt
              mutmut results 2>&1 | tee reports/quality/mutation_results.txt
"""
    new = """              : > reports/quality/mutation_run.txt
              for target in \\
                'crypto_quant_bot.market_analysis.technical_indicators.x__clamp__mutmut_*' \\
                'crypto_quant_bot.market_analysis.technical_indicators.x__rsi__mutmut_*' \\
                'crypto_quant_bot.market_analysis.technical_indicators.x__bollinger__mutmut_*' \\
                'crypto_quant_bot.market_analysis.technical_indicators.x__rate_of_change__mutmut_*' \\
                'crypto_quant_bot.market_analysis.numeric.x_require_finite_float__mutmut_*'
              do
                mutmut run "$target" 2>&1 | tee -a reports/quality/mutation_run.txt
              done
              mutmut results 2>&1 | tee reports/quality/mutation_results.txt
"""
    if text.count(old) != 1:
        raise RuntimeError("generated mutation command block not found exactly once")
    text = text.replace(old, new, 1)

    MIGRATOR.write_text(text, encoding="utf-8")
    Path(__file__).unlink()
    print("P0_EXACT_MUTATION_ORACLES_APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
