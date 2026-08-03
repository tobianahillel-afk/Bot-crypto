from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.risk.risk_engine import RiskEngine


def test_risk_engine_blocks_by_default():
    risk = RiskEngine().evaluate_default()
    assert risk.trade_allowed is False
    assert risk.reason == "default_block_until_validated"
    assert "risk_veto" in risk.vetoes
