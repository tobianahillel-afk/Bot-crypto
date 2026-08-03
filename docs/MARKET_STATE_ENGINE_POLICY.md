# Market State Engine Policy

Lot 7 introduces MarketStatePoint objects that aggregate already validated analysis objects from Lots 2 to 6.

A MarketStatePoint is not a signal, not a strategy and not a trading instruction. It is an auditable snapshot of what the system knew at a given timestamp and timeframe.

Inputs:
- candles and basic features;
- pivots and support/resistance zones;
- VWAP and Anchored VWAP;
- volatility and range state;
- market regime.

The engine writes one market state per candle for each supported timeframe.

Lot 7 keeps `used_for_decision = false` for every generated object.
