from typing import Any

from crypto_quant_bot.contracts.market_state import MarketStatePoint
from crypto_quant_bot.market_state.nearest import nearest_pivots, nearest_zones
from crypto_quant_bot.market_state.quality import assess_data_quality


def _compact(row: dict[str, Any] | None, keys: list[str] | None = None) -> dict[str, Any] | None:
    if row is None:
        return None
    if keys is None:
        return dict(row)
    return {key: row.get(key) for key in keys if key in row}


def _max_available(component_available_at: dict[str, str]) -> str:
    values = [value for value in component_available_at.values() if isinstance(value, str) and value]
    if not values:
        return ""
    return max(values)


def _availability(name: str, row: dict[str, Any] | None, out: dict[str, str]) -> None:
    if row and isinstance(row.get("available_at"), str):
        out[name] = str(row["available_at"])


def assemble_market_states(
    *,
    pair: str,
    timeframe: str,
    candles: list[dict[str, Any]],
    features_by_timestamp: dict[str, dict[str, Any]],
    pivots: list[dict[str, Any]],
    zones: list[dict[str, Any]],
    vwap_by_timestamp: dict[str, dict[str, Any]],
    anchored_vwap_by_timestamp: dict[str, list[dict[str, Any]]],
    volatility_by_timestamp: dict[str, dict[str, Any]],
    range_by_timestamp: dict[str, dict[str, Any]],
    regime_by_timestamp: dict[str, dict[str, Any]],
    source_dataset_ids: list[str],
    lineage_id: str,
) -> list[MarketStatePoint]:
    points: list[MarketStatePoint] = []
    for index, candle in enumerate(candles):
        timestamp = str(candle["timestamp"])
        close = float(candle["close"])
        feature_row = features_by_timestamp.get(timestamp)
        vwap_row = vwap_by_timestamp.get(timestamp)
        anchored_rows = anchored_vwap_by_timestamp.get(timestamp, [])
        volatility_row = volatility_by_timestamp.get(timestamp)
        range_row = range_by_timestamp.get(timestamp)
        regime_row = regime_by_timestamp.get(timestamp)

        component_available_at: dict[str, str] = {}
        _availability("candle", candle, component_available_at)
        _availability("basic_features", feature_row, component_available_at)
        _availability("vwap_state", vwap_row, component_available_at)
        _availability("volatility_state", volatility_row, component_available_at)
        _availability("range_state", range_row, component_available_at)
        _availability("regime_state", regime_row, component_available_at)
        if anchored_rows:
            anchored_available = [row.get("available_at") for row in anchored_rows if isinstance(row.get("available_at"), str)]
            if anchored_available:
                component_available_at["anchored_vwap_state"] = max(anchored_available)

        current_available_at = _max_available(component_available_at) or str(candle.get("available_at", ""))
        selected_pivots = nearest_pivots(pivots, close, current_available_at, limit=3)
        selected_zones = nearest_zones(zones, close, current_available_at, limit=3)
        if selected_pivots:
            pivot_available = [row.get("available_at") or row.get("usable_from") for row in selected_pivots]
            pivot_available = [value for value in pivot_available if isinstance(value, str)]
            if pivot_available:
                component_available_at["nearest_pivots"] = max(pivot_available)
        if selected_zones:
            zone_available = [row.get("available_at") or row.get("usable_from") for row in selected_zones]
            zone_available = [value for value in zone_available if isinstance(value, str)]
            if zone_available:
                component_available_at["nearest_zones"] = max(zone_available)

        current_available_at = _max_available(component_available_at) or current_available_at
        components = {
            "candle": candle,
            "basic_features": feature_row,
            "nearest_pivots": selected_pivots,
            "nearest_zones": selected_zones,
            "vwap_state": vwap_row,
            "anchored_vwap_state": anchored_rows,
            "volatility_state": volatility_row,
            "range_state": range_row,
            "regime_state": regime_row,
        }
        data_quality = assess_data_quality(components)
        points.append(
            MarketStatePoint(
                pair=pair,
                timeframe=timeframe,
                timestamp=timestamp,
                available_at=current_available_at,
                market_state_id=f"market_state_{pair.lower().replace('/', '_')}_{timeframe}_{index}",
                candle=_compact(candle, ["timestamp", "available_at", "open", "high", "low", "close", "volume", "trades"])
                or {},
                basic_features=(feature_row or {}).get("features") if feature_row else None,
                nearest_pivots=selected_pivots,
                nearest_zones=selected_zones,
                vwap_state=_compact(vwap_row, ["timestamp", "available_at", "vwap", "cumulative_volume"]),
                anchored_vwap_state=[
                    _compact(row, ["timestamp", "available_at", "anchor_id", "anchor_type", "anchored_vwap"]) or {}
                    for row in anchored_rows
                    if row.get("available_at", "") <= current_available_at
                ],
                volatility_state=_compact(
                    volatility_row,
                    ["timestamp", "available_at", "true_range", "atr_3", "atr_6", "realized_volatility_3", "realized_volatility_6"],
                ),
                range_state=_compact(
                    range_row,
                    [
                        "timestamp",
                        "available_at",
                        "rolling_high_6",
                        "rolling_low_6",
                        "rolling_range_6",
                        "range_width_pct",
                        "compression_score",
                        "expansion_score",
                        "range_state",
                    ],
                ),
                regime_state=_compact(
                    regime_row,
                    [
                        "timestamp",
                        "available_at",
                        "regime_id",
                        "regime_state",
                        "trend_score",
                        "range_score",
                        "volatility_score",
                        "confidence_score",
                        "direction_score",
                    ],
                ),
                data_quality=data_quality,
                component_available_at=component_available_at,
                source_dataset_ids=source_dataset_ids,
                source="lot7_market_state_engine",
                lineage_id=lineage_id,
                quality_flag="valid" if data_quality["status"] != "invalid" else "invalid",
                validation_status="validated_lot7",
                used_for_decision=False,
            )
        )
    return points
