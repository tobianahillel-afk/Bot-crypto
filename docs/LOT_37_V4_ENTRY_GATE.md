# Lot 37 — V4 Implementation Entry Gate

## Decision

```text
gate_status=GO_LOT37_IMPLEMENTATION_ENTRY
base_commit=33fba0abf7463fc54a36282476ee51655ff09919
current_version=0.36.0
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
canonical_title=Microstructure Scope & Offline Data Contracts
lot38_status=PLANNED_LOCKED
```

The independent Lot 36 post-merge audit is complete on the exact audited `main` commit above and V3 Market Data Governance is closed. Lot 37 may begin only inside the V4 scope-and-contracts boundary defined by the canonical roadmap. This gate does not implement any microstructure engine and does not unlock Lot 38.

## Canonical authority

The authoritative Lot 37 record is bound to:

```text
path=data/audit/product_scope_roadmap_lot21.jsonl
line=38
blob_sha=84de51bda788a8d124fb7d344419c4a4b12030b5
lot_id=Lot 37
title=Microstructure Scope & Offline Data Contracts
version_id=V4_MICROSTRUCTURE_LIQUIDITY
owner=MicrostructureDomain
runtime_mode=OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY
package_boundary=src/crypto_quant_bot/microstructure
```

The validator recomputes the Git blob SHA of the canonical JSONL roadmap and parses line 38 directly. The detailed V4 specification is `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`.

## Verified V3 prerequisites

- V3 audited closure merge: `33fba0abf7463fc54a36282476ee51655ff09919`;
- audited release: `0.36.0`;
- lifecycle latest implemented lot: `36`;
- Lot 36 status: `IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY`;
- `v3_closed=true` at the release/lifecycle layer;
- Lot 36 implementation source: `c21b8f242270bd87eebbf7279635ab8bb51b8666`;
- Lot 36 canonical evidence freeze: `b3680f5da0a3fd98fdedc31599c829dc60808290`;
- Lot 36 exact-head CI attestation: `16f3454c6f912f3f00f79836950047b15687abce`;
- Lot 36 implementation merge: `87da195283797247505e4fc650214e33e759e21a`;
- state checksum: `635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592`;
- audit checksum: `ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42`;
- historical closure-candidate manifest checksum: `6a9935e728a93a23a3804106dc54aa216f4f9fedad3635b5507139f4ccbfc37f`;
- replay checksum: `cef50b5191c1f3c78baaa3906c4c5ded59f1dd45dad0271a0071b7056b6af91d`;
- line coverage: `100.00%`;
- branch coverage: `100.00%`;
- mutation score: `83.48%`;
- anti-flake: `3` repetitions PASS;
- trading, execution, raw mutation, external connectivity and network ingestion remain disabled.

The implementation-stage Lot 36 manifest intentionally remains historical with `v3_closed=false`; the independent post-merge lifecycle overlay is the authority that closes V3.

## Offline L2 / trades availability prerequisite

The V4 version entry gate requires V3 closure and L2/trades data availability. This gate satisfies the data-availability prerequisite with two deterministic **test-only offline fixtures**:

- `tests/fixtures/lot37/offline_l2_availability_fixture_v1.json`;
- `tests/fixtures/lot37/offline_trade_availability_fixture_v1.json`.

These fixtures are deliberately marked:

```text
fixture_only=true
canonical_contract=false
used_for_decision=false
```

They are not exchange ingestion, not live data, not a Lot 38 OrderBookSnapshot implementation and not canonical V4 market-data contracts. Their only purpose is to prove that Lot 37 can define and validate offline contracts against available representative L2/trade-shaped input.

The L2 fixture is checked for causal timestamps, positive decimal price/quantity values and a strictly non-crossed book. The trade fixture is checked for causal timestamps, unique IDs and positive decimal price/quantity values. Every trade side remains `UNKNOWN`; aggressor classification belongs to a later V4 lot and is forbidden here.

## Authorized Lot 37 implementation scope

Lot 37 may implement only `Microstructure Scope & Offline Data Contracts` inside `MicrostructureDomain`:

1. define the V4 microstructure scope and domain boundary;
2. define versioned offline input/output contracts and their registry;
3. define the public domain API and permitted dependencies;
4. classify every planned V4 capability as `REQUIRED`, `OPTIONAL_RESEARCH`, `DISABLED` or `FORBIDDEN`;
5. bind configuration, lineage, timestamps, validation state, reason codes and deterministic checksums;
6. validate input availability and schema/freshness prerequisites;
7. persist deterministic state and audit artifacts atomically;
8. prove negative/forbidden capability behavior and the complete chain through Lot 37.

## Required outputs

- `MicrostructureScopeOfflineDataContractsStateV1`;
- `MicrostructureScopeOfflineDataContractsAuditV1`;
- `MicrostructureScopeOfflineDataContractsContractRegistryV1`;
- `MicrostructureScopeOfflineDataContractsCapabilityMatrixV1`.

No output may imply a trading permission. UNKNOWN, stale, incompatible or ambiguous input remains fail-closed.

## Explicitly forbidden scope

This gate does **not** authorize implementation of Lot 38 or later V4 engines. In particular it forbids:

- external network access, live exchange data, real credentials or network ingestion;
- canonical L2 snapshot engine logic;
- order-book delta/sequence reconstruction;
- book-integrity/desynchronization algorithms;
- spread/depth/imbalance calculations;
- liquidity wall/void/zone inference;
- resilience/replenishment analysis;
- trade aggressor classification;
- order-flow/delta/CVD computation;
- classification-confidence engines;
- absorption/hidden-liquidity inference;
- volume-cluster/time-at-level inference;
- stop/liquidity-pool inference;
- sweep/fakeout/trap/failed-auction engines;
- derivatives context fusion;
- participant intent presented as fact;
- game-theory scenario aggregation;
- scenario-to-signal conversion;
- forecasts, signals, risk approval, order routing, trading or execution.

Participant behavior, when introduced in later V4 lots, must remain explicitly labeled inference. `scenario_score != signal` remains invariant.

## Quality gates

```text
line_coverage_min=95%
branch_coverage_min=90%
mutation_score_min=80%
anti_flake_repetitions=3
```

These are the implementation quality thresholds that Lot 37 must satisfy before promotion. The entry gate itself must pass targeted tests, full regression, anti-flake repetitions, architecture/roadmap/traceability/engineering validation and security/dependency checks.

## Safety

```text
analysis_only=true
used_for_decision=false
participant_behavior_inference_explicitly_labeled=true
scenario_score_is_signal=false
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

## Promotion boundary

Merging this gate authorizes only the start of Lot 37 implementation. `implementation_started=false` remains part of the gate artifact itself. Lot 38 remains `PLANNED_LOCKED` until Lot 37 is implemented, independently audited post-merge, and a distinct Lot 38 entry gate is approved.

## Immutable gate checksum

```text
37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d
```
