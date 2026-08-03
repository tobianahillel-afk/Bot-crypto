# Volatility Engine Policy — Lot 5

Lot 5 computes realized volatility from historical returns only. For row `t`, the engine may only use candles with `available_at <= available_at(t)`. Early rows with insufficient rolling windows return `null`.

No trading, no strategy, no backtest, no target, no label, no `future_*` field and no execution module are introduced in this lot.
