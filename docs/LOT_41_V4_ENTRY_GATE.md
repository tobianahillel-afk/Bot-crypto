# Lot 41 — V4 Implementation Entry Gate

## Decision

```text
gate_status=GO_LOT41_IMPLEMENTATION_ENTRY
base_commit=20975b505c7f8b527751fb5d3bce034c6e55dcc2
current_version=0.40.0
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
canonical_title=Spread, Depth & Imbalance Engine
lot42_status=PLANNED_LOCKED
```

The independent Lot 40 post-merge audit is complete on the exact audited `main` commit above. Lot 41 may begin only inside the canonical offline spread/depth/imbalance boundary. This gate does not implement Lot 41, does not create its production contracts/configuration, and does not unlock Lot 42.

## Canonical authority

The gate is bound to the immutable product-scope registry:

```text
path=data/audit/product_scope_roadmap_lot21.jsonl
line=42
blob_sha=84de51bda788a8d124fb7d344419c4a4b12030b5
lot_id=Lot 41
title=Spread, Depth & Imbalance Engine
version_id=V4_MICROSTRUCTURE_LIQUIDITY
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
package_boundary=src/crypto_quant_bot/microstructure
```

The validator recomputes the Git blob SHA, parses Lot 41 at line 42 and Lot 42 at line 43, and checks both exact identities. The detailed normative authority is `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`.

## Verified Lot 40 prerequisites

- audited release: `0.40.0`;
- independent Lot 40 post-merge audit merge: `20975b505c7f8b527751fb5d3bce034c6e55dcc2`;
- post-merge verdict: `GO_LOT40_POST_MERGE`;
- Lot 40 status: `IMPLEMENTED_VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY`;
- implementation source head: `b9a18a8aaef858b985c3f75ef2aa8955ec521e9f`;
- frozen evidence head: `ea04fe826261eeed5a59eea60265b38b68404b6b`;
- final implementation PR head: `1268772c07cbb76c18b3267aef12dad5ba58af31`;
- implementation merge: `88f0dac660e262a1c468d9cd75c5e7996ce4817b`;
- state checksum: `e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477`;
- audit checksum: `978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c`;
- integrity checksum: `35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a`;
- health-veto checksum: `000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc`;
- line coverage: `97.31%`;
- branch coverage: `91.24%`;
- mutation score: `82.32%`;
- anti-flake: `3` repetitions PASS;
- reference book health: `HEALTHY`, score `100`, consequence `NONE`, sequence `1003`;
- Lot 41 remains `PLANNED_LOCKED` in the audited Lot 40 lifecycle until this gate is merged.

Any changed commit, checksum, quality result, lifecycle status, health prerequisite or roadmap binding invalidates this gate.

## Canonical Lot 41 contracts

Inputs, reproduced exactly from canonical roadmap line 42:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`;
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`.

Outputs:

- `SpreadDepthImbalanceEngineStateV1`;
- `SpreadDepthImbalanceEngineAuditV1`;
- `BookFeatureStateV1`.

The implementation may bind certified Lot 40 book-integrity/reconstruction evidence through lineage, but it may not bypass or reinterpret a Lot 40 health veto.

## Authorized implementation scope

Lot 41 may only implement deterministic offline book features directly required by the canonical contract:

1. validate Lot 41 entry gates, contract versions and dependency freshness;
2. bind versioned configuration and lineage to certified offline prerequisites;
3. calculate absolute spread and spread in bps;
4. calculate mid price;
5. calculate microprice from observed top-of-book price/quantity only;
6. calculate depth within versioned bps bands;
7. calculate cumulative depth from observed levels;
8. calculate symmetric imbalance with explicit zero-denominator handling;
9. publish feature values by configured horizon/level with book-quality evidence;
10. refuse extrapolation beyond observed depth;
11. publish `BookFeatureStateV1` plus state/audit reason codes and uncertainty;
12. persist state/audit evidence atomically and deterministically;
13. validate empty/unilateral books, unit invariance, bounds, replay and forbidden capabilities.

These outputs are descriptive offline microstructure features. They are not participant intent, forecasts, signals or trade permissions.

## Explicitly forbidden scope

Lot 42 — `Liquidity Zones, Walls & Voids Engine` — remains `PLANNED_LOCKED`. Lot 41 must not cluster liquidity zones, infer walls/voids, persistence, replenishment, cancellation-rate intent, resilience, trade aggressors, order-flow/CVD, hidden liquidity, stop zones, sweeps/fakeouts/traps, derivatives context, game-theory scenarios, forecasts, signals, risk approval, routing, trading or execution.

External network access, live exchange data, real credentials and network ingestion remain forbidden. Participant intent may never be presented as fact.

## Pre-implementation boundary

Before this gate merges, all Lot 41 production files remain absent: engine/models, config, output schemas, runner, validator, implementation tests, output evidence, report and implementation documentation. Canonical Lot 42 source/runner/validator/docs must also remain absent.

The gate PR is governance-only and must contain exactly seven gate files. Lot 41 production work starts from the exact gate merge commit only.

## Quality gates

```text
line_coverage >= 95%
branch_coverage >= 90%
mutation_score >= 80%
anti_flake_repetitions >= 3
```

No threshold may be reduced, bypassed or satisfied through permissive coercion/fallback.

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

Unknown, stale, incompatible, unhealthy, unilateral, empty, ambiguous or insufficient-depth input is fail-closed according to the implementation contract. A valid feature state never grants trading permission.

## Gate checksum

```text
1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe
```

## Promotion rule

This gate must be green, reviewed and merged while governance-only. Lot 41 implementation then starts from that exact merge commit. Lot 42 remains `PLANNED_LOCKED` through implementation, freeze, merge and the independent Lot 41 post-merge audit; only a later dedicated Lot 42 gate may change that status.
