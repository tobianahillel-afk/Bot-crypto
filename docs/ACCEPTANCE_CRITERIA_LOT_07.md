# Acceptance Criteria — Lot 7

Lot 7 is accepted only if:

- `contracts/market_state.py` exists;
- `src/crypto_quant_bot/market_state/` exists;
- `scripts/build_lot7_market_state.py` exists;
- `scripts/validate_lot7.py` exists;
- 5m market state dataset has 36 rows;
- 15m market state dataset has 12 rows;
- every row contains candle, volatility_state, range_state and regime_state;
- nearest pivots/zones are lists of at most 3 items;
- no pivot/zone is used before `usable_from`;
- MarketStatePoint `available_at` respects component availability;
- `used_for_decision = false`;
- no `future_*`, `target`, `label`, `LONG` or `SHORT` is generated;
- previous validations still pass;
- defensive invariants stay unchanged.
