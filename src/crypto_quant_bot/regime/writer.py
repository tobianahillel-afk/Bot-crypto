from pathlib import Path

from crypto_quant_bot.contracts.regime import RegimePoint
from crypto_quant_bot.data.data_writer import write_jsonl


def write_regime_points(points: list[RegimePoint], path: Path | str) -> Path:
    return write_jsonl(points, path)
