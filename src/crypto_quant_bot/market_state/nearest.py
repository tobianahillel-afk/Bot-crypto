from typing import Any


def _usable(row: dict[str, Any], current_available_at: str) -> bool:
    usable_from = row.get("usable_from") or row.get("available_at")
    return isinstance(usable_from, str) and usable_from <= current_available_at


def nearest_pivots(pivots: list[dict[str, Any]], close: float, current_available_at: str, limit: int = 3) -> list[dict[str, Any]]:
    usable = [row for row in pivots if _usable(row, current_available_at) and row.get("price") is not None]
    ordered = sorted(usable, key=lambda row: abs(float(row["price"]) - close))
    result: list[dict[str, Any]] = []
    for row in ordered[:limit]:
        result.append(
            {
                "pivot_id": row.get("pivot_id"),
                "side": row.get("side"),
                "price": row.get("price"),
                "pivot_time": row.get("pivot_time"),
                "usable_from": row.get("usable_from"),
                "available_at": row.get("available_at"),
                "strength_score": row.get("strength_score"),
            }
        )
    return result


def nearest_zones(zones: list[dict[str, Any]], close: float, current_available_at: str, limit: int = 3) -> list[dict[str, Any]]:
    usable = [row for row in zones if _usable(row, current_available_at) and row.get("center_price") is not None]
    ordered = sorted(usable, key=lambda row: abs(float(row["center_price"]) - close))
    result: list[dict[str, Any]] = []
    for row in ordered[:limit]:
        result.append(
            {
                "zone_id": row.get("zone_id"),
                "zone_type": row.get("zone_type"),
                "center_price": row.get("center_price"),
                "lower_bound": row.get("lower_bound"),
                "upper_bound": row.get("upper_bound"),
                "usable_from": row.get("usable_from"),
                "available_at": row.get("available_at"),
                "strength_score": row.get("strength_score"),
            }
        )
    return result
