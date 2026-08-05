# Lot 26 implementation guardrails

- Scope: descriptive multi-timeframe alignment only.
- Initial ordered edge: `timebar-5m -> timebar-15m`.
- Join: `ASOF_BACKWARD` on closed, complete, valid and available states.
- Outputs: component compatibility, weighted coverage, agreement, divergence, coherence and descriptive uncertainty.
- Forbidden: forecast, probability claim, alpha signal, TradeIntent, OrderIntent, routing, paper execution and live execution.
- Runtime invariants: `TradingDecision=WAIT`, `SystemDecision=BLOCK_TRADING`, `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.
