from typing import Any


def clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def compute_direction_scores(candles: list[dict[str, Any]], window: int = 3, scale: float = 0.01) -> list[float | None]:
    scores: list[float | None] = []
    for index, candle in enumerate(candles):
        if index < window:
            scores.append(None)
            continue
        previous_close = float(candles[index - window]["close"])
        close = float(candle["close"])
        if previous_close == 0:
            scores.append(None)
            continue
        score = (close / previous_close - 1.0) / scale
        scores.append(round(clamp(score), 12))
    return scores
