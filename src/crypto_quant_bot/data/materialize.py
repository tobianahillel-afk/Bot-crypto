from pathlib import Path

from crypto_quant_bot.contracts.ohlcvt import OHLCVTCandle
from crypto_quant_bot.data.data_writer import write_jsonl as _write_jsonl


def write_jsonl(candles: list[OHLCVTCandle], path: Path | str) -> None:
    _write_jsonl(candles, path)
