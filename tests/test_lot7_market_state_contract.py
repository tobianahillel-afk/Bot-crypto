from crypto_quant_bot.contracts.market_state import MarketStatePoint


def test_market_state_contract_defaults():
    point = MarketStatePoint(timestamp="2026-05-25T00:00:00Z", market_state_id="ms_test")
    data = point.to_dict()
    assert data["pair"] == "BTC/EUR"
    assert data["timeframe"] == "5m"
    assert data["market_state_id"] == "ms_test"
    assert data["used_for_decision"] is False
    assert isinstance(data["component_available_at"], dict)
