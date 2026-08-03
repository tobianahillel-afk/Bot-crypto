from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class VolumeProfileBin(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    profile_id: str = ""
    bin_id: str = ""
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    center_price: float = 0.0
    volume: float = 0.0
    trade_count: float = 0.0
    volume_share: float = 0.0
    is_poc: bool = False
    is_hvn: bool = False
    is_lvn: bool = False
    source_dataset_id: str = ""


@dataclass(frozen=True)
class VolumeProfileSummary(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    profile_id: str = ""
    start_timestamp: str = ""
    end_timestamp: str = ""
    bin_size: float = 50.0
    total_volume: float = 0.0
    total_trades: float = 0.0
    poc_price: float = 0.0
    poc_volume: float = 0.0
    hvn_prices: list[float] = field(default_factory=list)
    lvn_prices: list[float] = field(default_factory=list)
    bin_count: int = 0
    source_dataset_id: str = ""
