from typing import Any


def compute_replay_metrics(steps: list[dict[str, Any]], lookahead_violations: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts: dict[str, int] = {}
    invalid_state_count = 0
    degraded_state_count = 0
    orders_created_count = 0
    fills_created_count = 0
    pnl_total: int | float = 0
    for step in steps:
        decision = str(step.get("decision", ""))
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        warnings = step.get("warnings")
        if isinstance(warnings, list):
            if "market_state_data_quality_invalid" in warnings:
                invalid_state_count += 1
            if "market_state_not_validated_or_degraded" in warnings:
                degraded_state_count += 1
        orders = step.get("orders_created")
        fills = step.get("fills_created")
        if isinstance(orders, list):
            orders_created_count += len(orders)
        if isinstance(fills, list):
            fills_created_count += len(fills)
        pnl_total += step.get("pnl_impact", 0) or 0
    return {
        "step_count": len(steps),
        "decision_counts": decision_counts,
        "invalid_state_count": invalid_state_count,
        "degraded_state_count": degraded_state_count,
        "orders_created_count": orders_created_count,
        "fills_created_count": fills_created_count,
        "pnl_total": pnl_total,
        "lookahead_violation_count": len(lookahead_violations),
    }
