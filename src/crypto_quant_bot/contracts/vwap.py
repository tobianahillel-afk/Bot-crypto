from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class VWAPPoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    vwap: float | None = None
    cumulative_price_volume: float = 0.0
    cumulative_volume: float = 0.0
    source_dataset_id: str = ""


@dataclass(frozen=True)
class AnchorPoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    anchor_id: str = ""
    anchor_type: str = "session_start"
    anchor_time: str = ""
    selected_at: str = ""
    usable_from: str = ""
    selection_rule: str = ""
    source_object_id: str = ""


@dataclass(frozen=True)
class AnchoredVWAPPoint(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    anchor_id: str = ""
    anchor_type: str = "session_start"
    anchor_time: str = ""
    timestamp: str = ""
    anchored_vwap: float | None = None
    cumulative_price_volume: float = 0.0
    cumulative_volume: float = 0.0
    source_dataset_id: str = ""
