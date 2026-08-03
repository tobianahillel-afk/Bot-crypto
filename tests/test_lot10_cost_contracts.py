from crypto_quant_bot.contracts.costs import TransactionCostConfig, TransactionCostEstimate, TransactionCostRunResult


def test_lot10_contract_defaults_are_non_trading():
    config = TransactionCostConfig()
    estimate = TransactionCostEstimate()
    result = TransactionCostRunResult()
    assert config.trade_allowed is False
    assert config.used_for_decision is False
    assert estimate.side == "neutral"
    assert estimate.order_type == "hypothetical_noop"
    assert estimate.trade_allowed is False
    assert estimate.used_for_decision is False
    assert result.trade_allowed is False
    assert result.orders_created_count == 0
    assert result.fills_created_count == 0
    assert result.pnl_total == 0
    assert result.used_for_decision is False


def test_lot10_contracts_can_serialize():
    payload = TransactionCostEstimate(estimate_id="e1", total_cost_bps=41).to_dict()
    assert payload["estimate_id"] == "e1"
    assert payload["total_cost_bps"] == 41
    assert payload["side"] == "neutral"
