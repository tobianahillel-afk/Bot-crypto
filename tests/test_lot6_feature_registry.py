from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = [
    "direction_score",
    "trend_score",
    "range_score",
    "volatility_score",
    "regime_state",
    "regime_confidence_score",
]


def test_lot6_features_registered():
    config = (ROOT / "config/feature_registry.yaml").read_text(encoding="utf-8")
    docs = (ROOT / "docs/FEATURE_REGISTRY.md").read_text(encoding="utf-8")
    for feature in FEATURES:
        assert feature in config
        assert feature in docs
