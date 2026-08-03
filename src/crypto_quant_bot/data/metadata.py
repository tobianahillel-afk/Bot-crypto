from pathlib import Path

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.contracts.ohlcvt import OHLCVTCandle
from crypto_quant_bot.data.checksum import sha256_file


def build_dataset_metadata(
    *,
    dataset_id: str,
    dataset_name: str,
    path: Path | str,
    candles: list[OHLCVTCandle],
    pair: str,
    timeframe: str,
    source: str,
    layer: str,
    data_version: str,
) -> DatasetMetadata:
    start = candles[0].timestamp if candles else ""
    end = candles[-1].timestamp if candles else ""
    lineage = candles[0].lineage_id if candles else ""
    return DatasetMetadata(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        pair=pair,
        timeframe=timeframe,
        source=source,
        layer=layer,
        data_version=data_version,
        start_timestamp=start,
        end_timestamp=end,
        row_count=len(candles),
        checksum=sha256_file(path),
        lineage_id=lineage,
        quality_flag="valid",
        validation_status="validated_lot1",
        used_for_decision=False,
    )
