from uuid import uuid4

from crypto_quant_bot.contracts.pivots import PivotPoint
from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.pivots.strength import compute_pivot_strength


def _average_volume(candles: list[AggregatedCandle]) -> float:
    if not candles:
        return 0.0
    return sum(c.volume for c in candles) / len(candles)


def detect_fractal_pivots(
    candles: list[AggregatedCandle],
    *,
    source_dataset_id: str,
    left_window: int = 2,
    right_window: int = 2,
    source: str = "lot3_fractal_pivot_engine",
    lineage_id: str | None = None,
) -> list[PivotPoint]:
    if left_window < 1 or right_window < 1:
        raise ValueError("left_window and right_window must be >= 1")
    if len(candles) < left_window + right_window + 1:
        return []

    lineage = lineage_id or str(uuid4())
    pivots: list[PivotPoint] = []
    lookback_window = left_window + right_window + 1
    avg_volume = _average_volume(candles)

    for index in range(left_window, len(candles) - right_window):
        pivot = candles[index]
        left = candles[index - left_window : index]
        right = candles[index + 1 : index + 1 + right_window]
        if len(left) != left_window or len(right) != right_window:
            continue

        is_high = all(pivot.high > item.high for item in left) and all(pivot.high > item.high for item in right)
        is_low = all(pivot.low < item.low for item in left) and all(pivot.low < item.low for item in right)
        confirmation = candles[index + right_window]

        if is_high:
            score, components = compute_pivot_strength(
                price=pivot.high,
                side="high",
                pivot_high=pivot.high,
                pivot_low=pivot.low,
                confirmation_close=confirmation.close,
                pivot_volume=pivot.volume,
                average_volume=avg_volume,
                timeframe=pivot.target_timeframe,
            )
            pivots.append(
                PivotPoint(
                    pair=pivot.pair,
                    timeframe=pivot.target_timeframe,
                    pivot_id=f"pivot_{pivot.pair.replace('/', '_').lower()}_{pivot.target_timeframe}_{index}_high_{uuid4().hex[:8]}",
                    method="fractal",
                    side="high",
                    pivot_time=pivot.timestamp,
                    detected_at=confirmation.available_at,
                    confirmed_at=confirmation.available_at,
                    usable_from=confirmation.available_at,
                    available_at=confirmation.available_at,
                    left_window=left_window,
                    right_window=right_window,
                    lookback_window=lookback_window,
                    price=pivot.high,
                    candle_index=index,
                    source_dataset_id=source_dataset_id,
                    strength_score=score,
                    strength_components=components,
                    source=source,
                    lineage_id=lineage,
                    quality_flag="valid",
                    validation_status="validated_lot3",
                    used_for_decision=False,
                )
            )

        if is_low:
            score, components = compute_pivot_strength(
                price=pivot.low,
                side="low",
                pivot_high=pivot.high,
                pivot_low=pivot.low,
                confirmation_close=confirmation.close,
                pivot_volume=pivot.volume,
                average_volume=avg_volume,
                timeframe=pivot.target_timeframe,
            )
            pivots.append(
                PivotPoint(
                    pair=pivot.pair,
                    timeframe=pivot.target_timeframe,
                    pivot_id=f"pivot_{pivot.pair.replace('/', '_').lower()}_{pivot.target_timeframe}_{index}_low_{uuid4().hex[:8]}",
                    method="fractal",
                    side="low",
                    pivot_time=pivot.timestamp,
                    detected_at=confirmation.available_at,
                    confirmed_at=confirmation.available_at,
                    usable_from=confirmation.available_at,
                    available_at=confirmation.available_at,
                    left_window=left_window,
                    right_window=right_window,
                    lookback_window=lookback_window,
                    price=pivot.low,
                    candle_index=index,
                    source_dataset_id=source_dataset_id,
                    strength_score=score,
                    strength_components=components,
                    source=source,
                    lineage_id=lineage,
                    quality_flag="valid",
                    validation_status="validated_lot3",
                    used_for_decision=False,
                )
            )

    return pivots
