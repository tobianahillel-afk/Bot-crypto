from pathlib import Path

from crypto_quant_bot.contracts.market_state import MarketStatePoint
from crypto_quant_bot.data.data_writer import write_jsonl


def write_market_states(points: list[MarketStatePoint], path: Path | str) -> Path:
    return write_jsonl(points, path)
