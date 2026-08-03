from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.core.config_loader import ConfigLoader
from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine


def test_lot1_keeps_default_wait_and_risk_block():
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    assert decision.trading_decision == "WAIT"
    assert decision.trade_allowed is False
    assert risk.trade_allowed is False
    assert "risk_veto" in risk.vetoes


def test_live_execution_disabled_and_leverage_forbidden():
    config = ConfigLoader(ROOT / "config")
    module_status = config.load("module_status_matrix")
    risk = config.load("risk")
    assert module_status["live_execution"] == "DISABLED"
    assert module_status["leverage"] == "FORBIDDEN"
    assert risk["trade_allowed_default"] is False
