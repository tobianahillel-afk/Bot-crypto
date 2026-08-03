from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class AggregatedCandle(BaseContract):
    pair: str = "BTC/EUR"
    source_timeframe: str = "1m"
    target_timeframe: str = "5m"
    timestamp: str = ""
    closed_at: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    trades: int = 0
    input_count: int = 0
