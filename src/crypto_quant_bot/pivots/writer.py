from pathlib import Path

from crypto_quant_bot.contracts.pivots import PivotPoint
from crypto_quant_bot.contracts.zones import PriceZone
from crypto_quant_bot.data.data_writer import write_jsonl


def write_pivots(pivots: list[PivotPoint], path: Path | str) -> Path:
    return write_jsonl(pivots, path)


def write_price_zones(zones: list[PriceZone], path: Path | str) -> Path:
    return write_jsonl(zones, path)
