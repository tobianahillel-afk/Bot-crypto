from typing import Any


def estimate_slippage_bps(market_state: dict[str, Any], config_payload: dict[str, Any]) -> float:
    slippage_model = config_payload.get("slippage_model", {})
    if not isinstance(slippage_model, dict):
        slippage_model = {}
    base = float(slippage_model.get("base_slippage_bps", 5))
    multiplier = float(slippage_model.get("volatility_multiplier", 1.0))
    maximum = float(slippage_model.get("max_slippage_bps", 150))
    volatility_component = 0.0
    volatility_state = market_state.get("volatility_state", {})
    if isinstance(volatility_state, dict):
        realized = volatility_state.get("realized_volatility_3")
        if isinstance(realized, int | float):
            volatility_component = min(maximum, abs(float(realized)) * 10000.0 * multiplier)
    return round(max(0.0, min(maximum, base + volatility_component)), 8)
