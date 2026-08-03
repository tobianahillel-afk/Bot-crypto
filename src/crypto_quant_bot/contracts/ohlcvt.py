from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class OHLCVTCandle(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "1m"
    timestamp: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    trades: int = 0
