from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class MarketStatePoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    market_state_id: str = ""
    candle: dict[str, Any] = field(default_factory=dict)
    basic_features: dict[str, Any] | None = None
    nearest_pivots: list[dict[str, Any]] = field(default_factory=list)
    nearest_zones: list[dict[str, Any]] = field(default_factory=list)
    vwap_state: dict[str, Any] | None = None
    anchored_vwap_state: list[dict[str, Any]] = field(default_factory=list)
    volatility_state: dict[str, Any] | None = None
    range_state: dict[str, Any] | None = None
    regime_state: dict[str, Any] | None = None
    data_quality: dict[str, Any] = field(default_factory=dict)
    component_available_at: dict[str, str] = field(default_factory=dict)
    source_dataset_ids: list[str] = field(default_factory=list)
