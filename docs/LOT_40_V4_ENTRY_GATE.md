# Lot 40 — V4 Implementation Entry Gate

## Decision

```text
gate_status=GO_LOT40_IMPLEMENTATION_ENTRY
base_commit=5381a773a9d69036b38c57904b2f4a66ffb2f595
current_version=0.39.0
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
canonical_title=Book Integrity / Desynchronization Detector
lot41_status=PLANNED_LOCKED
```

The independent Lot 39 post-merge audit is complete on the exact audited `main` commit above. Lot 40 may begin only inside the canonical offline book-integrity and desynchronization boundary. This gate does not implement the detector, does not define its output schemas/configuration yet, and does not unlock Lot 41.

## Canonical authority

The gate is bound to the immutable product-scope registry:

```text
path=data/audit/product_scope_roadmap_lot21.jsonl
line=41
blob_sha=84de51bda788a8d124fb7d344419c4a4b12030b5
lot_id=Lot 40
title=Book Integrity / Desynchronization Detector
version_id=V4_MICROSTRUCTURE_LIQUIDITY
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
package_boundary=src/crypto_quant_bot/microstructure
```

The validator recomputes the Git blob SHA, parses line 41 directly, and checks the exact identity plus canonical input/output contract strings. The detailed normative authority is `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`.

## Verified Lot 39 prerequisites

- audited release: `0.39.0`;
- Lot 39 post-merge audit merge: `5381a773a9d69036b38c57904b2f4a66ffb2f595`;
- post-merge verdict: `GO_LOT39_POST_MERGE`;
- Lot 39 status: `IMPLEMENTED_VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY`;
- implementation source head: `203a2b2d3d69644bd67c0e583df9d0405941def6`;
- frozen evidence head: `b1bf9605fe20cacca76861e3fc6941ad38ea8f23`;
- final implementation PR head: `3dc7ec29bb1a4152017854581573c26465ee33a2`;
- implementation merge: `e2b787905e126a4f8ba19c933d39550ad338ac74`;
- state checksum: `d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0`;
- audit checksum: `1e29d0b8695a1b8825e1fc91728a6254ad93c689e1f961cfa424e6d5fed8ed41`;
- reconstructed-book checksum: `a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde`;
- delta fixture SHA256: `1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97`;
- line coverage: `99.24%`;
- branch coverage: `96.97%`;
- mutation score: `81.81%` (`1651/2018` killed, zero timeout/suspicious);
- anti-flake: `3` repetitions PASS;
- reference synchronization state: `SYNCED`;
- reference reconstructed sequence: `1003`;
- healthy reference path persists no `SequenceGapEventV1`;
- Lot 40 remains `PLANNED_LOCKED` in the audited Lot 39 lifecycle until this gate is merged.

The complete prerequisite evidence object is checked exactly. Any changed commit, checksum, fixture, quality result, lifecycle status or synchronization prerequisite invalidates the gate.

## Canonical Lot 40 contracts

Inputs, reproduced exactly from canonical roadmap line 41:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`;
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`.

Outputs:

- `BookIntegrityDesynchronizationDetectorStateV1`;
- `BookIntegrityDesynchronizationDetectorAuditV1`;
- `BookIntegrityStateV1`;
- `BookHealthVetoV1`.

The gate intentionally does not create those output schemas. Their exact model/schema/config definitions belong to the implementation scope authorized only after this gate merges.

## Authorized implementation scope

Lot 40 may only implement the offline integrity/desynchronization detector and directly required contracts/configuration:

1. validate Lot 40 entry gates, contract versions and dependency freshness;
2. consume only versioned, lineage-bound offline prerequisites;
3. check sequence continuity explicitly;
4. check crossed and locked book state explicitly;
5. calculate and validate stale age using an injected deterministic decision clock;
6. validate book/reconstruction checksum integrity;
7. detect configured depth collapse without inventing missing depth;
8. validate bid/ask level monotonicity;
9. publish each `book_health_score` component and its inputs rather than a hidden aggregate;
10. produce `BookIntegrityStateV1` and `BookHealthVetoV1` with reason codes and lineage;
11. apply offline `WAIT` below the configured trade-health threshold;
12. apply offline `BLOCK`/`PAUSE` below the configured system-health threshold according to versioned policy;
13. ensure any critical veto dominates an apparently healthy aggregate score;
14. persist state/audit evidence atomically and deterministically;
15. validate negative paths, replay determinism and forbidden capabilities.

`WAIT`, `BLOCK` and `PAUSE` here are offline audited health/veto outputs only. They do not authorize signal generation, risk approval, order routing, trading or execution.

## Explicitly forbidden scope

This gate does not authorize Lot 41 or later capabilities. It forbids:

- external network access, live exchange data, real credentials and network ingestion;
- Lot 41 `Spread, Depth & Imbalance Engine`;
- spread, mid, microprice, depth-band or imbalance analytics;
- liquidity walls, voids, zones, resilience or replenishment inference;
- trade-aggressor classification, order flow, delta/CVD analysis;
- classification-confidence, hidden-liquidity, cluster or stop-zone inference;
- sweep/fakeout/trap engines, derivatives context or game-theory aggregation;
- participant intent presented as fact;
- forecast generation or scenario-to-signal conversion;
- signal generation, risk approval, order routing, trading or execution.

Lot 40 may use the minimum book/reconstruction facts required to determine integrity and health. It may not convert those facts into Lot 41 market features or any downstream alpha/trading capability.

## Pre-implementation boundary

The gate validator requires all Lot 40 production files to remain absent, including detector source/models, config, output schemas, runner, validator, implementation tests, evidence and implementation documentation. It also requires the canonical Lot 41 engine/runner/validator/docs to remain absent.

The gate PR is governance-only. Production work starts from the exact gate merge commit only.

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

Unknown, stale, incompatible, out-of-sequence, ambiguous, crossed, checksum-invalid, depth-collapsed or unreconciled input is fail-closed. A healthy book score is never a signal or trade permission.

## Gate checksum

```text
23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18
```

## Promotion rule

This gate PR must remain governance-only with no Lot 40 production implementation. Lot 40 implementation starts only after this gate is green, reviewed, merged, and the exact merge commit is used as the implementation base. Lot 41 remains `PLANNED_LOCKED` throughout Lot 40 implementation and requires its own gate after an independent Lot 40 post-merge audit.
