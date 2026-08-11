# Lot 42 — V4 Implementation Entry Gate

## Decision

```text
gate_status=GO_LOT42_IMPLEMENTATION_ENTRY
base_commit=2b4186aa0bac2f60819361958e6eff215699ab53
current_version=0.41.0
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
canonical_title=Liquidity Zones, Walls & Voids Engine
lot43_status=PLANNED_LOCKED
```

The independent Lot 41 post-merge audit is complete on the exact audited `main` commit above. Lot 42 may begin only inside the canonical offline liquidity-zone/wall/void boundary. This gate does not implement Lot 42, does not create its production contracts/configuration, and does not unlock Lot 43.

## Canonical authority

The gate is bound to the immutable product-scope registry:

```text
path=data/audit/product_scope_roadmap_lot21.jsonl
line=43
blob_sha=84de51bda788a8d124fb7d344419c4a4b12030b5
lot_id=Lot 42
title=Liquidity Zones, Walls & Voids Engine
version_id=V4_MICROSTRUCTURE_LIQUIDITY
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
package_boundary=src/crypto_quant_bot/microstructure
```

The validator recomputes the Git blob SHA, parses Lot 42 at line 43 and Lot 43 at line 44, and checks both exact identities. The detailed normative authority is `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`.

## Verified Lot 41 prerequisites

- audited release: `0.41.0`;
- independent Lot 41 post-merge audit merge: `2b4186aa0bac2f60819361958e6eff215699ab53`;
- post-merge verdict: `GO_LOT41_POST_MERGE`;
- Lot 41 status: `IMPLEMENTED_VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY`;
- Lot 41 entry-gate merge: `75822f8ea7c6f67f73649d2f43be6efba840ab67`;
- implementation source head: `14c0d8da1b02d076b3c43a07a34ac96c673018b0`;
- frozen evidence head: `7ada0ca6c4d439505ef453b988dedd4aa96c1a32`;
- final implementation PR head: `89ae244db77f16f31d226a7494d78b65b904dcd9`;
- implementation merge: `a253ce35c97303e8b8c65707c07597e996b3a832`;
- engine-state checksum: `23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573`;
- engine-audit checksum: `af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd`;
- feature checksum: `77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5`;
- line coverage: `100.00%`;
- branch coverage: `100.00%`;
- mutation score: `81.93%`;
- anti-flake: `3` repetitions PASS;
- reference book health: `HEALTHY`, score `100`, consequence `NONE`, sequence `1003`;
- Lot 42 remains `PLANNED_LOCKED` in the audited Lot 41 lifecycle until this gate is merged.

Any changed commit, checksum, quality result, lifecycle status, roadmap binding or safety prerequisite invalidates this gate.

## Canonical Lot 42 contracts

Inputs, reproduced exactly from canonical roadmap line 43:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`;
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`.

Outputs:

- `LiquidityZonesWallsVoidsEngineStateV1`;
- `LiquidityZonesWallsVoidsEngineAuditV1`;
- `LiquidityZoneSetV1`.

The implementation may bind certified Lot 41 feature/book-quality evidence through lineage, but it may not reinterpret a healthy feature state as participant intent, forecast, signal or trade permission.

## Authorized implementation scope

Lot 42 may only implement deterministic offline liquidity-structure features directly required by the canonical contract:

1. validate Lot 42 entry gates, contract versions and dependency freshness;
2. bind versioned configuration and lineage to certified offline prerequisites;
3. cluster adjacent observed book levels according to a versioned bps-distance rule;
4. measure zone notional from observed levels only;
5. measure zone persistence over explicitly available historical observations;
6. measure zone replenishment without promoting it to the Lot 43 resilience engine;
7. measure cancellation rate without inferring participant intent;
8. measure distance to mid with explicit decimal semantics;
9. classify `displayed_wall`, `persistent_zone` and `liquidity_void`;
10. detect liquidity voids bilaterally when the observed book supports them;
11. expire zones when freshness or persistence requirements fail;
12. publish `LiquidityZoneSetV1` plus state/audit reason codes and uncertainty;
13. persist state/audit evidence atomically and deterministically;
14. validate instantaneous cancellation, bilateral voids, stale inputs, replay and forbidden capabilities.

These outputs are descriptive offline microstructure structures. They are not participant intent, forecasts, signals or trade permissions.

## Explicitly forbidden scope

Lot 43 — `Book Resilience & Replenishment Engine` — remains `PLANNED_LOCKED`. Lot 42 must not implement resilience scoring, trade aggressors, order-flow/CVD, classification-confidence engines, hidden-liquidity inference, volume clusters, stop/liquidity-pool inference, sweeps/fakeouts/traps, derivatives context, game-theory aggregation, participant intent as fact, forecasts, signals, risk approval, routing, trading or execution.

Lot 42 may measure replenishment and cancellation **only as attributes of a liquidity-zone observation required by its own roadmap contract**. It must not promote those measurements into the dedicated Lot 43 resilience capability or into intent inference.

External network access, live exchange data, real credentials and network ingestion remain forbidden.

## Pre-implementation boundary

Before this gate merges, the complete expected Lot 42 production inventory remains absent: engine/models/validation helper, config, output schemas, runner, implementation validator, frozen/no-connectivity validators, implementation/schema/validation tests, runtime artifacts, quality evidence, report and implementation documentation. Canonical Lot 43 production files must also remain absent.

This is intentionally stricter than checking only the engine entrypoint: partial or premature Lot 42 implementation is rejected even when the main engine file is absent.

The gate PR is governance-only and must contain exactly seven gate files. Lot 42 production work starts from the exact gate merge commit only.

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

Unknown, stale, incompatible, unhealthy, unilateral, empty, ambiguous or insufficient evidence is fail-closed according to the future implementation contract. A valid liquidity-zone state never grants trading permission.

## Gate checksum

```text
7ab3b17a74d30866fbec4ec15acfe608a9545e8831d80dcb39db2d059e293924
```

## Promotion rule

This gate must be green, reviewed and merged while governance-only. Lot 42 implementation then starts from that exact merge commit. Lot 43 remains `PLANNED_LOCKED` through implementation, freeze, merge and the independent Lot 42 post-merge audit; only a later dedicated Lot 43 gate may change that status.
