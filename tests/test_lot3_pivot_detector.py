from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.pivots.fractal import detect_fractal_pivots
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt


def test_lot3_fixture_resamples_and_detects_pivots():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    assert len(candles) == 180
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    candles_15m = resample_ohlcvt(candles, target_timeframe="15m")
    assert len(candles_5m) == 36
    assert len(candles_15m) == 12

    pivots_5m = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m")
    pivots_15m = detect_fractal_pivots(candles_15m, source_dataset_id="test_15m")
    assert sum(p.side == "high" for p in pivots_5m) >= 2
    assert sum(p.side == "low" for p in pivots_5m) >= 2
    assert sum(p.side == "high" for p in pivots_15m) >= 1
    assert sum(p.side == "low" for p in pivots_15m) >= 1
    assert all(p.method == "fractal" for p in pivots_5m + pivots_15m)
    assert all(0.0 <= p.strength_score <= 1.0 for p in pivots_5m + pivots_15m)


def test_lot3_no_pivots_without_complete_windows():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    pivots = detect_fractal_pivots(candles_5m[:4], source_dataset_id="too_short")
    assert pivots == []
