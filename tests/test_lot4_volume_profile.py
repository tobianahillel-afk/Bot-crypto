from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.pivots.fractal import detect_fractal_pivots
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt
from crypto_quant_bot.volume.profile import build_volume_profile


def test_lot4_volume_profile_bins_share_and_poc():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    bins, summary = build_volume_profile(candles_5m, profile_id="test_profile", source_dataset_id="test_5m")
    assert bins
    assert summary.bin_count == len(bins)
    assert any(row.is_poc for row in bins)
    assert abs(sum(row.volume_share for row in bins) - 1.0) < 1e-6
    assert summary.poc_price > 0
    assert all(row.used_for_decision is False for row in bins)
    assert summary.used_for_decision is False
    assert summary.available_at == candles_5m[-1].available_at


def test_lot4_volume_profile_hvn_lvn_can_be_empty_without_breaking():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_15m = resample_ohlcvt(candles, target_timeframe="15m")
    bins, summary = build_volume_profile(candles_15m, profile_id="test_profile_15m", source_dataset_id="test_15m")
    assert bins
    assert isinstance(summary.hvn_prices, list)
    assert isinstance(summary.lvn_prices, list)
    assert any(row.is_poc for row in bins)


def test_lot4_pivot_detection_still_available_for_anchors():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    pivots = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m")
    assert any(p.side == "high" for p in pivots)
    assert any(p.side == "low" for p in pivots)
