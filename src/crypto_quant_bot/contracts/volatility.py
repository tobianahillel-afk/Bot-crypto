from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class VolatilityPoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    realized_volatility_3: float | None = None
    realized_volatility_6: float | None = None
    atr_3: float | None = None
    atr_6: float | None = None
    true_range: float | None = None
    hl_range: float | None = None
    oc_range: float | None = None
    close_to_close_abs_return: float | None = None
    volatility_percentile_lookback: float | None = None
    source_dataset_id: str = ""
