from math import log, sqrt
from statistics import mean
from uuid import uuid4

from crypto_quant_bot.contracts.features import FeatureRow
from crypto_quant_bot.contracts.timeframe import AggregatedCandle

FEATURE_NAMES = [
    "close",
    "simple_return_1",
    "log_return_1",
    "hl_range",
    "oc_change",
    "typical_price",
    "true_range",
    "rolling_mean_close_3",
    "rolling_volatility_return_3",
    "volume_sum_3",
]


def sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    avg = mean(values)
    return sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def compute_basic_features(
    candles: list[AggregatedCandle],
    *,
    feature_set_id: str,
    source_dataset_id: str,
    data_version: str = "lot2_v1",
    lineage_id: str | None = None,
) -> list[FeatureRow]:
    lineage = lineage_id or str(uuid4())
    rows: list[FeatureRow] = []
    simple_returns: list[float | None] = []
    for index, candle in enumerate(candles):
        previous = candles[index - 1] if index > 0 else None
        simple_return = None if previous is None else candle.close / previous.close - 1
        log_return = None if previous is None else log(candle.close / previous.close)
        true_range = candle.high - candle.low
        if previous is not None:
            true_range = max(candle.high - candle.low, abs(candle.high - previous.close), abs(candle.low - previous.close))
        simple_returns.append(simple_return)
        close_window = [item.close for item in candles[max(0, index - 2) : index + 1]]
        volume_window = [item.volume for item in candles[max(0, index - 2) : index + 1]]
        return_window = [value for value in simple_returns[max(0, index - 2) : index + 1] if value is not None]
        features = {
            "close": candle.close,
            "simple_return_1": simple_return,
            "log_return_1": log_return,
            "hl_range": candle.high - candle.low,
            "oc_change": candle.close - candle.open,
            "typical_price": (candle.high + candle.low + candle.close) / 3,
            "true_range": true_range,
            "rolling_mean_close_3": mean(close_window) if len(close_window) == 3 else None,
            "rolling_volatility_return_3": sample_std(return_window) if len(return_window) == 3 else None,
            "volume_sum_3": sum(volume_window) if len(volume_window) == 3 else None,
        }
        rows.append(
            FeatureRow(
                pair=candle.pair,
                timeframe=candle.target_timeframe,
                timestamp=candle.timestamp,
                available_at=candle.available_at,
                feature_set_id=feature_set_id,
                source_dataset_id=source_dataset_id,
                data_version=data_version,
                features=features,
                source="lot2_basic_features",
                lineage_id=lineage,
                quality_flag="valid",
                validation_status="validated_lot2",
                used_for_decision=False,
            )
        )
    return rows
