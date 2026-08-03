from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class PriceZone(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    zone_id: str = ""
    zone_type: str = "support"
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    center_price: float = 0.0
    source_pivot_ids: list[str] = field(default_factory=list)
    touch_count: int = 1
    strength_score: float = 0.0
    first_seen_at: str = ""
    last_confirmed_at: str = ""
    usable_from: str = ""
    source_dataset_id: str = ""
