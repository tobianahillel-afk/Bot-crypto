# Lot 38 — Order Book L2 Snapshot Engine

## Goal

Implement the first canonical V4 order-book representation as a deterministic, offline-only L2 snapshot normalizer. Lot 38 consumes validated representative L2-shaped input, maps it explicitly to `OrderBookSnapshotRawV1`, and publishes a canonical `OrderBookSnapshotV1` plus `BookHealthStateV1`.

This lot does **not** reconstruct deltas, repair sequence gaps, compute imbalance/order flow, infer liquidity intent, or produce any trading permission.

## Authorized base

Implementation starts from the exact merged Lot 38 gate commit:

`2120aab94d54fde6e9ad36022499b1f9f284c3f6`

Gate checksum:

`29fe4a5fd14b3bce95e3016fce67e10f94edcca1c2aad60c9fda382f3eb9d6a0`

Runtime:

`OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`

Owner:

`MicrostructureDomain`

## Inputs

Canonical roadmap inputs:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`;
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`;
- `OrderBookSnapshotRawV1`.

The Lot 37 L2 fixture remains explicitly noncanonical (`fixture_only=true`, `canonical_contract=false`, `used_for_decision=false`). Lot 38 performs an explicit mapping step into `OrderBookSnapshotRawV1`; it never mutates or silently promotes the fixture.

## Outputs

- `OrderBookL2SnapshotEngineStateV1`;
- `OrderBookL2SnapshotEngineAuditV1`;
- `OrderBookSnapshotV1`;
- `BookHealthStateV1`.

## Deterministic normalization

For each side of the book:

1. parse price and quantity from decimal text into `Decimal`;
2. require finite, strictly positive prices;
3. require finite, non-negative quantities;
4. aggregate all levels sharing the same price using exact `Decimal` addition;
5. sort bids strictly descending by price;
6. sort asks strictly ascending by price;
7. preserve raw/source depth and post-aggregation normalized depth;
8. cap the published depth from versioned configuration.

No float conversion is used in price/quantity arithmetic.

## Book-state rule

After full-side aggregation and sorting:

```text
best_bid > best_ask  -> reject (crossed)
best_bid = best_ask  -> allowed iff venue_state == LOCKED
best_bid < best_ask  -> allowed iff venue_state == OPEN
```

The `LOCKED` flag is therefore neither inferred permissively nor accepted for an actually open book. A crossed book is always rejected in Lot 38.

## Sequence anchor

Lot 38 does not reconstruct sequences. It binds the source snapshot to a deterministic sequence anchor computed from:

- source id;
- venue;
- instrument id;
- source sequence id;
- event time;
- receive time.

Changing the source sequence changes the anchor and the snapshot checksum. Applying deltas, detecting gaps, repairing sequence order or resynchronizing belongs to Lot 39+ and remains forbidden here.

## Snapshot checksum

The canonical snapshot checksum is calculated only after aggregation, ordering and depth capping. Therefore semantically identical raw snapshots with different input level ordering produce the same canonical snapshot and checksum.

## Book health

`BookHealthStateV1` records only Lot 38 validity information:

- `HEALTHY` for an open non-crossed book;
- `LOCKED` for an explicitly locked book with equal best prices;
- `crossed=false` for every publishable state;
- sequence presence;
- source, normalized and published depths;
- deterministic reason codes and checksum.

It does not implement the Lot 40 desynchronization/integrity engine.

## Metrics

Reference evidence records:

- one snapshot processed;
- source level count;
- normalized level count;
- duplicate levels aggregated;
- published level count;
- zero validation failures for the certified fixture.

Processing latency is intentionally `null` with status `NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY`. Lot 38 does not fabricate a zero-latency measurement.

## Safety

The state and audit must exactly retain:

```text
analysis_only=true
used_for_decision=false
external_connectivity_allowed=false
network_ingestion_allowed=false
real_credentials_allowed=false
market_event_publication_allowed=false
raw_data_mutation_allowed=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## Persistence and replay

The runner writes four JSON artifacts atomically:

- `data/audit/order_book_l2_snapshot_engine_lot38.json`;
- `data/audit/order_book_l2_snapshot_engine_audit_lot38.json`;
- `data/audit/order_book_snapshot_lot38.json`;
- `data/audit/book_health_state_lot38.json`.

The validator recomputes all four checksums, verifies their cross-links and rebuilds the state/audit using the certified code commit. Replay must match exactly.

## Explicit non-goals

Lot 38 does not implement:

- external/live exchange ingestion;
- delta application or sequence reconstruction;
- gap repair or resynchronization;
- spread/depth/imbalance analytics as a downstream feature engine;
- walls, voids, zones, resilience or replenishment;
- aggressor classification, order flow, delta or CVD;
- participant behavior or hidden-liquidity inference;
- forecasting, signals, risk, routing, paper/live trading or execution.

Lot 39 remains `PLANNED_LOCKED` until Lot 38 is implemented, merged and independently audited post-merge.
