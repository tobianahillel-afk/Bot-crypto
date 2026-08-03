from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.pivots.fractal import detect_fractal_pivots
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt


def test_lot3_pivot_confirmed_at_equals_right_window_available_at():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    pivots = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m", left_window=2, right_window=2)
    assert pivots
    for pivot in pivots:
        expected_confirmation = candles_5m[pivot.candle_index + pivot.right_window].available_at
        assert pivot.confirmed_at == expected_confirmation
        assert pivot.usable_from == expected_confirmation
        assert pivot.available_at == expected_confirmation
        assert pivot.usable_from >= pivot.pivot_time
        assert pivot.used_for_decision is False
