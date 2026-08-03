from datetime import datetime, timedelta, timezone
from uuid import uuid4

from crypto_quant_bot.contracts.ohlcvt import OHLCVTCandle
from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.timeframes.timeframe import timeframe_to_minutes


def parse_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resample_ohlcvt(
    candles: list[OHLCVTCandle],
    *,
    target_timeframe: str,
    source_timeframe: str = "1m",
    source: str = "lot2_resampler",
    lineage_id: str | None = None,
) -> list[AggregatedCandle]:
    if not candles:
        return []
    source_minutes = timeframe_to_minutes(source_timeframe)
    target_minutes = timeframe_to_minutes(target_timeframe)
    if target_minutes % source_minutes != 0:
        raise ValueError("target timeframe must be a multiple of source timeframe")
    bucket_size = target_minutes // source_minutes
    if len(candles) % bucket_size != 0:
        raise ValueError("input candles must form complete buckets")
    lineage = lineage_id or str(uuid4())
    aggregated: list[AggregatedCandle] = []
    for start_index in range(0, len(candles), bucket_size):
        bucket = candles[start_index : start_index + bucket_size]
        if len(bucket) != bucket_size:
            raise ValueError("incomplete bucket")
        timestamp_dt = parse_utc(bucket[0].timestamp)
        closed_at_dt = timestamp_dt + timedelta(minutes=target_minutes)
        aggregated.append(
            AggregatedCandle(
                pair=bucket[0].pair,
                source_timeframe=source_timeframe,
                target_timeframe=target_timeframe,
                timestamp=format_utc(timestamp_dt),
                closed_at=format_utc(closed_at_dt),
                available_at=format_utc(closed_at_dt),
                open=bucket[0].open,
                high=max(c.high for c in bucket),
                low=min(c.low for c in bucket),
                close=bucket[-1].close,
                volume=sum(c.volume for c in bucket),
                trades=sum(c.trades for c in bucket),
                input_count=len(bucket),
                source=source,
                lineage_id=lineage,
                quality_flag="valid",
                validation_status="validated_lot2",
                used_for_decision=False,
            )
        )
    return aggregated
