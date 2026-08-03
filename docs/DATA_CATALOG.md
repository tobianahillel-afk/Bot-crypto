# Data Catalog

The catalog is stored at:

```text
data/audit/dataset_catalog.json
```

It contains a JSON list of `DatasetMetadata` objects.

The catalog is not a trading signal. It is an audit and reproducibility tool. Later lots will use
it to know exactly which dataset version, checksum, schema and quality flag were active during a
backtest, a paper trading run or a decision replay.

Lot 1 only registers the local BTC/EUR OHLCVT fixture and any bronze artifact generated from it.
