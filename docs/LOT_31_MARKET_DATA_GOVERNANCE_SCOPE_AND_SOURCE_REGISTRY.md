# Lot 31 — Market Data Governance Scope & Source Registry

## Status

`IMPLEMENTATION_IN_PROGRESS_AWAITING_EXACT_HEAD_CI`

## Purpose

Lot 31 opens V3 through a strictly metadata-only governance layer. It defines the public
boundary of `MarketDataGovernanceDomain`, the contracts owned by the domain, the capability
matrix, and `SourceRegistryV1`. It performs no network request and ingests no market event.

## Owner and boundary

```text
owner = MarketDataGovernanceDomain
package = src/crypto_quant_bot/data_governance
runtime_mode = DATA_GOVERNANCE_ONLY
```

The package may depend only on public contracts, the defensive core and the Python standard
library. It cannot import or call strategy, risk, portfolio, connectors or execution code.

## Entry gate

Implementation consumes the merged and checksum-protected gate:

```text
data/audit/lot31_v3_entry_gate.json
```

The gate must state `GO_LOT31_IMPLEMENTATION_ENTRY`, bind Lot 31 to the V3 owner and package,
record the human start decision, leave `implementation_started=false`, and keep Lot 32
`PLANNED_LOCKED`.

## Inputs

- `RunContextV1` with explicit runtime, config and code commit;
- `LineageEnvelopeV1` bound to the certified Lot 30 closure state;
- `market_data_source_registry_v1.json` as the versioned metadata configuration;
- no remote response, credential, exchange session or network socket.

## Outputs

- `MarketDataGovernanceScopeSourceRegistryStateV1`;
- `MarketDataGovernanceScopeSourceRegistryAuditV1`;
- `MarketDataGovernanceScopeSourceRegistryContractRegistryV1`;
- `MarketDataGovernanceScopeSourceRegistryCapabilityMatrixV1`;
- `SourceRegistryV1`.

The state, audit and standalone source registry are persisted atomically in `data/audit`.

## Source registry contract

Every source declares at least:

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

Lot 31 additionally records a non-routable endpoint descriptor, schema version, revision,
approval status and connection status. Exactly one source is the source of truth. All backup
references must exist and the backup graph must be acyclic.

The initial registry contains three metadata declarations for the BTC/EUR spot scope. These
names are governance records only. They are not proof that the corresponding external data
has been fetched, licensed for production, or validated economically.

## Capability matrix

Statuses are closed to:

```text
REQUIRED
OPTIONAL_RESEARCH
DISABLED
FORBIDDEN
```

Only `source_registry` is `REQUIRED` in Lot 31. Instrument normalization, canonical time,
data quality and continuous market data remain disabled for Lots 32–36. Forecasts, signals,
trade execution and external connectivity remain forbidden.

## Determinism and checksums

JSON is serialized canonically with sorted keys and compact separators before SHA-256.
The state checksum excludes its checksum field. The audit checksum excludes its checksum
field and binds the state checksum and configuration file checksum. The runner must produce
byte-identical state, audit and registry artifacts on two executions with the same commit.

## Time and lookahead boundary

`event_time`, `available_at` and `generated_at` are explicit UTC timestamps and must satisfy:

```text
event_time <= available_at <= generated_at
```

Lot 31 governs source metadata only; it does not claim that a market event was available.
Future-state or timezone-naive values are rejected.

## Fail-closed safety

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

Missing, unknown, duplicated, cyclic, secret-bearing, authenticated or connection-enabled
metadata raises `SourceRegistryValidationError`. No permissive default converts unknown state
into approval.

## Atomic persistence

Artifacts are written to a temporary file in the destination directory, flushed and fsynced,
then atomically replaced. A partial artifact is never treated as valid evidence.

## Non-goals

Lot 31 does not:

- connect to Kraken, Coinbase, Bitstamp or any other provider;
- download instrument metadata or market data;
- normalize instruments, symbols, timestamps, candles, trades or books;
- calculate data-quality scores, forecasts, scenarios, signals or positions;
- create `TradeIntent`, `RiskDecision`, `OrderIntent` or an order;
- enable Lot 32.

## Required validation

- deterministic run1/run2 and byte comparison;
- strict schema parsing;
- targeted line coverage >= 95% and branch coverage >= 90%;
- mutation score >= 80% on critical Lot 31 code;
- unknown source, duplicate source, cycle and active connection rejection;
- secret/authentication rejection;
- UTC and anti-future-state checks;
- architecture, ownership, traceability and engineering-deviation gates;
- full repository regression and three anti-flake repetitions;
- Bandit and locked dependency audit.
