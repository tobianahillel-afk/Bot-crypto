from crypto_quant_bot.regime.classifier import classify_state


def test_classifier_states_are_deterministic():
    kwargs = dict(
        trend_score=0.8,
        range_score=0.1,
        compression_score=0.2,
        expansion_score=0.2,
        volatility_score=0.2,
        trend_up_threshold=0.35,
        trend_down_threshold=-0.35,
        range_score_threshold=0.60,
        compression_threshold=0.70,
        expansion_threshold=0.70,
        volatility_high_threshold=0.70,
    )
    assert classify_state(direction_score=None, **kwargs) == "unknown"
    assert classify_state(direction_score=0.8, **kwargs) == "trend_up"
    assert classify_state(direction_score=-0.8, **kwargs) == "trend_down"
    assert classify_state(direction_score=0.0, range_score=0.8, **{k: v for k, v in kwargs.items() if k != "range_score"}) == "range"
    assert classify_state(direction_score=0.0, compression_score=0.8, **{k: v for k, v in kwargs.items() if k != "compression_score"}) == "compressed"
