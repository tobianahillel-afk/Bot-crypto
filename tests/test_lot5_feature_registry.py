from crypto_quant_bot.features.registry import load_feature_registry


def test_lot5_features_declared_in_registry():
    registry = load_feature_registry("config/feature_registry.yaml")
    for name in [
        "realized_volatility_3",
        "realized_volatility_6",
        "true_range",
        "atr_3",
        "atr_6",
        "rolling_high_6",
        "rolling_low_6",
        "rolling_range_6",
        "rolling_mid_6",
        "close_position_in_range_6",
        "range_width_pct",
        "compression_score",
        "expansion_score",
        "range_state",
    ]:
        assert registry[name] == "MVP_REQUIRED"
