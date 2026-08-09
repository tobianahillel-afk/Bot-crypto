# Lot 38 — V4 Implementation Entry Gate

## Decision

```text
gate_status=GO_LOT38_IMPLEMENTATION_ENTRY
base_commit=c7ff8eecafd5f34196e9383013e97548b1a0ba02
current_version=0.37.0
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
canonical_title=Order Book L2 Snapshot Engine
lot39_status=PLANNED_LOCKED
```

The independent Lot 37 post-merge audit is complete on the exact audited `main` commit above. Lot 38 may begin only inside the canonical offline L2 snapshot-normalization boundary. This gate does not implement the engine and does not unlock Lot 39.

## Canonical authority

The gate is bound to the immutable product-scope registry:

```text
path=data/audit/product_scope_roadmap_lot21.jsonl
line=39
blob_sha=84de51bda788a8d124fb7d344419c4a4b12030b5
lot_id=Lot 38
title=Order Book L2 Snapshot Engine
version_id=V4_MICROSTRUCTURE_LIQUIDITY
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
package_boundary=src/crypto_quant_bot/microstructure
```

The validator recomputes the Git blob SHA, parses line 39 directly, and checks the exact identity plus canonical input/output contract sets. The detailed V4 authority is `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`.

## Verified Lot 37 prerequisites

- audited release: `0.37.0`;
- Lot 37 post-merge audit merge: `c7ff8eecafd5f34196e9383013e97548b1a0ba02`;
- Lot 37 status: `IMPLEMENTED_VALIDATED_OFFLINE_SCOPE_CONTRACTS_ONLY`;
- implementation source head: `59b189e9980772245993a9212b6c8ad5e9a88a00`;
- frozen evidence head: `91c28f17acc2f66c906dddee96cbda369945f3ea`;
- implementation squash merge: `f1da136ff956e40915fab42ae21748a6f2b1ebca`;
- state checksum: `ea960217eb9a2159c4a99c56257a37c43869ffad0da86555fef24eb356e5f8e7`;
- audit checksum: `aa2df489e636860c119eb2ed54f7a5f03ede09838dfbd056dae0bb5a8a2a482f`;
- contract-registry checksum: `129140ffb7e812afd59d0174d318c5e3388d23bc49cc554168bde558bc0bf590`;
- capability-matrix checksum: `f7132fcfdab898af3f733b2715e0836d23e6284f8c0c1f3e7dd92ccf0070f1b4`;
- line coverage: `100.00%`;
- branch coverage: `100.00%`;
- mutation score: `80.26%`;
- anti-flake: `3` repetitions PASS;
- Lot 38 remains `PLANNED_LOCKED` in the audited Lot 37 capability matrix until this gate is merged.

## Offline L2 prerequisite

Lot 37 created the active offline input contract `MicrostructureOfflineL2InputV1` at `contracts/schemas/microstructure_offline_l2_input_v1.schema.json`. The test-only L2 availability fixture remains:

```text
fixture_only=true
canonical_contract=false
used_for_decision=false
```

The fixture is not `OrderBookSnapshotRawV1` and is not silently promoted into a Lot 38 canonical contract. Lot 38 implementation may define the canonical raw snapshot contract explicitly and map validated offline input into it. No live exchange fetch or network ingestion is authorized.

## Canonical Lot 38 contracts

Inputs:

- `RunContextV1`;
- `LineageEnvelopeV1`;
- `OrderBookSnapshotRawV1`.

Outputs:

- `OrderBookL2SnapshotEngineStateV1`;
- `OrderBookL2SnapshotEngineAuditV1`;
- `OrderBookSnapshotV1`;
- `BookHealthStateV1`.

## Authorized implementation scope

Lot 38 may only implement the offline L2 snapshot engine and directly required contracts/configuration:

1. define `OrderBookSnapshotRawV1` explicitly;
2. normalize an offline L2 snapshot into canonical bids and asks;
3. sort bids descending and asks ascending;
4. aggregate duplicate price levels deterministically;
5. reject negative quantities;
6. reject crossed books and require an explicit venue-locked state for a locked book;
7. cap published depth from versioned configuration while retaining source depth metadata;
8. bind a deterministic sequence anchor;
9. compute a reproducible snapshot checksum independent of raw level ordering where semantics are identical;
10. produce `BookHealthStateV1`, state and audit artifacts with lineage and reason codes;
11. persist artifacts atomically and remain deterministic under replay.

## Explicitly forbidden scope

This gate does not authorize Lot 39 or later capabilities. It forbids:

- external network access, live exchange data, real credentials and network ingestion;
- order-book delta application, gap repair, sequence reconstruction or resynchronization logic;
- the Lot 40 integrity/desynchronization engine beyond the basic Lot 38 snapshot validity checks;
- spread/depth/imbalance analytics as a derived analysis engine;
- liquidity walls, voids, zones, resilience or replenishment inference;
- aggressor classification, order flow, delta or CVD;
- participant-intent claims, hidden-liquidity inference or game-theory scenarios;
- forecasts, signals, risk approval, order routing, trading and execution.

## Quality gates

```text
line_coverage >= 95%
branch_coverage >= 90%
mutation_score >= 80%
anti_flake_repetitions >= 3
```

No threshold may be reduced, bypassed or satisfied through a permissive fallback.

## Safety boundary

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

Unknown, stale, incompatible, crossed or ambiguous input is fail-closed. A successful snapshot normalization is never a trade permission.

## Gate checksum

```text
4f82b04a98c542cf01d3047360f2beb54a1d808b4dd0c7160388f454c4506673
```

## Promotion rule

This gate PR must remain governance-only with no `src/` change. Lot 38 implementation starts only after this gate is green, reviewed, merged, and the exact merge commit is used as the implementation base. Lot 39 remains `PLANNED_LOCKED` throughout Lot 38 implementation and requires its own gate after an independent Lot 38 post-merge audit.
