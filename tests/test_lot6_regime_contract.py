from crypto_quant_bot.contracts.regime import RegimePoint


def test_regime_contract_defaults():
    point = RegimePoint(timestamp="2026-05-25T00:00:00Z")
    assert point.regime_state == "unknown"
    assert point.used_for_decision is False
    assert isinstance(point.components, dict)
    assert isinstance(point.source_dataset_ids, list)
