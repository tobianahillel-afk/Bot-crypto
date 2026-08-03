from uuid import uuid4

from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.contracts.vwap import VWAPPoint


def typical_price(candle: AggregatedCandle) -> float:
    return (candle.high + candle.low + candle.close) / 3.0


def compute_session_vwap(
    candles: list[AggregatedCandle],
    *,
    source_dataset_id: str,
    source: str = "lot4_vwap_engine",
    lineage_id: str | None = None,
) -> list[VWAPPoint]:
    lineage = lineage_id or str(uuid4())
    rows: list[VWAPPoint] = []
    cumulative_price_volume = 0.0
    cumulative_volume = 0.0
    for candle in candles:
        price_volume = typical_price(candle) * candle.volume
        cumulative_price_volume += price_volume
        cumulative_volume += candle.volume
        vwap = None if cumulative_volume == 0 else cumulative_price_volume / cumulative_volume
        rows.append(
            VWAPPoint(
                pair=candle.pair,
                timeframe=candle.target_timeframe,
                timestamp=candle.timestamp,
                available_at=candle.available_at,
                vwap=None if vwap is None else round(vwap, 8),
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
