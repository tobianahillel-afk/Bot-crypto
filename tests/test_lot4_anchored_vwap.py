from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.pivots.fractal import detect_fractal_pivots
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt
from crypto_quant_bot.volume.anchors import build_anchor_points, compute_anchored_vwap


def test_lot4_session_and_pivot_anchors_exist():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    candles_15m = resample_ohlcvt(candles, target_timeframe="15m")
    pivots_5m = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m")
    anchors = build_anchor_points({"5m": candles_5m, "15m": candles_15m}, {"5m": pivots_5m, "15m": []})
    anchors_5m = anchors["5m"]
    anchors_15m = anchors["15m"]
    assert any(anchor.anchor_id == "session_start_5m" for anchor in anchors_5m)
    assert any(anchor.anchor_id == "session_start_15m" for anchor in anchors_15m)
    assert any(anchor.anchor_type == "pivot_high" for anchor in anchors_5m)
    assert any(anchor.anchor_type == "pivot_low" for anchor in anchors_5m)


def test_lot4_pivot_anchor_usable_from_matches_pivot_usable_from():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    pivots = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m")
    anchors = build_anchor_points({"5m": candles_5m}, {"5m": pivots})["5m"]
    pivot_by_id = {pivot.pivot_id: pivot for pivot in pivots}
    for anchor in anchors:
        if anchor.anchor_type in {"pivot_high", "pivot_low"}:
            pivot = pivot_by_id[anchor.source_object_id]
            assert anchor.anchor_time == pivot.pivot_time
            assert anchor.selected_at == pivot.usable_from
            assert anchor.usable_from == pivot.usable_from
            assert anchor.usable_from >= anchor.selected_at >= anchor.anchor_time


def test_lot4_anchored_vwap_no_points_before_usable_from():
    candles = parse_ohlcvt_csv(
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        pair="BTC/EUR",
        timeframe="1m",
        source="test",
    )
    candles_5m = resample_ohlcvt(candles, target_timeframe="5m")
    pivots = detect_fractal_pivots(candles_5m, source_dataset_id="test_5m")
    anchors = build_anchor_points({"5m": candles_5m}, {"5m": pivots})["5m"]
    rows = compute_anchored_vwap(candles_5m, anchors, source_dataset_id="test_5m")
    anchor_by_id = {anchor.anchor_id: anchor for anchor in anchors}
    assert rows
    for row in rows:
        assert row.available_at >= anchor_by_id[row.anchor_id].usable_from
        assert row.used_for_decision is False
