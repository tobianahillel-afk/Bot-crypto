from pathlib import Path

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_defensive_invariants_stay_unchanged():
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    assert "live_execution: DISABLED" in status_text
    assert "leverage: FORBIDDEN" in status_text
    assert "trade_allowed_default: false" in risk_text
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    assert decision.trading_decision == "WAIT"
    assert decision.system_decision == "BLOCK_TRADING"
    assert decision.trade_allowed is False
    assert risk.trade_allowed is False


def test_lot8_validate_script_is_direct_and_non_nested():
    text = (ROOT / "scripts" / "validate_lot8.py").read_text(encoding="utf-8")
    forbidden = [
        "subprocess.run",
        "subprocess.call",
        "Popen",
        "capture_" + "output=True",
        "validate_lot0.py",
        "validate_lot1.py",
        "validate_lot2.py",
        "validate_lot3.py",
        "validate_lot4.py",
        "validate_lot5.py",
        "validate_lot6.py",
        "validate_lot7.py",
    ]
    for token in forbidden:
        assert token not in text
