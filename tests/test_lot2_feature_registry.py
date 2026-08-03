from crypto_quant_bot.features.basic import FEATURE_NAMES
from crypto_quant_bot.features.registry import assert_features_registered, load_feature_registry


def test_lot2_feature_registry_contains_all_basic_features():
    registry = load_feature_registry("config/feature_registry.yaml")
    assert_features_registered(FEATURE_NAMES, registry)
    for name in FEATURE_NAMES:
        assert registry[name] == "MVP_REQUIRED"
