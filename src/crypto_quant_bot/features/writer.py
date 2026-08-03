from pathlib import Path

from crypto_quant_bot.contracts.features import FeatureRow
from crypto_quant_bot.data.data_writer import write_jsonl


def write_feature_rows(rows: list[FeatureRow], path: Path | str) -> Path:
    return write_jsonl(rows, path)
