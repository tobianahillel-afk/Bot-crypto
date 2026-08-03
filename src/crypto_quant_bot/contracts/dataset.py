from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class DatasetMetadata(BaseContract):
    dataset_id: str = ""
    dataset_name: str = ""
    pair: str = "BTC/EUR"
    timeframe: str = "1m"
    layer: str = "raw"
    data_version: str = "v1"
    start_timestamp: str = ""
    end_timestamp: str = ""
    row_count: int = 0
    checksum: str = ""
