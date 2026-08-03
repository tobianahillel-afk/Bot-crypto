from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class PivotPoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    pivot_id: str = ""
    method: str = "fractal"
    side: str = "high"
    pivot_time: str = ""
    detected_at: str = ""
    confirmed_at: str = ""
    usable_from: str = ""
    left_window: int = 2
    right_window: int = 2
    lookback_window: int = 5
    price: float = 0.0
    candle_index: int = 0
    source_dataset_id: str = ""
    strength_score: float = 0.0
    strength_components: dict[str, Any] = field(default_factory=dict)
