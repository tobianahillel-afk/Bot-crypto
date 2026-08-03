from pathlib import Path

from crypto_quant_bot.contracts.range_state import RangeStatePoint
from crypto_quant_bot.contracts.volatility import VolatilityPoint
from crypto_quant_bot.data.data_writer import write_jsonl


def write_volatility_points(points: list[VolatilityPoint], path: Path | str) -> Path:
    return write_jsonl(points, path)


def write_range_state_points(points: list[RangeStatePoint], path: Path | str) -> Path:
    return write_jsonl(points, path)
