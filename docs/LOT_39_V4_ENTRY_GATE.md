# Lot 39 — V4 Implementation Entry Gate

## Decision

```text
gate_status=GO_LOT39_IMPLEMENTATION_ENTRY
base_commit=5d0695f248b1bd4e6af5621f8a3d448cc0430050
current_version=0.38.0
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
canonical_title=Order Book Delta & Sequence Reconstructor
lot40_status=PLANNED_LOCKED
```

The independent Lot 38 post-merge audit is complete on the exact audited `main` commit above. Lot 39 may begin only inside the canonical offline snapshot+delta sequence-reconstruction boundary. This gate does not implement the reconstructor, does not define `OrderBookDeltaV1` yet, and does not unlock Lot 40.

## Canonical authority

The gate is bound to the immutable product-scope registry:

```text
path=data/audit/product_scope_roadmap_lot21.jsonl
line=40
blob_sha=84de51bda788a8d124fb7d344419c4a4b12030b5
lot_id=Lot 39
title=Order Book Delta & Sequence Reconstructor
version_id=V4_MICROSTRUCTURE_LIQUIDITY
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
package_boundary=src/crypto_quant_bot/microstructure
```

The validator recomputes the Git blob SHA, parses line 40 directly, and checks the exact identity plus canonical input/output contract strings. The detailed normative authority is `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`.

## Verified Lot 38 prerequisites

- audited release: `0.38.0`;
- Lot 38 post-merge audit merge: `5d0695f248b1bd4e6af5621f8a3d448cc0430050`;
- Lot 38 status: `IMPLEMENTED_VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY`;
- implementation source head: `b74bea4329d5e5cb7cf2452058b684ea5a5df13c`;
- frozen evidence head: `ef197437d13012644e48a9044cf0883bd17700fb`;
- implementation squash merge: `e4b44d27886ade86f9d1d05d480b89010b03700d`;
- state checksum: `7610fc6ea73e49075a1b8611f8344c7b9c8fcf8ab02f55612d914eeac0ccda9b`;
- audit checksum: `0290637591e1a8c4cd7a9975868932b65afa28fb75d6843340dbeea67a682d20`;
- snapshot checksum: `0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16`;
- book-health checksum: `58b56f7cf21aa74dd67620b8dd6e19cad11b77412cdcc3103b6d60bd15703837`;
- config checksum: `60899c1393e111315395dd0e149f3a468972e9e99ca5a1322b8a97ec786497db`;
- line coverage: `99.61%`;
- branch coverage: `99.35%`;
- mutation score: `81.66%`;
- anti-flake: `3` repetitions PASS;
- reference book health: `HEALTHY`;
- reference sequence present: `true`;
- Lot 39 remains `PLANNED_LOCKED` in the audited Lot 38 lifecycle until this gate is merged.

The complete prerequisite evidence object is checked exactly. Any changed commit, checksum, quality result, lifecycle status, snapshot health or sequence prerequisite invalidates the gate.

## Canonical Lot 39 contracts

Inputs, reproduced exactly from canonical roadmap line 40:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`;
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`;
- `OrderBookSnapshotV1`;
- `OrderBookDeltaV1`.

Outputs:

- `OrderBookDeltaSequenceReconstructorStateV1`;
- `OrderBookDeltaSequenceReconstructorAuditV1`;
- `ReconstructedOrderBookV1`;
- `SequenceGapEventV1`.

`OrderBookSnapshotV1` already exists as a certified Lot 38 contract. `OrderBookDeltaV1` is intentionally still absent in this gate PR: defining that canonical contract is part of the implementation scope authorized only after the gate merges.

## Authorized implementation scope

Lot 39 may only implement the offline snapshot+delta sequence reconstructor and directly required contracts/configuration:

1. define `OrderBookDeltaV1` explicitly;
2. start from a validated `OrderBookSnapshotV1`;
3. apply deltas only when `sequence_id` and `prev_sequence` satisfy the versioned venue sequence policy;
4. delete a level when quantity becomes exactly zero;
5. reject negative quantities;
6. detect gaps, duplicates, reordering and sequence ambiguity explicitly;
7. enter `RESYNC_REQUIRED` on a gap, ambiguous duplicate or checksum mismatch;
8. publish a reconstructed book only when `synchronization_state=SYNCED`;
9. emit `SequenceGapEventV1` with deterministic reason codes and lineage;
10. calculate reproducible reconstructed-book checksums;
11. replay exact snapshot+deltas deterministically;
12. persist state/audit/reconstructed-book/gap evidence atomically.

## Explicitly forbidden scope

This gate does not authorize Lot 40 or later capabilities. It forbids:

- external network access, live exchange data, real credentials and network ingestion;
- the Lot 40 Book Integrity / Desynchronization Detector as an independent engine;
- spread/depth/imbalance analytics;
- liquidity walls, voids, zones, resilience or replenishment inference;
- trade-aggressor classification, order flow, delta/CVD analysis;
- confidence/hidden-liquidity/cluster/stop-zone inference;
- sweep/fakeout/trap engines, derivatives context or game-theory aggregation;
- participant intent as fact;
- forecasts, signals, risk approval, order routing, trading and execution.

Lot 39 may detect the sequence-integrity conditions strictly necessary to fail closed and request resynchronization; it may not implement the broader Lot 40 integrity-analysis capability.

## Pre-implementation boundary

The gate validator requires all Lot 39 production files to remain absent, including the canonical `OrderBookDeltaV1` schema and the reconstructor source/model/runner/validator. The gate PR is governance-only. Production work starts from the exact gate merge commit only.

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

Unknown, stale, incompatible, out-of-sequence, ambiguous or unreconciled input is fail-closed. A successfully reconstructed book is never a signal or trade permission.

## Gate checksum

```text
250c67574a8add382915c1b8f0b104f801bd91757c829c3d7d336f8e2e22e0ab
```

## Promotion rule

This gate PR must remain governance-only with no Lot 39 production implementation. Lot 39 implementation starts only after this gate is green, reviewed, merged, and the exact merge commit is used as the implementation base. Lot 40 remains `PLANNED_LOCKED` throughout Lot 39 implementation and requires its own gate after an independent Lot 39 post-merge audit.
