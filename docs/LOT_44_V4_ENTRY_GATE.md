# Lot 44 — V4 Implementation Entry Gate

## Decision

`GO_LOT44_IMPLEMENTATION_ENTRY`

This governance gate authorizes a future implementation PR for **Lot 44 — Trades & Aggressor Classification Schema** after the merged Lot 43 post-merge audit `7a207a16e7aa543f9f7c241828f8ea5ae9ed0407`.

The current release is `0.43.0`. The transition is governance-only: seven Lot 44 gate artifacts, eleven historical workflow-archival changes across Lots 40–43, and one governed migration of the historical Lot 43 entry-gate test. `implementation_started=false`. No Lot 44 business implementation file is created by this gate.

## Canonical roadmap binding

- roadmap: `data/audit/product_scope_roadmap_lot21.jsonl`
- immutable roadmap blob: `84de51bda788a8d124fb7d344419c4a4b12030b5`
- source line: `45`
- lot: `Lot 44`
- title: `Trades & Aggressor Classification Schema`
- version: `V4_MICROSTRUCTURE_LIQUIDITY`
- owner: `MicrostructureDomain`
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- canonical status before gate merge: `PLANNED_LOCKED`

The next roadmap row, Lot 45 — **Order Flow, Delta & CVD Engine** — remains `PLANNED_LOCKED`. Roadmap line 47, Lot 46 — **Trade Classification Confidence Engine** — is also bound and remains `PLANNED_LOCKED`; its canonical nine implementation files are required to be physically absent by both the validator and CI gate.

## Prerequisite closure

The gate is based on `7a207a16e7aa543f9f7c241828f8ea5ae9ed0407`, where Lot 43 has the merged post-merge verdict `GO_LOT43_POST_MERGE`.

Frozen Lot 43 evidence carried into this gate:

- source `d45f40aec90b26dd1278ec2f49b405fa5b2ed94e`;
- implementation merge `0b524b1478272e0a69a06b50c68b1b2c3b092964`;
- exact final PR head `69667b5c46ac2ecf7b2a64656f84c374ee929dbf`;
- state checksum `30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6`;
- audit checksum `3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67`;
- resilience checksum `598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb`;
- post-merge audit checksum `167c69b324377ceefd322d59fab7f42d9f7998efde94503d6d86ca4a51ed9c14`;
- line coverage `98.07%`;
- branch coverage `96.88%`;
- mutation score `82.13%`;
- anti-flake repetitions `3`.

## Required contracts

Inputs remain the canonical V4 governance contracts:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`

The future Lot 44 implementation may define only the canonical outputs:

- `TradesAggressorClassificationSchemaStateV1`
- `TradesAggressorClassificationSchemaAuditV1`
- `ClassifiedTradeV1`
- `AggressorConfidenceStateV1`

`AggressorConfidenceStateV1` is a versioned descriptive confidence contract for Lot 44 classification. It does **not** authorize the separate Lot 46 `Trade Classification Confidence Engine`.

## Authorized Lot 44 scope

The implementation entry gate allows only deterministic, offline descriptive trade-side classification:

- timestamped trade input contracts and no-future-leakage ordering;
- quote-test classification as the primary method;
- tick-rule fallback only when quote data is unavailable under explicit policy;
- `BUY_AGGRESSOR`, `SELL_AGGRESSOR`, or `UNKNOWN`;
- explicit classification method and versioned confidence field;
- `unknown_volume_ratio` measurement;
- conservation `total volume = buy + sell + unknown`;
- stale/locked quote degradation to reduced confidence or `UNKNOWN`;
- deterministic state/audit persistence with lineage and checksums;
- no participant intent asserted as fact.

## Explicitly forbidden

The gate does not authorize Lot 45+ or execution authority. In particular it forbids:

- Order Flow / Delta / CVD aggregation or CVD computation;
- the Lot 46 Trade Classification Confidence **engine**;
- absorption/hidden-liquidity inference;
- volume clusters/time-at-level;
- stop zones/liquidity pools;
- sweeps/fakeouts/traps/failed auctions;
- derivatives context or game-theory aggregation;
- participant intent as fact;
- future quote backfill or suppression of unknown volume;
- forecast, scenario-to-signal conversion, signal generation;
- risk approval, order routing, trading, or execution;
- live data, network ingestion, real credentials, external connectivity.

The Lot 46 prohibition is enforced structurally, not only by prose: the immutable roadmap line 47 is validated as `PLANNED_LOCKED`, its exact nine `implementation_files` entries are required, and every one of those paths must be absent at gate certification and on the current gate head.

## Safety boundary

The gate preserves:

```text
analysis_only=true
used_for_decision=false
external_connectivity_allowed=false
network_ingestion_allowed=false
real_credentials_allowed=false
market_event_publication_allowed=false
raw_data_mutation_allowed=false
participant_behavior_inference_explicitly_labeled=true
scenario_score_is_signal=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## Governance-only proof

Before gate merge, all Lot 44 implementation paths, all Lot 45 implementation paths and all canonical Lot 46 confidence-engine implementation paths must be physically absent. The exact governance transition is **19 paths**: seven new Lot 44 gate artifacts, eleven workflow archival/path-scope changes across Lots 40–43, plus `tests/test_lot43_v4_entry_gate.py` as an explicit historical-governance migration.

The historical Lot 43 test migration neutralizes current-tree `LOT43_FORBIDDEN_IMPLEMENTATION_PATHS` and `LOT44_FORBIDDEN_IMPLEMENTATION_PATHS` only inside its replay fixture. Its original certified behavior is still exercised in detached historical worktrees by the Lot 43 workflows. The Lot 44 gate also tests that the current historical-test fixture contains the explicit Lot 44 isolation, so the transition cannot regress silently.

The eleven archived workflows are:

- Lot 40 frozen evidence and post-merge audit;
- Lot 41 source validation, frozen evidence and post-merge audit;
- Lot 42 source validation, frozen evidence and post-merge audit;
- Lot 43 entry gate, frozen evidence and post-merge audit.

These workflows keep their historical certification logic. Path scoping only prevents closed predecessor lots from executing current-head `Lot 44 absent` assertions on the future Lot 44 implementation that this gate authorizes. Lot 43 entry/frozen/post-merge proofs continue to replay their certified historical states; the governance-migrated test is no longer classified as immutable Lot 43 production source on the current tree. The Lot 41 post-merge path filter explicitly includes its root-level frozen report `reports/lot_41_spread_depth_and_imbalance_engine_report.md`, matching the report already protected by its immutability check. Lot 43 source validation itself remains safe because it checks out the frozen Lot 43 source rather than the future current head.

Canonical gate checksum:

`100d21ea18cfd7d9fe275ac0bea162c76a0bb7e5f85e319b543b4053e3c4d5ef`

## Downstream lock

After this gate merges:

- Lot 44 implementation may start in a separate implementation branch/PR under the exact authorized scope;
- Lot 45 remains `PLANNED_LOCKED`;
- Lot 46 Trade Classification Confidence Engine remains `PLANNED_LOCKED` and physically absent;
- no Lot 45 or Lot 46 implementation is authorized;
- this gate itself contains no Lot 44 business implementation.
