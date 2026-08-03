from crypto_quant_bot.contracts.backtest import BacktestRunConfig, BacktestRunResult, BacktestStep


def test_lot9_backtest_contract_defaults_are_safe():
    config = BacktestRunConfig(run_id="run")
    step = BacktestStep(run_id="run", step_id="step")
    result = BacktestRunResult(run_id="run")
    assert config.mode == "replay_v0"
    assert config.policy_name == "noop_wait_policy"
    assert config.trade_allowed is False
    assert step.decision == "WAIT"
    assert step.trade_allowed is False
    assert step.orders_created == []
    assert step.fills_created == []
    assert step.pnl_impact == 0
    assert step.used_for_decision is False
    assert result.orders_created_count == 0
    assert result.fills_created_count == 0
    assert result.pnl_total == 0
    assert result.lookahead_violations == []
    assert result.used_for_decision is False
