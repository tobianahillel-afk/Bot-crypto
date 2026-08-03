# Pivot Engine Policy — Lot 3

The Lot 3 Pivot Engine creates analytical pivot objects only. It does not create trading signals and it cannot authorize execution.

## Fractal pivot definition

A pivot high is a candle whose high is strictly greater than the highs of the `left_window` candles before it and strictly greater than the highs of the `right_window` candles after it.

A pivot low is a candle whose low is strictly lower than the lows of the `left_window` candles before it and strictly lower than the lows of the `right_window` candles after it.

Default parameters:

```text
left_window = 2
right_window = 2
```

No pivot is emitted when the left or right windows are incomplete.

## Strength score

Lot 3 uses a deterministic simple score:

```text
strength_score = mean(reaction_component, volume_component, timeframe_component)
```

The score is clipped to `[0, 1]`. It is a research-quality analytical score, not a trading signal.

## Scope exclusions

Lot 3 does not implement trading, strategy, backtesting, paper trading, WebSocket, API calls, ML or AI/news.
