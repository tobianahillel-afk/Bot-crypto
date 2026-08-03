# Lot 5 Volatility Report

Input candles 1m: 180

5m candles: 36

15m candles: 12

5m volatility points: 36

15m volatility points: 12

Features: realized_volatility_3, realized_volatility_6, true_range, atr_3, atr_6, hl_range, oc_range, close_to_close_abs_return.

Anti-look-ahead: each point uses only candles available at or before its own available_at.

No trading, no strategy, no backtest, no WebSocket, no API.
