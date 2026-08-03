from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class MinimalMarketDataSnapshot(BaseContract):
    pair: str = "BTC/EUR"
    has_data: bool = False
    reason: str = "no_market_data_in_lot0"
