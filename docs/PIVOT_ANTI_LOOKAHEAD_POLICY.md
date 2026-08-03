# Pivot Anti-Lookahead Policy — Lot 3

A fractal pivot requires future candles to be confirmed. Therefore, the pivot cannot be used at `pivot_time`.

For a pivot at index `i` with `right_window = 2`:

```text
confirmed_at = available_at of candle i + 2
usable_from  = confirmed_at
```

The pivot may be displayed in historical analysis after it is confirmed, but it must never be available to any live-like process before `usable_from`.

Lot 3 enforces:

```text
usable_from = confirmed_at
confirmed_at = available_at of the candle located right_window after the pivot candle
used_for_decision = false
```

This lot creates analytical objects only. The Decision Engine remains WAIT and the Risk Engine blocks by default.
