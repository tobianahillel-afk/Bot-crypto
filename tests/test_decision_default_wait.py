from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.decision.decision_engine import DecisionEngine


def test_default_decision_wait_and_block_trading():
    decision = DecisionEngine().decide_default()
    assert decision.trading_decision == "WAIT"
    assert decision.system_decision == "BLOCK_TRADING"
    assert decision.trade_allowed is False
    assert decision.replay_id
