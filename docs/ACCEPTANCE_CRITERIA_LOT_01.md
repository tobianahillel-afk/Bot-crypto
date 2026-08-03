# Acceptance Criteria — Lot 1-bis

Lot 1-bis is a compliance correction for Lot 1 only. It does not start Lot 2.

## Required fixtures

The project must contain:

- `tests/fixtures/btc_eur_ohlcvt_sample.csv`
- `tests/fixtures/btc_eur_ohlcvt_invalid.csv`

The valid fixture must contain at least six valid OHLCVT candles. The invalid fixture must contain detectable data-quality errors such as negative volume, OHLC inconsistency, duplicate timestamp, or negative trades.

## Required scripts

The project must contain:

- `scripts/ingest_ohlcvt_fixture.py`
- `scripts/validate_lot1.py`

The ingestion script must read the official valid fixture, parse candles, validate quality, write a bronze dataset, update `data/audit/dataset_catalog.json`, generate `reports/lot_01_data_quality_report.md`, and never write new raw data.

## Required data writer

The project must contain:

- `src/crypto_quant_bot/data/data_writer.py`

It must expose `write_jsonl(...)`.

## Required validation behavior

`scripts/validate_lot1.py` must verify:

- both official fixtures exist;
- valid fixture contains at least six candles;
- valid fixture quality is `valid`;
- invalid fixture quality is `invalid` or `degraded`;
- ingestion script exists and runs;
- data writer exists;
- SHA256 checksums are 64 characters;
- bronze JSONL output is generated;
- dataset catalog is generated;
- data quality markdown report is generated;
- Decision Engine still returns `WAIT`;
- Risk Engine still blocks by default;
- `trade_allowed` remains `false`;
- `live_execution` remains `DISABLED`;
- `leverage` remains `FORBIDDEN`.

The script may print `LOT 1 VALIDATION: PASS` only if all checks pass.

## Forbidden scope

Lot 1-bis must not implement:

- Lot 2;
- multi-timeframes;
- trading features;
- backtesting;
- WebSocket;
- API calls;
- strategy;
- ML;
- paper trading;
- live execution.
