from typing import Any


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def timeframe_weight(timeframe: str) -> float:
    weights = {
        "1m": 0.20,
        "5m": 0.45,
        "15m": 0.60,
        "1h": 0.75,
        "4h": 0.90,
        "1d": 1.00,
    }
    return weights.get(timeframe, 0.40)


def compute_pivot_strength(
    *,
    price: float,
    side: str,
    pivot_high: float,
    pivot_low: float,
    confirmation_close: float,
    pivot_volume: float,
    average_volume: float,
    timeframe: str,
) -> tuple[float, dict[str, Any]]:
    if price <= 0:
        reaction_component = 0.0
    elif side == "high":
        reaction_component = _clamp((price - confirmation_close) / price * 20.0)
    else:
        reaction_component = _clamp((confirmation_close - price) / price * 20.0)

    if average_volume <= 0:
        volume_component = 0.0
    else:
        volume_component = _clamp(pivot_volume / average_volume / 2.0)

    timeframe_component = timeframe_weight(timeframe)
    score = _clamp((reaction_component + volume_component + timeframe_component) / 3.0)
    components = {
        "reaction_component": round(reaction_component, 6),
        "volume_component": round(volume_component, 6),
        "timeframe_component": round(timeframe_component, 6),
        "pivot_high": pivot_high,
        "pivot_low": pivot_low,
        "confirmation_close": confirmation_close,
    }
    return round(score, 6), components
