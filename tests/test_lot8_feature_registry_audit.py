import json
from pathlib import Path

from crypto_quant_bot.audit.feature_registry_audit import audit_feature_registry
from crypto_quant_bot.features.registry import load_feature_registry_entries

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_feature_registry_audit_is_clean():
    payload = json.loads((ROOT / "data" / "audit" / "feature_registry_audit_lot8.json").read_text(encoding="utf-8"))
    assert payload["validation_status"] == "validated_lot8"
    assert payload["quality_flag"] == "valid"
    assert payload["missing_from_registry"] == []
    assert payload["forbidden_feature_names"] == []
    assert payload["lookahead_violations"] == []
    assert payload["available_at_violations"] == []
    assert payload["used_for_decision_violations"] == []


def test_lot8_feature_registry_contains_required_lot2_lot5_lot6_entries():
    entries = load_feature_registry_entries(ROOT / "config" / "feature_registry.yaml")
    required = [
        "close",
        "simple_return_1",
        "log_return_1",
        "true_range",
        "rolling_mean_close_3",
        "realized_volatility_3",
        "realized_volatility_6",
        "atr_3",
        "atr_6",
        "range_state",
        "direction_score",
        "trend_score",
        "range_score",
        "volatility_score",
        "regime_state",
        "regime_confidence_score",
    ]
    for name in required:
        assert name in entries
        assert entries[name]["status"] == "MVP_REQUIRED"
        assert entries[name]["lookahead_safe"] is True
        for field in ["name", "description", "inputs", "formula", "timeframe", "available_at_rule", "lookahead_safe", "status"]:
            assert field in entries[name]


def test_lot8_feature_registry_audit_function_returns_valid_result():
    result = audit_feature_registry(ROOT)
    assert result.validation_status == "validated_lot8"
    assert result.missing_from_registry == []
