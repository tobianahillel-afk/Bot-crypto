from statistics import mean

from crypto_quant_bot.contracts.timeframe import AggregatedCandle


def true_ranges(candles: list[AggregatedCandle]) -> list[float]:
    values: list[float] = []
    for index, candle in enumerate(candles):
        high_low = candle.high - candle.low
        if index == 0:
            values.append(high_low)
        else:
            previous_close = candles[index - 1].close
            values.append(max(high_low, abs(candle.high - previous_close), abs(candle.low - previous_close)))
    return values


def rolling_atr(true_range_values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(true_range_values)):
        window_values = true_range_values[max(0, index - window + 1): index + 1]
        result.append(mean(window_values) if len(window_values) == window else None)
    return result
