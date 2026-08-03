from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class RegimePoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    regime_id: str = ""
    regime_state: str = "unknown"
    trend_score: float | None = None
    range_score: float | None = None
    compression_score: float | None = None
    expansion_score: float | None = None
    volatility_score: float | None = None
    direction_score: float | None = None
    confidence_score: float | None = None
    components: dict[str, Any] = field(default_factory=dict)
    source_dataset_ids: list[str] = field(default_factory=list)
