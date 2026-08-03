# Market State Anti-Lookahead Policy

The Market State Engine must never use future information.

Rules:
- `available_at` of the MarketStatePoint is the maximum `available_at` of the components actually used.
- a component with an `available_at` greater than the final MarketStatePoint `available_at` is invalid.
- pivots and zones can only be used when `usable_from <= current available_at`.
- missing optional components are represented by `null` or an empty list.
- Market State datasets must not contain `future_*`, `target`, `label`, `LONG` or `SHORT` values.

The Market State Engine is an analysis layer only.
