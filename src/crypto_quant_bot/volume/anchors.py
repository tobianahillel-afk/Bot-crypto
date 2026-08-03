from uuid import uuid4

from crypto_quant_bot.contracts.pivots import PivotPoint
from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.contracts.vwap import AnchorPoint, AnchoredVWAPPoint
from crypto_quant_bot.volume.vwap import typical_price

ALLOWED_ANCHOR_TYPES = {"session_start", "pivot_high", "pivot_low"}


def _session_anchor(candles: list[AggregatedCandle], *, source: str, lineage: str) -> AnchorPoint | None:
    if not candles:
        return None
    first = candles[0]
    return AnchorPoint(
        pair=first.pair,
        timeframe=first.target_timeframe,
        anchor_id=f"session_start_{first.target_timeframe}",
        anchor_type="session_start",
        anchor_time=first.timestamp,
        selected_at=first.timestamp,
        usable_from=first.timestamp,
        selection_rule=f"first_{first.target_timeframe}_candle",
        source_object_id=f"{first.target_timeframe}_{first.timestamp}",
        created_at=first.timestamp,
        available_at=first.timestamp,
        source=source,
        lineage_id=lineage,
        quality_flag="valid",
        validation_status="validated_lot4",
        used_for_decision=False,
    )


def _first_pivot_anchor(pivots: list[PivotPoint], side: str, timeframe: str, *, source: str, lineage: str) -> AnchorPoint | None:
    candidates = sorted([pivot for pivot in pivots if pivot.side == side and pivot.timeframe == timeframe], key=lambda p: (p.usable_from, p.pivot_time, p.pivot_id))
    if not candidates:
        return None
    pivot = candidates[0]
    anchor_type = "pivot_high" if side == "high" else "pivot_low"
    return AnchorPoint(
        pair=pivot.pair,
        timeframe=pivot.timeframe,
        anchor_id=f"first_confirmed_{anchor_type}_{timeframe}",
        anchor_type=anchor_type,
        anchor_time=pivot.pivot_time,
        selected_at=pivot.usable_from,
        usable_from=pivot.usable_from,
        selection_rule=f"first_confirmed_{side}_fractal_pivot_{timeframe}",
        source_object_id=pivot.pivot_id,
        created_at=pivot.usable_from,
        available_at=pivot.usable_from,
        source=source,
        lineage_id=lineage,
        quality_flag="valid",
        validation_status="validated_lot4",
        used_for_decision=False,
    )


def build_anchor_points(
    candles_by_timeframe: dict[str, list[AggregatedCandle]],
    pivots_by_timeframe: dict[str, list[PivotPoint]],
    *,
    source: str = "lot4_anchor_engine",
    lineage_id: str | None = None,
) -> dict[str, list[AnchorPoint]]:
    lineage = lineage_id or str(uuid4())
    anchors_by_timeframe: dict[str, list[AnchorPoint]] = {}
    for timeframe, candles in candles_by_timeframe.items():
        anchors: list[AnchorPoint] = []
        session = _session_anchor(candles, source=source, lineage=lineage)
        if session is not None:
            anchors.append(session)
        if timeframe == "5m":
            high = _first_pivot_anchor(pivots_by_timeframe.get(timeframe, []), "high", timeframe, source=source, lineage=lineage)
            low = _first_pivot_anchor(pivots_by_timeframe.get(timeframe, []), "low", timeframe, source=source, lineage=lineage)
            if high is not None:
                anchors.append(high)
            if low is not None:
                anchors.append(low)
        anchors_by_timeframe[timeframe] = anchors
    return anchors_by_timeframe


def compute_anchored_vwap(
    candles: list[AggregatedCandle],
    anchors: list[AnchorPoint],
    *,
    source_dataset_id: str,
    source: str = "lot4_anchored_vwap_engine",
    lineage_id: str | None = None,
) -> list[AnchoredVWAPPoint]:
    lineage = lineage_id or str(uuid4())
    rows: list[AnchoredVWAPPoint] = []
    for anchor in anchors:
        if anchor.anchor_type not in ALLOWED_ANCHOR_TYPES:
            raise ValueError(f"unsupported anchor_type: {anchor.anchor_type}")
        cumulative_price_volume = 0.0
        cumulative_volume = 0.0
        for candle in candles:
            if candle.timestamp < anchor.anchor_time:
                continue
            price_volume = typical_price(candle) * candle.volume
            cumulative_price_volume += price_volume
            cumulative_volume += candle.volume
            if candle.available_at < anchor.usable_from:
                continue
            anchored_vwap = None if cumulative_volume == 0 else cumulative_price_volume / cumulative_volume
            rows.append(
                AnchoredVWAPPoint(
                    pair=candle.pair,
                    timeframe=candle.target_timeframe,
                    anchor_id=anchor.anchor_id,
                    anchor_type=anchor.anchor_type,
                    anchor_time=anchor.anchor_time,
                    timestamp=candle.timestamp,
                    available_at=candle.available_at,
                    anchored_vwap=None if anchored_vwap is None else round(anchored_vwap, 8),
                    cumulative_price_volume=round(cumulative_price_volume, 8),
                    cumulative_volume=round(cumulative_volume, 8),
                    source_dataset_id=source_dataset_id,
                    source=source,
                    lineage_id=lineage,
                    quality_flag="valid",
                    validation_status="validated_lot4",
                    used_for_decision=False,
                )
            )
    return rows
