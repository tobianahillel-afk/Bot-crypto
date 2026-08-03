from typing import Any

POLICY_NAME = "noop_wait_policy"


def apply_noop_wait_policy(market_state: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    if market_state.get("quality_flag") != "valid" or market_state.get("validation_status") not in {"validated_lot7", "validated_lot8", "validated_lot9"}:
        warnings.append("market_state_not_validated_or_degraded")
    data_quality = market_state.get("data_quality")
    if isinstance(data_quality, dict) and data_quality.get("status") == "invalid":
        warnings.append("market_state_data_quality_invalid")
    return {
        "policy_name": POLICY_NAME,
        "decision": "WAIT",
        "trade_allowed": False,
        "orders_created": [],
        "fills_created": [],
        "pnl_impact": 0,
        "warnings": warnings,
    }
