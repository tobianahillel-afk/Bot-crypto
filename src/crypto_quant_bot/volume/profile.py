from math import floor, sqrt
from statistics import mean
from uuid import uuid4

from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.contracts.volume_profile import VolumeProfileBin, VolumeProfileSummary


def _bin_index(price: float, bin_size: float) -> int:
    return floor(price / bin_size)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return sqrt(sum((value - avg) ** 2 for value in values) / len(values))


def build_volume_profile(
    candles: list[AggregatedCandle],
    *,
    profile_id: str,
    source_dataset_id: str,
    bin_size: float = 50.0,
    source: str = "lot4_volume_profile_engine",
    lineage_id: str | None = None,
) -> tuple[list[VolumeProfileBin], VolumeProfileSummary]:
    if bin_size <= 0:
        raise ValueError("bin_size must be positive")
    if not candles:
        summary = VolumeProfileSummary(
            profile_id=profile_id,
            bin_size=bin_size,
            source_dataset_id=source_dataset_id,
            source=source,
            lineage_id=lineage_id or str(uuid4()),
            quality_flag="invalid",
            validation_status="empty_lot4",
            used_for_decision=False,
        )
        return [], summary

    lineage = lineage_id or str(uuid4())
    bin_totals: dict[int, dict[str, float]] = {}
    for candle in candles:
        if candle.high == candle.low:
            indices = [_bin_index(candle.low, bin_size)]
        else:
            indices = list(range(_bin_index(candle.low, bin_size), _bin_index(candle.high, bin_size) + 1))
        if not indices:
            indices = [_bin_index(candle.close, bin_size)]
        volume_part = candle.volume / len(indices)
        trades_part = candle.trades / len(indices)
        for index in indices:
            current = bin_totals.setdefault(index, {"volume": 0.0, "trades": 0.0})
            current["volume"] += volume_part
            current["trades"] += trades_part

    total_volume = sum(item["volume"] for item in bin_totals.values())
    total_trades = sum(item["trades"] for item in bin_totals.values())
    if total_volume <= 0:
        shares = {index: 0.0 for index in bin_totals}
    else:
        shares = {index: item["volume"] / total_volume for index, item in bin_totals.items()}
    poc_index = max(bin_totals, key=lambda index: (bin_totals[index]["volume"], -index))
    share_values = list(shares.values())
    share_mean = mean(share_values) if share_values else 0.0
    share_std = _std(share_values)
    hvn_threshold = share_mean + share_std
    lvn_threshold = share_mean - share_std

    bins: list[VolumeProfileBin] = []
    for index in sorted(bin_totals):
        lower = index * bin_size
        upper = (index + 1) * bin_size
        center = lower + bin_size / 2.0
        volume_share = shares[index]
        is_hvn = share_std > 0 and volume_share >= hvn_threshold
        is_lvn = share_std > 0 and volume_share <= lvn_threshold
        bins.append(
            VolumeProfileBin(
                pair=candles[0].pair,
                timeframe=candles[0].target_timeframe,
                profile_id=profile_id,
                bin_id=f"{profile_id}_bin_{index}",
                lower_bound=round(lower, 8),
                upper_bound=round(upper, 8),
                center_price=round(center, 8),
                volume=round(bin_totals[index]["volume"], 8),
                trade_count=round(bin_totals[index]["trades"], 8),
                volume_share=round(volume_share, 12),
                is_poc=index == poc_index,
                is_hvn=is_hvn,
                is_lvn=is_lvn,
                source_dataset_id=source_dataset_id,
                created_at=candles[-1].available_at,
                available_at=candles[-1].available_at,
                source=source,
                lineage_id=lineage,
                quality_flag="valid",
                validation_status="validated_lot4",
                used_for_decision=False,
            )
        )

    summary = VolumeProfileSummary(
        pair=candles[0].pair,
        timeframe=candles[0].target_timeframe,
        profile_id=profile_id,
        start_timestamp=candles[0].timestamp,
        end_timestamp=candles[-1].available_at,
        created_at=candles[-1].available_at,
        available_at=candles[-1].available_at,
        bin_size=bin_size,
        total_volume=round(total_volume, 8),
        total_trades=round(total_trades, 8),
        poc_price=round(poc_index * bin_size + bin_size / 2.0, 8),
        poc_volume=round(bin_totals[poc_index]["volume"], 8),
        hvn_prices=[item.center_price for item in bins if item.is_hvn],
        lvn_prices=[item.center_price for item in bins if item.is_lvn],
        bin_count=len(bins),
        source_dataset_id=source_dataset_id,
        source=source,
        lineage_id=lineage,
        quality_flag="valid",
        validation_status="validated_lot4",
        used_for_decision=False,
    )
    return bins, summary
