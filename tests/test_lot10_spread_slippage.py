from pathlib import Path

from crypto_quant_bot.costs.config import load_raw_transaction_cost_config
from crypto_quant_bot.costs.slippage import estimate_slippage_bps
from crypto_quant_bot.costs.spread import estimate_spread_bps

ROOT = Path(__file__).resolve().parents[1]


def test_lot10_spread_is_bounded():
    payload = load_raw_transaction_cost_config(ROOT / "config" / "transaction_costs.yaml")
    spread = estimate_spread_bps({}, payload)
    assert 1 <= spread <= 100
    assert spread == 10


def test_lot10_slippage_is_bounded_and_uses_base_when_missing():
    payload = load_raw_transaction_cost_config(ROOT / "config" / "transaction_costs.yaml")
    slippage = estimate_slippage_bps({}, payload)
    assert 0 <= slippage <= 150
    assert slippage == 5
