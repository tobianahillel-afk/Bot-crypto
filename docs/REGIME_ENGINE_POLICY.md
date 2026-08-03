# Regime Engine Policy — Lot 6

The Market Regime Engine V1 creates deterministic regime analysis objects from already validated datasets. It does not trade, does not generate LONG/SHORT signals, and does not create targets, labels or future_* fields.

Allowed states:

```text
unknown
trend_up
trend_down
range
compressed
expanding
volatile
mixed
```

All outputs keep `used_for_decision=false` in Lot 6.

Anti-look-ahead rule: every RegimePoint uses only candle, VWAP, volatility and range-state rows available at the same timestamp or earlier. `available_at` is inherited from the current candle.
