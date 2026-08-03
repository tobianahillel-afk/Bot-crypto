from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.contracts.volatility import VolatilityPoint
from crypto_quant_bot.volatility.atr import rolling_atr, true_ranges
from crypto_quant_bot.volatility.realized import percentile_rank, rolling_realized_volatility, simple_returns


def compute_volatility_points(
    candles: list[AggregatedCandle],
    *,
    source_dataset_id: str,
    lineage_id: str,
) -> tuple[list[VolatilityPoint], list[float]]:
    returns = simple_returns(candles)
    rv3 = rolling_realized_volatility(returns, 3)
    rv6 = rolling_realized_volatility(returns, 6)
    tr_values = true_ranges(candles)
    atr3 = rolling_atr(tr_values, 3)
    atr6 = rolling_atr(tr_values, 6)
    tr_history: list[float] = []
    points: list[VolatilityPoint] = []
    for index, candle in enumerate(candles):
        previous_close = candles[index - 1].close if index > 0 else None
        close_to_close_abs_return = None if previous_close is None else abs(candle.close / previous_close - 1)
        tr_history.append(tr_values[index])
        percentile = percentile_rank(tr_values[index], tr_history) if len(tr_history) >= 6 else None
        points.append(
            VolatilityPoint(
                pair=candle.pair,
                timeframe=candle.target_timeframe,
                timestamp=candle.timestamp,
                available_at=candle.available_at,
                realized_volatility_3=rv3[index],
                realized_volatility_6=rv6[index],
                atr_3=atr3[index],
                atr_6=atr6[index],
                true_range=tr_values[index],
                hl_range=candle.high - candle.low,
                oc_range=candle.close - candle.open,
                close_to_close_abs_return=close_to_close_abs_return,
                volatility_percentile_lookback=percentile,
                source_dataset_id=source_dataset_id,
                source="lot5_volatility_engine",
                lineage_id=lineage_id,
                quality_flag="valid",
                validation_status="validated_lot5",
                used_for_decision=False,
            )
        )
    return points, tr_values
