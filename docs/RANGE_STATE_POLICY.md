# Range State Policy — Lot 5

Rolling range features use the last 6 candles available at each row. Compression and expansion are simple percentile-rank proxies. If both compression and expansion thresholds are reached, `expanding` has priority.

Allowed states: `unknown`, `compressed`, `normal`, `expanding`.
