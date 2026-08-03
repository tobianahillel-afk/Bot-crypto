from crypto_quant_bot.core.config_loader import ConfigLoader
from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine


def test_lot2_defensive_invariants_unchanged():
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    statuses = ConfigLoader("config").load("module_status_matrix")
    assert decision.trading_decision == "WAIT"
    assert decision.system_decision == "BLOCK_TRADING"
    assert decision.trade_allowed is False
    assert risk.trade_allowed is False
    assert statuses["live_execution"] == "DISABLED"
    assert statuses["leverage"] == "FORBIDDEN"
