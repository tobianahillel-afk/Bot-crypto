# Lot 38 — Order Book L2 Snapshot Engine Implementation Report

## Status

`EVIDENCE_PENDING_EXACT_SOURCE_HEAD`

This report documents the implementation candidate only. It is not final certification and does not authorize Lot 39.

## Authorized base

- gate merge: `2120aab94d54fde6e9ad36022499b1f9f284c3f6`
- gate checksum: `29fe4a5fd14b3bce95e3016fce67e10f94edcca1c2aad60c9fda382f3eb9d6a0`
- owner: `MicrostructureDomain`
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`

## Implemented candidate

The candidate adds:

- versioned Lot 38 configuration;
- strict schemas for raw snapshot, canonical snapshot, book health, state and audit;
- immutable dataclasses using `Decimal` for all level values;
- explicit Lot37-fixture → `OrderBookSnapshotRawV1` mapping;
- exact duplicate-price aggregation;
- canonical bid/ask sorting;
- crossed/explicit-locked validation;
- configured published-depth capping with source/normalized depth preservation;
- deterministic sequence anchor, snapshot checksum and health checksum;
- fail-closed state/audit safety maps;
- atomic persistence of four artifacts;
- deterministic replay validator;
- AST-based no-connectivity validation;
- behavioral, boundary and mutation-oriented tests.

## Explicitly not implemented

- network or exchange connectivity;
- live data ingestion;
- delta application or sequence reconstruction;
- gap repair/resynchronization;
- Lot40 desynchronization engine;
- spread/depth/imbalance feature engine;
- order flow, aggressor classification or CVD;
- liquidity inference, participant intent or game theory;
- forecast, signal, risk approval, routing, trading or execution.

## Reference evidence target

For the unchanged Lot37 L2 fixture with published depth 2, the expected reference state is:

```text
records_processed=1
source_levels=6
normalized_levels=6
duplicate_levels_aggregated=0
published_levels=4
source_bid_depth=3
source_ask_depth=3
published_bid_depth=2
published_ask_depth=2
venue_state=OPEN
health_status=HEALTHY
crossed=false
latency_measurement_status=NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY
```

## Quality evidence

Not frozen yet. Required before promotion:

```text
line_coverage >= 95%
branch_coverage >= 90%
mutation_score >= 80%
anti_flake_repetitions >= 3
full_regression = PASS
institutional_gates = PASS
no_connectivity = PASS
```

The final report must replace this section with the exact certified source head, workflow runs/digests, generated artifact checksums and measured scores. No threshold reduction or mutation exclusion may be used to manufacture PASS.

## Safety target

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

## Promotion rule

The implementation is not mergeable until a single exact source head passes all applicable CI, the generated evidence is frozen against that head, the frozen evidence is independently revalidated with zero subsequent production drift, and no review finding remains unresolved. Lot 39 stays `PLANNED_LOCKED` throughout this process.
