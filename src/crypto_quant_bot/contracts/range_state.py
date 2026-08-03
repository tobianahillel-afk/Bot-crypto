from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class RangeStatePoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    rolling_high_6: float | None = None
    rolling_low_6: float | None = None
    rolling_range_6: float | None = None
    rolling_mid_6: float | None = None
    close_position_in_range_6: float | None = None
    range_width_pct: float | None = None
    compression_score: float | None = None
    expansion_score: float | None = None
    range_state: str = "unknown"
    source_dataset_id: str = ""
