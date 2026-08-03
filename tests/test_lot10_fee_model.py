from pathlib import Path

from crypto_quant_bot.costs.config import load_transaction_cost_config
from crypto_quant_bot.costs.fees import calculate_fee_bps

ROOT = Path(__file__).resolve().parents[1]


def test_lot10_fee_model_uses_taker_for_hypothetical_noop():
    config = load_transaction_cost_config(ROOT / "config" / "transaction_costs.yaml")
    assert calculate_fee_bps("hypothetical_noop", config) == config.taker_fee_bps
    assert config.taker_fee_bps == 26
    assert config.trade_allowed is False
    assert config.used_for_decision is False
