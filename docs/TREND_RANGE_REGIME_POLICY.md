# Trend / Range Regime Policy — Lot 6

The V1 classifier uses simple deterministic components:

```text
direction_score
trend_score
range_score
compression_score
expansion_score
volatility_score
confidence_score
```

`direction_score` uses a 3-candle lookback. Early rows with insufficient history are `unknown`.

Classification priority:

```text
insufficient data -> unknown
high expansion + high volatility -> volatile
high expansion -> expanding
high compression -> compressed
weak direction + high range_score -> range
positive direction -> trend_up
negative direction -> trend_down
otherwise -> mixed
```

This is not a strategy and not a trading signal.
