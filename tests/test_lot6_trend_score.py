from crypto_quant_bot.regime.trend import compute_direction_scores


def test_direction_score_window_and_bounds():
    candles = [{"close": value} for value in [100, 101, 102, 104, 102, 98]]
    scores = compute_direction_scores(candles, window=3, scale=0.05)
    assert scores[:3] == [None, None, None]
    assert all(value is None or -1 <= value <= 1 for value in scores)
    assert scores[3] is not None and scores[3] > 0
    assert scores[5] is not None and scores[5] < 0
