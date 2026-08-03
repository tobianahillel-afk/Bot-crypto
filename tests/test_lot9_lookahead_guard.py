from crypto_quant_bot.backtest.lookahead_guard import check_market_state_no_lookahead, check_step_no_lookahead


def test_lookahead_guard_accepts_safe_market_state_and_step():
    market_state = {
        "timestamp": "2026-05-25T00:00:00Z",
        "available_at": "2026-05-25T00:05:00Z",
        "component_available_at": {"candle": "2026-05-25T00:05:00Z"},
    }
    step = {"available_at": "2026-05-25T00:05:00Z", "decision": "WAIT"}
    assert check_market_state_no_lookahead(market_state, step["available_at"]) == []
    assert check_step_no_lookahead(step, market_state) == []


def test_lookahead_guard_rejects_future_component_and_forbidden_keys():
    market_state = {
        "available_at": "2026-05-25T00:05:00Z",
        "component_available_at": {"candle": "2026-05-25T00:10:00Z"},
        "future_price": 1,
    }
    violations = check_market_state_no_lookahead(market_state, "2026-05-25T00:05:00Z")
    rules = {violation["rule"] for violation in violations}
    assert "component_available_at <= market_state.available_at" in rules
    assert "forbidden key" in rules
