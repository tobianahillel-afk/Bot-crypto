from typing import Any


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def estimate_spread_bps(market_state: dict[str, Any], config_payload: dict[str, Any]) -> float:
    spread_model = config_payload.get("spread_model", {})
    if not isinstance(spread_model, dict):
        spread_model = {}
    default_spread = float(spread_model.get("default_spread_bps", 10))
    min_spread = float(spread_model.get("min_spread_bps", 1))
    max_spread = float(spread_model.get("max_spread_bps", 100))
    range_state = market_state.get("range_state", {})
    adjustment = 0.0
    if isinstance(range_state, dict):
        width = range_state.get("range_width_pct")
        if isinstance(width, int | float):
            adjustment = min(5.0, max(0.0, float(width) * 0.05))
    return round(_clamp(default_spread + adjustment, min_spread, max_spread), 8)
