from pathlib import Path

from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt


def test_lot2_resampler_counts_and_available_at():
    candles = parse_ohlcvt_csv(Path("tests/fixtures/btc_eur_ohlcvt_1m_60.csv"), pair="BTC/EUR", timeframe="1m", source="test")
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    candles_15m = resample_ohlcvt(candles, target_timeframe="15m")
    assert len(candles) == 60
    assert len(candles_5m) == 12
    assert len(candles_15m) == 4
    assert candles_5m[0].timestamp == "2026-05-25T00:00:00Z"
    assert candles_5m[0].closed_at == "2026-05-25T00:05:00Z"
    assert candles_5m[0].available_at == "2026-05-25T00:05:00Z"
    assert candles_15m[0].available_at == "2026-05-25T00:15:00Z"


def test_lot2_resampler_ohlcvt_aggregation():
    candles = parse_ohlcvt_csv(Path("tests/fixtures/btc_eur_ohlcvt_1m_60.csv"), pair="BTC/EUR", timeframe="1m", source="test")
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    bucket = candles[:5]
    first = candles_5m[0]
    assert first.open == bucket[0].open
    assert first.close == bucket[-1].close
    assert first.high == max(item.high for item in bucket)
    assert first.low == min(item.low for item in bucket)
    assert abs(first.volume - sum(item.volume for item in bucket)) < 1e-9
    assert first.trades == sum(item.trades for item in bucket)
    assert first.input_count == 5
