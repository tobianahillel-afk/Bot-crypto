from pathlib import Path

from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.features.basic import FEATURE_NAMES, compute_basic_features
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt


def test_lot2_basic_features_exist_and_have_initial_nulls():
    candles = parse_ohlcvt_csv(Path("tests/fixtures/btc_eur_ohlcvt_1m_60.csv"), pair="BTC/EUR", timeframe="1m", source="test")
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    rows = compute_basic_features(candles_5m, feature_set_id="test_features", source_dataset_id="test_dataset")
    assert len(rows) == 12
    assert set(FEATURE_NAMES) == set(rows[0].features)
    assert rows[0].features["simple_return_1"] is None
    assert rows[0].features["log_return_1"] is None
    assert rows[0].features["rolling_mean_close_3"] is None
    assert rows[0].features["rolling_volatility_return_3"] is None
    assert rows[0].features["volume_sum_3"] is None
    assert rows[2].features["rolling_mean_close_3"] is not None
    assert rows[3].features["rolling_volatility_return_3"] is not None


def test_lot2_features_are_not_future_or_target():
    candles = parse_ohlcvt_csv(Path("tests/fixtures/btc_eur_ohlcvt_1m_60.csv"), pair="BTC/EUR", timeframe="1m", source="test")
    rows = compute_basic_features(resample_ohlcvt(candles, target_timeframe="15m"), feature_set_id="test", source_dataset_id="test")
    for row in rows:
        for name in row.features:
            assert not name.startswith("future_")
            assert name != "target"
            assert not name.startswith("target")
