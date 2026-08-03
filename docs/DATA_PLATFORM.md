# Data Platform — Lot 1

The data platform is the first real data foundation of Crypto Quant Bot V3.1-Ops.

It introduces five layers:

```text
data/raw/      = original immutable input data
data/bronze/   = minimally parsed and normalized data
data/silver/   = aligned, quality-controlled and resampled data
data/gold/     = feature-ready datasets for later modules
data/audit/    = catalog, checksums and quality reports
```

## Raw immutable rule

`data/raw/` is immutable. Raw input data is never edited in place. Any correction, parsing,
normalization or repair must produce a new artifact in `bronze/`, `silver/` or `gold/` with a
new `data_version` and lineage.

## Lot 1 includes

- local BTC/EUR OHLCVT fixture;
- OHLCVT candle contract;
- dataset metadata contract;
- data quality report contract;
- CSV parser for OHLCVT data;
- checksum generation;
- dataset catalog skeleton;
- quality validation for monotonic timestamps, duplicates, negative volume and OHLC consistency;
- Lot 1 validation script and tests.

## Lot 1 excludes

- real Kraken download requirement;
- WebSocket;
- strategy;
- backtest;
- paper trading;
- ML;
- AI/news;
- live trading.

The bot remains defensive: `trade_allowed = false`, default decision is `WAIT`, and the risk
engine blocks by default.
