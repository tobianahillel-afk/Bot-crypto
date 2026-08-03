from crypto_quant_bot.contracts.range_state import RangeStatePoint
from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.volatility.realized import percentile_rank


def _state(compression_score: float | None, expansion_score: float | None) -> str:
    if compression_score is None or expansion_score is None:
        return "unknown"
    if expansion_score >= 0.70:
        return "expanding"
    if compression_score >= 0.70:
        return "compressed"
    return "normal"


def compute_range_state_points(
    candles: list[AggregatedCandle],
    *,
    true_range_values: list[float],
    source_dataset_id: str,
    lineage_id: str,
    window: int = 6,
) -> list[RangeStatePoint]:
    points: list[RangeStatePoint] = []
    range_width_history: list[float] = []
    true_range_history: list[float] = []
    for index, candle in enumerate(candles):
        rolling_high = None
        rolling_low = None
        rolling_range = None
        rolling_mid = None
        close_position = None
        range_width_pct = None
        compression_score = None
        expansion_score = None
        if index + 1 >= window:
            bucket = candles[index - window + 1: index + 1]
            rolling_high = max(item.high for item in bucket)
            rolling_low = min(item.low for item in bucket)
            rolling_range = rolling_high - rolling_low
            rolling_mid = (rolling_high + rolling_low) / 2
            close_position = None if rolling_range == 0 else (candle.close - rolling_low) / rolling_range
            range_width_pct = None if candle.close == 0 else rolling_range / candle.close
            if range_width_pct is not None:
                range_width_history.append(range_width_pct)
            true_range_history.append(true_range_values[index])
            if len(range_width_history) >= window and len(true_range_history) >= window:
                compression_score = 1 - percentile_rank(range_width_pct, range_width_history)
                expansion_score = percentile_rank(true_range_values[index], true_range_history)
        points.append(
            RangeStatePoint(
                pair=candle.pair,
                timeframe=candle.target_timeframe,
                timestamp=candle.timestamp,
                available_at=candle.available_at,
                rolling_high_6=rolling_high,
                rolling_low_6=rolling_low,
                rolling_range_6=rolling_range,
                rolling_mid_6=rolling_mid,
                close_position_in_range_6=close_position,
                range_width_pct=range_width_pct,
                compression_score=compression_score,
                expansion_score=expansion_score,
                range_state=_state(compression_score, expansion_score),
                source_dataset_id=source_dataset_id,
                source="lot5_range_state_engine",
                lineage_id=lineage_id,
                quality_flag="valid",
                validation_status="validated_lot5",
                used_for_decision=False,
            )
        )
    return points
