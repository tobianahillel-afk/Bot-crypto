# Lot 31 — V3 Entry Gate

Status: `GO_LOT31_IMPLEMENTATION_ENTRY`

Base commit: `71b6fd8c6a25f390aee06a962d7c3439e224bbfb`

Target runtime ceiling: `DATA_GOVERNANCE_ONLY`

## Purpose

This gate authorizes the start of Lot 31 implementation after the independent Lot 30
post-merge audit. It does not itself implement `SourceRegistryV1`, create a data-governance
package, connect to a provider or unlock any runtime capability.

## Verified prerequisites

- Lot 30 implementation PR #15 was squash-merged as
  `4551f4973ce535a6f2733ea4d92833d84ae298f7`;
- Lot 30 post-merge audit PR #16 was squash-merged as
  `71b6fd8c6a25f390aee06a962d7c3439e224bbfb`;
- project version is `0.30.0`;
- V2 Market Analysis Offline is closed for Lots 21–30;
- the current lifecycle overlay identifies Lot 30 as the latest validated lot;
- the user explicitly approved sequential development of the following lots on
  `2026-08-06T12:08:32Z`;
- V3, Lot 31 and the continuous-market-data addendum were re-read before this gate.

## Lot 31 ownership

```text
owner = MarketDataGovernanceDomain
package = src/crypto_quant_bot/data_governance
runtime_mode = DATA_GOVERNANCE_ONLY
```

Lot 31 may define only governance, registry and audit contracts. It may not ingest or
retrieve market data.

## Required Lot 31 contracts

The implementation must publish and validate:

- `RunContextV1`;
- `LineageEnvelopeV1`;
- `MarketDataGovernanceScopeSourceRegistryStateV1`;
- `MarketDataGovernanceScopeSourceRegistryAuditV1`;
- `MarketDataGovernanceScopeSourceRegistryContractRegistryV1`;
- `MarketDataGovernanceScopeSourceRegistryCapabilityMatrixV1`;
- `SourceRegistryV1`.

Every output must contain at least:

```text
schema_version
event_time
generated_at
lineage_id
validation_state
```

## Required source metadata

Each source entry must explicitly declare:

```text
source_id
provider
venue
endpoint_type
fields
cadence
timezone
license
auth_mode
retention
criticality
source_of_truth
backup_sources
revision_policy
```

Additional temporal and quality metadata required by the V3 addendum must include source
capabilities, expected latency/cadence, timestamp semantics, revisions and quality rules.
Unknown information must remain explicit `UNKNOWN` or nullable according to a closed
schema; it must never be silently converted into permission or a numeric zero.

## Forbidden implementation

Lot 31 must not contain:

- external HTTP, WebSocket, exchange or database connectivity;
- actual market-data ingestion;
- real credentials, API keys, secrets or authenticated adapters;
- forecast, probability, expected return or signal generation;
- `TradeIntent`, `RiskDecisionV1`, `RiskReservationV1` or `OrderIntent` creation;
- paper, sandbox or live execution;
- automatic activation of Lot 32.

The source registry describes possible future sources. A registry entry is not evidence
that the source is connected, healthy, licensed for production or available at runtime.

## Safety invariants

```text
analysis_only=true
used_for_decision=false
external_connectivity_allowed=false
network_ingestion_allowed=false
real_credentials_allowed=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## Acceptance requirements for the implementation PR

- strict closed JSON schemas;
- deterministic registry ordering and checksums;
- duplicate source IDs rejected;
- malformed provider, venue, endpoint, timezone, cadence, licence, auth and revision fields
  rejected;
- missing mandatory source metadata rejected;
- explicit source-of-truth and backup-source relationships validated;
- no circular backup relationships unless explicitly supported and proven safe;
- capability matrix matches registry entries;
- contract registry matches emitted artifacts;
- deterministic replay and tamper tests;
- full repository non-regression;
- targeted line coverage at least `95%` and branch coverage at least `90%`;
- critical mutation score at least `80%`;
- Ruff, mypy, architecture, ownership, traceability, Bandit and dependency audit pass;
- three anti-flake repetitions pass;
- no new unregistered engineering deviation;
- Lot 32 remains `PLANNED_LOCKED` until Lot 31 post-merge audit.

## Gate consequence

The gate records:

```text
human_decision = APPROVED_START_LOT31
implementation_started = false
gate_status = GO_LOT31_IMPLEMENTATION_ENTRY
next_lot_status = PLANNED_LOCKED
```

`implementation_started=false` describes this gate artifact itself. It becomes historical
evidence when merged; the separate Lot 31 implementation branch may then begin.
