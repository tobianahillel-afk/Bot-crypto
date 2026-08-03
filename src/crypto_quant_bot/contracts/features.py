from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class FeatureRow(BaseContract):
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    feature_set_id: str = ""
    source_dataset_id: str = ""
    data_version: str = "v1"
    features: dict[str, Any] = field(default_factory=dict)
