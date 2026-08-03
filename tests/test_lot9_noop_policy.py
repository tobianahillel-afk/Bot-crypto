from crypto_quant_bot.backtest.noop_policy import POLICY_NAME, apply_noop_wait_policy


def test_noop_policy_always_waits_and_creates_no_trade_objects():
    decision = apply_noop_wait_policy({"quality_flag": "valid", "validation_status": "validated_lot7"})
    assert decision["policy_name"] == POLICY_NAME
    assert decision["decision"] == "WAIT"
    assert decision["trade_allowed"] is False
    assert decision["orders_created"] == []
    assert decision["fills_created"] == []
    assert decision["pnl_impact"] == 0
