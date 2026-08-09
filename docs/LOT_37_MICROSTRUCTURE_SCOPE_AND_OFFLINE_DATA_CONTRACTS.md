# Lot 37 — Microstructure Scope & Offline Data Contracts

## Status

`IMPLEMENTATION_CANDIDATE_OFFLINE_SCOPE_ONLY`

Owner: `MicrostructureDomain`  
Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
Package: `src/crypto_quant_bot/microstructure`  
Entry gate: `GO_LOT37_IMPLEMENTATION_ENTRY`

## Objective

Lot 37 creates the V4 domain boundary and the deterministic offline contract surface required by later microstructure lots. It does **not** implement an order-book engine, trade classification, order flow, liquidity inference, participant behavior inference, scenario aggregation, signals, risk approval, routing, trading or execution.

The implementation publishes exactly four Lot 37 outputs:

- `MicrostructureScopeOfflineDataContractsStateV1`;
- `MicrostructureScopeOfflineDataContractsAuditV1`;
- `MicrostructureScopeOfflineDataContractsContractRegistryV1`;
- `MicrostructureScopeOfflineDataContractsCapabilityMatrixV1`.

## Entry evidence

The implementation is bound to the audited V3 closure and the merged V4 entry gate:

- V3 post-merge audit commit: `33fba0abf7463fc54a36282476ee51655ff09919`;
- Lot 37 gate checksum: `37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d`;
- Lot 36 state checksum: `635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592`;
- Lot 36 audit checksum: `ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42`;
- Lot 38 remains `PLANNED_LOCKED`.

## Offline input contracts

Two gate-certified fixtures prove only that the required *shape of offline input data is available*:

- `MicrostructureOfflineL2InputV1`;
- `MicrostructureOfflineTradeInputV1`.

They are explicitly:

- fixture-only;
- non-canonical;
- offline;
- non-decision data;
- non-network;
- non-executable.

Lot 37 does not normalize those fixtures into a live/canonical market-event stream. The trade fixture keeps `side=UNKNOWN`; aggressor classification belongs to Lot 44.

## Contract registry

The contract registry contains exactly six contracts: two input contracts and the four Lot 37 outputs. Every entry has an owner, schema path, producer, consumer, status and enabling lot. Schema files live only under `contracts/schemas/`.

## Capability matrix

The matrix classifies every capability relevant to the V4 boundary:

- `REQUIRED`: four Lot 37 scope/governance capabilities;
- `DISABLED`: all fifteen future V4 capabilities from Lots 38–52;
- `FORBIDDEN`: network access, participant intent presented as fact, scenario-to-signal conversion, signal generation, risk approval, order routing, trading and execution.

A `DISABLED` capability must remain `PLANNED_LOCKED` and bound to its future lot. A `FORBIDDEN` capability has no enabling lot.

## Public API

Lot 37 exposes only:

- `build_lot37_artifacts`;
- `write_lot37_artifacts`;
- `MicrostructureScopeOfflineDataContractsStateV1`;
- `MicrostructureScopeOfflineDataContractsAuditV1`.

Future Lot 38+ internals are not part of the Lot 37 public API.

## Determinism and time

The reference configuration uses explicit UTC event, availability and generation timestamps. Causality is enforced as:

`event_time <= available_at <= generated_at`

Input freshness is computed using integer microseconds. The reference processing latency is `950000 us`. Run1 and run2 with the same code commit and immutable inputs must produce byte-equivalent logical JSON and identical canonical checksums.

## Fail-closed rules

Publication is refused when any of the following is observed:

- gate checksum mismatch;
- V3 closure not certified;
- unexpected config field or incompatible config version;
- missing contract schema;
- fixture checksum mismatch;
- fixture marked canonical or decision-usable;
- stale or causally impossible fixture;
- trade aggressor side pre-classified by Lot 37;
- contract registry membership drift;
- public API membership drift;
- future V4 capability activated early;
- forbidden capability weakened;
- safety dictionary drift;
- invalid checksum, Git SHA, timestamp or reason code.

UNKNOWN is never converted to permission.

## Safety boundary

The state and audit both persist the exact safety boundary:

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

## Observability

The state records deterministic counters for contracts, capabilities by class, public API symbols, offline fixtures, validation failures and processing latency. Validation failures do not produce a valid state.

## Persistence

State, audit, contract-registry and capability-matrix artifacts are written atomically using the existing V3 audited persistence primitive. No input fixture or upstream V3 artifact is mutated.

## Non-goals

This lot explicitly does not implement Lots 38–52. In particular it performs no sorting/aggregation of an order book, no delta reconstruction, no spread/depth/imbalance calculation, no aggressor classification, no CVD, no absorption/hidden-liquidity inference, no stop-zone inference, no game-theory scenario generation and no derivatives modeling.

## Promotion

Lot 38 remains locked until:

1. Lot 37 implementation CI is green on an exact frozen head;
2. coverage and branch thresholds pass;
3. mutation score for the critical Lot 37 boundary passes `>=80%`;
4. deterministic replay and anti-flake pass;
5. the implementation PR is merged;
6. an independent Lot 37 post-merge audit records GO;
7. a distinct Lot 38 entry gate is approved.
