from crypto_quant_bot.contracts.costs import TransactionCostConfig


def calculate_fee_bps(order_type: str, config: TransactionCostConfig) -> float:
    if order_type != "hypothetical_noop":
        raise ValueError("Lot 10 only supports hypothetical_noop")
    return float(config.taker_fee_bps)
