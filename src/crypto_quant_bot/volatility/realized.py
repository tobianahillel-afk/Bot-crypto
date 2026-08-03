from math import log, sqrt
from statistics import mean

from crypto_quant_bot.contracts.timeframe import AggregatedCandle


def sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    avg = mean(values)
    return sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def simple_returns(candles: list[AggregatedCandle]) -> list[float | None]:
    values: list[float | None] = []
    for index, candle in enumerate(candles):
        if index == 0:
            values.append(None)
        else:
            values.append(candle.close / candles[index - 1].close - 1)
    return values


def log_returns(candles: list[AggregatedCandle]) -> list[float | None]:
    values: list[float | None] = []
    for index, candle in enumerate(candles):
        if index == 0:
            values.append(None)
        else:
            values.append(log(candle.close / candles[index - 1].close))
    return values


def rolling_realized_volatility(returns: list[float | None], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(returns)):
        window_values = [value for value in returns[max(0, index - window + 1): index + 1] if value is not None]
        result.append(sample_std(window_values) if len(window_values) == window else None)
    return result


def percentile_rank(value: float | None, history: list[float]) -> float | None:
    if value is None or not history:
        return None
    lower_or_equal = sum(1 for item in history if item <= value)
    return lower_or_equal / len(history)
