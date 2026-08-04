from __future__ import annotations

from pathlib import Path

import pytest

from crypto_quant_bot.backtest.noop_policy import apply_noop_wait_policy
from crypto_quant_bot.costs import config as cost_config
from crypto_quant_bot.costs.config import TransactionCostConfigError
from crypto_quant_bot.features.registry import (
    assert_features_registered,
    load_feature_registry,
    load_feature_registry_entries,
)


def test_feature_registry_handles_mapping_scalar_defaults_and_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "crypto_quant_bot.features.registry.load_simple_yaml",
        lambda _path: {
            "mapped": {"status": "active"},
            "named": {"name": "explicit"},
            "scalar": "planned",
        },
    )
    entries = load_feature_registry_entries("unused.yaml")
    assert entries == {
        "mapped": {"name": "mapped", "status": "active"},
        "named": {"name": "explicit"},
        "scalar": {"name": "scalar", "status": "planned"},
    }
    assert load_feature_registry("unused.yaml") == {
        "mapped": "active",
        "named": "",
        "scalar": "planned",
    }

    assert_features_registered(["mapped"], {"mapped": "active"})
    with pytest.raises(ValueError, match="unregistered features"):
        assert_features_registered(["missing"], {})
    for forbidden in ("future_return", "target_price", "target"):
        with pytest.raises(ValueError, match="forbidden future or target"):
            assert_features_registered([forbidden], {forbidden: "active"})


def test_noop_policy_covers_valid_degraded_and_invalid_quality() -> None:
    valid = apply_noop_wait_policy(
        {
            "quality_flag": "valid",
            "validation_status": "validated_lot9",
            "data_quality": {"status": "valid"},
        }
    )
    assert valid["decision"] == "WAIT"
    assert valid["trade_allowed"] is False
    assert valid["warnings"] == []

    degraded = apply_noop_wait_policy(
        {
            "quality_flag": "degraded",
            "validation_status": "unknown",
            "data_quality": {"status": "invalid"},
        }
    )
    assert degraded["warnings"] == [
        "market_state_not_validated_or_degraded",
        "market_state_data_quality_invalid",
    ]
    assert apply_noop_wait_policy({"data_quality": "invalid"})["warnings"] == [
        "market_state_not_validated_or_degraded"
    ]


def test_transaction_cost_config_rejects_missing_and_unsafe_sections(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "costs.yaml"

    monkeypatch.setattr(cost_config, "load_simple_yaml", lambda _path: {})
    with pytest.raises(TransactionCostConfigError, match="missing safety section"):
        cost_config.load_transaction_cost_config(path)

    monkeypatch.setattr(
        cost_config,
        "load_simple_yaml",
        lambda _path: {"safety": {"trade_allowed": True, "used_for_decision": False}},
    )
    with pytest.raises(TransactionCostConfigError, match="must be non-trading"):
        cost_config.load_transaction_cost_config(path)

    with pytest.raises(TransactionCostConfigError, match="missing section fee_model"):
        cost_config._get_nested({}, "fee_model", "maker_fee_bps")
    with pytest.raises(TransactionCostConfigError, match="missing fee_model.maker_fee_bps"):
        cost_config._get_nested({"fee_model": {}}, "fee_model", "maker_fee_bps")
    assert cost_config._get_nested(
        {"fee_model": {"maker_fee_bps": 1.0}},
        "fee_model",
        "maker_fee_bps",
    ) == 1.0


def test_raw_transaction_cost_loader_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"version": "test"}
    monkeypatch.setattr(cost_config, "load_simple_yaml", lambda _path: payload)
    assert cost_config.load_raw_transaction_cost_config("unused.yaml") is payload
