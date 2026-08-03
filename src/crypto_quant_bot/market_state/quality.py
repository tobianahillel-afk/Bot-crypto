from typing import Any

ESSENTIAL_COMPONENTS = ["candle", "volatility_state", "range_state", "regime_state"]


def assess_data_quality(components: dict[str, Any]) -> dict[str, Any]:
    missing = [name for name in ESSENTIAL_COMPONENTS if not components.get(name)]
    optional_missing = [
        name
        for name in ["basic_features", "nearest_pivots", "nearest_zones", "vwap_state", "anchored_vwap_state"]
        if components.get(name) in (None, [], {})
    ]
    if "candle" in missing:
        status = "invalid"
    elif missing:
        status = "invalid"
    elif optional_missing:
        status = "degraded"
    else:
        status = "valid"
    return {
        "status": status,
        "missing_components": missing + optional_missing,
        "warning_count": len(missing) + len(optional_missing),
    }
