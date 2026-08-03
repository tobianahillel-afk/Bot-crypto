from typing import Any

from crypto_quant_bot.contracts.regime import RegimePoint
from crypto_quant_bot.regime.confidence import confidence_score
from crypto_quant_bot.regime.trend import compute_direction_scores

ALLOWED_REGIMES = {"unknown", "trend_up", "trend_down", "range", "compressed", "expanding", "volatile", "mixed"}


def clamp01(value: float | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def trend_score_from_direction(direction_score: float | None) -> float | None:
    if direction_score is None:
        return None
    return clamp01(abs(direction_score))


def range_score_from_components(direction_score: float | None, expansion_score: float | None, range_width_pct: float | None) -> float | None:
    if direction_score is None or expansion_score is None or range_width_pct is None:
        return None
    raw = (1.0 - abs(float(direction_score))) * (1.0 - float(expansion_score))
    return round(max(0.0, min(1.0, raw)), 12)


def volatility_score_from_row(volatility_row: dict[str, Any]) -> float | None:
    value = volatility_row.get("volatility_percentile_lookback")
    if value is None:
        return None
    return clamp01(float(value))


def classify_state(
    *,
    direction_score: float | None,
    trend_score: float | None,
    range_score: float | None,
    compression_score: float | None,
    expansion_score: float | None,
    volatility_score: float | None,
    trend_up_threshold: float,
    trend_down_threshold: float,
    range_score_threshold: float,
    compression_threshold: float,
    expansion_threshold: float,
    volatility_high_threshold: float,
) -> str:
    if direction_score is None or compression_score is None or expansion_score is None:
        return "unknown"
    if expansion_score >= expansion_threshold and volatility_score is not None and volatility_score >= volatility_high_threshold:
        return "volatile"
    if expansion_score >= expansion_threshold:
        return "expanding"
    if compression_score >= compression_threshold:
        return "compressed"
    if range_score is not None and abs(direction_score) < abs(trend_up_threshold) and range_score >= range_score_threshold:
        return "range"
    if direction_score >= trend_up_threshold:
        return "trend_up"
    if direction_score <= trend_down_threshold:
        return "trend_down"
    return "mixed"


def classify_regime_points(
    candles: list[dict[str, Any]],
    volatility_rows: list[dict[str, Any]],
    range_rows: list[dict[str, Any]],
    vwap_rows: list[dict[str, Any]],
    *,
    config: dict[str, Any],
    timeframe: str,
    source_dataset_ids: list[str],
    lineage_id: str,
) -> list[RegimePoint]:
    trend_window = int(config.get("trend_window", 3))
    direction_scores = compute_direction_scores(candles, trend_window)
    vwap_by_timestamp = {row.get("timestamp"): row for row in vwap_rows}
    points: list[RegimePoint] = []
    for index, candle in enumerate(candles):
        volatility_row = volatility_rows[index]
        range_row = range_rows[index]
        direction_score = direction_scores[index]
        trend_score = trend_score_from_direction(direction_score)
        compression_score = clamp01(range_row.get("compression_score"))
        expansion_score = clamp01(range_row.get("expansion_score"))
        volatility_score = volatility_score_from_row(volatility_row)
        range_width_pct = range_row.get("range_width_pct")
        range_score = range_score_from_components(direction_score, expansion_score, range_width_pct)
        vwap_row = vwap_by_timestamp.get(candle.get("timestamp"), {})
        vwap = vwap_row.get("vwap")
        close = float(candle["close"])
        close_vs_vwap = None if vwap is None else round((close - float(vwap)) / close, 12)
        confidence = confidence_score([trend_score, range_score, compression_score, expansion_score, volatility_score])
        regime_state = classify_state(
            direction_score=direction_score,
            trend_score=trend_score,
            range_score=range_score,
            compression_score=compression_score,
            expansion_score=expansion_score,
            volatility_score=volatility_score,
            trend_up_threshold=float(config.get("trend_up_threshold", 0.35)),
            trend_down_threshold=float(config.get("trend_down_threshold", -0.35)),
            range_score_threshold=float(config.get("range_score_threshold", 0.60)),
            compression_threshold=float(config.get("compression_threshold", 0.70)),
            expansion_threshold=float(config.get("expansion_threshold", 0.70)),
            volatility_high_threshold=float(config.get("volatility_high_threshold", 0.70)),
        )
        components = {
            "direction_score": direction_score,
            "range_state_lot5": range_row.get("range_state"),
            "range_width_pct": range_width_pct,
            "close_vs_vwap": close_vs_vwap,
            "trend_window": trend_window,
        }
        points.append(
            RegimePoint(
                pair=candle.get("pair", "BTC/EUR"),
                timeframe=timeframe,
                timestamp=candle["timestamp"],
                available_at=candle["available_at"],
                regime_id=f"regime_{candle.get('pair', 'BTC_EUR').replace('/', '_').lower()}_{timeframe}_{index}",
                regime_state=regime_state,
                trend_score=trend_score,
                range_score=range_score,
                compression_score=compression_score,
                expansion_score=expansion_score,
                volatility_score=volatility_score,
                direction_score=direction_score,
                confidence_score=confidence,
                components=components,
                source_dataset_ids=source_dataset_ids,
                source="lot6_regime_engine",
                lineage_id=lineage_id,
                quality_flag="valid",
                validation_status="validated_lot6",
                used_for_decision=False,
            )
        )
    return points
