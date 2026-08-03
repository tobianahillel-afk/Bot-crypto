from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt
from crypto_quant_bot.volume.vwap import compute_session_vwap, typical_price


def test_lot4_vwap_first_value_equals_typical_price_when_volume_positive():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    rows = compute_session_vwap(candles_5m, source_dataset_id="test_5m")
    assert rows
    assert candles_5m[0].volume > 0
    assert abs(rows[0].vwap - typical_price(candles_5m[0])) < 1e-8
    assert rows[0].available_at == candles_5m[0].available_at
    assert all(row.used_for_decision is False for row in rows)


def test_lot4_vwap_cumulative_volume_never_decreases():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_15m = resample_ohlcvt(candles, target_timeframe="15m")
    rows = compute_session_vwap(candles_15m, source_dataset_id="test_15m")
    volumes = [row.cumulative_volume for row in rows]
    assert volumes == sorted(volumes)
    assert all(row.available_at >= row.timestamp for row in rows)
