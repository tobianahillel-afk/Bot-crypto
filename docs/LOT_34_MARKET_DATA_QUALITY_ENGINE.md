# Lot 34 — Market Data Quality Engine

## Status and scope

- Owner: `MarketDataGovernanceDomain`
- Runtime: `DATA_GOVERNANCE_ONLY`
- Base authorization: `GO_LOT34_IMPLEMENTATION_ENTRY`
- Version before post-merge promotion: `0.33.0`
- Lot 35 remains locked until an independent post-merge audit.

Lot 34 is an offline, deterministic quality gate. It does not ingest network data and it does not create market-state, forecast, signal, risk, routing, trading or execution capabilities.

## Inputs

- versioned Lot 34 configuration;
- immutable raw quality records containing source/instrument/timeframe identity, event/availability time, sequence/revision, schema version, OHLC, volume and bid/ask;
- certified Lot 33 temporal state/audit and canonical-time collection lineage;
- exact Lot 34 entry gate.

Prices and volumes are parsed from explicit decimal strings with `Decimal`. Time comparisons use integer microseconds; no float timing conversion is permitted.

## Detection families

The engine evaluates exactly these anomaly families:

1. `MISSING_INTERVAL`;
2. `DUPLICATE`;
3. `OUT_OF_ORDER`;
4. `STALE_DATA`;
5. `INVALID_OHLC`;
6. `NEGATIVE_VOLUME`;
7. `IMPOSSIBLE_SPREAD`;
8. `SCHEMA_DRIFT`.

Every detected anomaly is typed, severity-labelled, linked to raw record IDs, bounded by an affected interval, marked `quarantined=true`, and has `correction_permitted=false`.

## Scoring

For each source/instrument/timeframe group the engine publishes integer basis-point scores:

- `coverage_bps`;
- `freshness_bps`;
- `completeness_bps`;
- `consistency_bps`;
- `quality_score_bps`.

The aggregate quality score is the integer average of the four component scores. Thresholds are versioned in configuration. No missing or malformed value is silently converted.

## Quality veto

`DataQualityVetoV1` is fail-closed:

- unknown quality -> `BLOCK_ANALYSIS_OR_TRADING`;
- any detected blocking anomaly -> `BLOCK_ANALYSIS_OR_TRADING`;
- score below the versioned threshold -> `BLOCK_ANALYSIS_OR_TRADING`;
- only known quality without anomaly and above threshold -> `ALLOW_ANALYSIS`.

`ALLOW_ANALYSIS` is not a trading permission. All trading/execution/sizing fields remain disabled/zero.

## Non-destructive quarantine

Raw inputs are immutable. Quarantine contains references to affected raw `record_id` values only. Lot 34 never edits, fills, rounds, replaces or deletes raw market data. Corrective or reconciled representations belong to later lots.

## Outputs

- `MarketDataQualityEngineStateV1`;
- `MarketDataQualityEngineAuditV1`;
- `DataQualityStateV1` collection;
- `DataAnomalyV1` collection;
- `DataQualityVetoV1`.

All state/audit outputs carry explicit versions, lineage, timestamps, reason codes, validation state, safety boundary and SHA-256 checksum.

## Determinism and persistence

The runner is `scripts/run_lot34_market_data_quality_engine.py`. Re-running the same code commit, configuration and upstream evidence must produce byte-identical output artifacts. Persistence uses the project atomic JSON writer.

## Validation

`python scripts/validate_lot34.py` independently recomputes state/audit checksums, verifies Lot 33 lineage, verifies standalone output collections, validates quarantine references and exact fail-closed safety fields.

`python scripts/validate_lot34_no_connectivity.py` rejects forbidden networking libraries in the Lot 34 production modules.

## Quality gates

- targeted line coverage >= 95%;
- targeted branch coverage >= 90%;
- mutation score >= 80%;
- anti-flake targeted suite x3;
- full repository regression;
- Ruff, mypy, Bandit, dependency audit, architecture, traceability and silent-numeric-coercion checks.

A separate post-merge audit is mandatory before any Lot 35 implementation gate can be created.
