from pathlib import Path

from crypto_quant_bot.contracts.volume_profile import VolumeProfileBin, VolumeProfileSummary
from crypto_quant_bot.contracts.vwap import AnchorPoint, AnchoredVWAPPoint, VWAPPoint
from crypto_quant_bot.data.data_writer import write_jsonl


def write_volume_profile(rows: list[VolumeProfileBin], path: Path | str) -> Path:
    return write_jsonl(rows, path)


def write_volume_profile_summary(rows: list[VolumeProfileSummary], path: Path | str) -> Path:
    return write_jsonl(rows, path)


def write_vwap(rows: list[VWAPPoint], path: Path | str) -> Path:
    return write_jsonl(rows, path)


def write_anchor_points(rows: list[AnchorPoint], path: Path | str) -> Path:
    return write_jsonl(rows, path)


def write_anchored_vwap(rows: list[AnchoredVWAPPoint], path: Path | str) -> Path:
    return write_jsonl(rows, path)
