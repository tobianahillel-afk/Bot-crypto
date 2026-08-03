from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.pivots.fractal import detect_fractal_pivots
from crypto_quant_bot.pivots.zones import build_price_zones
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt


def test_lot3_price_zones_are_created_from_pivots():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    pivots = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m")
    zones = build_price_zones(pivots, source_dataset_id="test_pivots")
    assert len(zones) == len(pivots)
    for zone in zones:
        assert zone.zone_type in {"support", "resistance"}
        assert zone.lower_bound <= zone.center_price <= zone.upper_bound
        assert zone.used_for_decision is False
        assert zone.source_pivot_ids
    pivot_by_id = {p.pivot_id: p for p in pivots}
    for zone in zones:
        pivot = pivot_by_id[zone.source_pivot_ids[0]]
        if pivot.side == "high":
            assert zone.zone_type == "resistance"
        else:
            assert zone.zone_type == "support"
