# Acceptance Criteria — Lot 3

Lot 3 is accepted only if:

- Lot 0 validation passes.
- Lot 1 validation passes.
- Lot 2 validation passes.
- The 180-candle pivot fixture exists.
- The fixture parses to exactly 180 valid 1m candles.
- Resampling produces exactly 36 candles at 5m and 12 candles at 15m.
- PivotPoint and PriceZone contracts exist.
- The fractal detector exists.
- At least 2 high and 2 low pivots are found on 5m.
- At least 1 high and 1 low pivot are found on 15m.
- Every pivot has confirmed_at and usable_from.
- Every pivot has usable_from >= pivot_time.
- Every pivot has used_for_decision=false.
- Every zone is support or resistance.
- Every zone satisfies lower_bound <= center_price <= upper_bound.
- Gold pivot and zone datasets are generated.
- Dataset catalog is updated.
- Reports are generated.
- No LONG/SHORT signal is generated.
- Decision Engine still returns WAIT.
- Risk Engine still blocks by default.
- trade_allowed remains false.
- live_execution remains DISABLED.
- leverage remains FORBIDDEN.
