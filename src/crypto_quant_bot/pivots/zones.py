from uuid import uuid4

from crypto_quant_bot.contracts.pivots import PivotPoint
from crypto_quant_bot.contracts.zones import PriceZone


def build_price_zones(
    pivots: list[PivotPoint],
    *,
    source_dataset_id: str,
    zone_width_pct: float = 0.001,
    source: str = "lot3_price_zone_engine",
    lineage_id: str | None = None,
) -> list[PriceZone]:
    if zone_width_pct <= 0:
        raise ValueError("zone_width_pct must be positive")
    lineage = lineage_id or str(uuid4())
    zones: list[PriceZone] = []
    for pivot in pivots:
        zone_type = "resistance" if pivot.side == "high" else "support"
        lower = pivot.price * (1.0 - zone_width_pct)
        upper = pivot.price * (1.0 + zone_width_pct)
        zones.append(
            PriceZone(
                pair=pivot.pair,
                timeframe=pivot.timeframe,
                zone_id=f"zone_{pivot.pivot_id}",
                zone_type=zone_type,
                lower_bound=round(lower, 8),
                upper_bound=round(upper, 8),
                center_price=pivot.price,
                source_pivot_ids=[pivot.pivot_id],
                touch_count=1,
                strength_score=pivot.strength_score,
                first_seen_at=pivot.pivot_time,
                last_confirmed_at=pivot.confirmed_at,
                usable_from=pivot.usable_from,
                available_at=pivot.usable_from,
                source_dataset_id=source_dataset_id,
                source=source,
                lineage_id=lineage,
                quality_flag="valid",
                validation_status="validated_lot3",
                used_for_decision=False,
            )
        )
    return zones
