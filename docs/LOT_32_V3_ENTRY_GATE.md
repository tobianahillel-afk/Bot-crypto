# Lot 32 — V3 Implementation Entry Gate

## Decision

```text
GO_LOT32_IMPLEMENTATION_ENTRY
```

The user explicitly approved continuation to the next lot after the Lot 31 implementation
and post-merge audit. This gate records that human decision without starting implementation
inside the gate branch.

## Certified baseline

```text
base_commit=77f739102d581dbb6fc76ccbdfe13ce1049e5002
lot31_implementation_merge_commit=235ee2e3a4eabd98e8a59241396f07fc4c29e39e
lot31_post_merge_audit_commit=77f739102d581dbb6fc76ccbdfe13ce1049e5002
current_version=0.31.0
runtime_mode=DATA_GOVERNANCE_ONLY
```

The Lot 31 registry remains metadata-only. It contains one declared source of truth and two
backup source records, with all connectors disabled and no authentication.

## Authorized scope

Lot 32 owns **Instrument, Symbol & Contract Normalization** inside:

```text
owner=MarketDataGovernanceDomain
package_boundary=src/crypto_quant_bot/data_governance
```

The implementation may create only the contracts and deterministic offline logic necessary
to produce:

- `ExchangeInstrumentMetadataV1` input validation;
- `InstrumentRegistryV1`;
- `InstrumentSpecificationV1`;
- `InstrumentSymbolContractNormalizationStateV1`;
- `InstrumentSymbolContractNormalizationAuditV1`.

## Required market model

The closed market-type registry is:

```text
SPOT
PERPETUAL
DATED_FUTURE
OPTION
```

Spot is the first configured and validated example. Perpetual, dated future and option must
be modeled with explicit applicability rules. A field that does not apply is explicitly
`null` or forbidden by the contract; it is never silently omitted or defaulted.

## Mandatory normalization invariants

- canonical instrument IDs are unique;
- venue symbol aliases are unique inside each venue;
- canonical symbol to venue symbol round-trip is deterministic;
- venue symbol to canonical symbol round-trip is deterministic;
- all economic increments and thresholds use canonical decimal strings;
- binary floating-point coercion is forbidden;
- `tick_size`, `lot_size`, `min_qty` and `min_notional` are strictly positive;
- quantization is explicit and direction-aware;
- a quantized amount that violates `min_notional` is rejected;
- source IDs and source revisions link back to the certified Lot 31 registry;
- ambiguous or revised metadata produces `INSTRUMENT_FROZEN`;
- UNKNOWN never becomes an authorization.

## Safety ceiling

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

The gate does not authorize live metadata retrieval, exchange authentication, market event
ingestion, canonical time publication, data-quality scoring, forecasting, signals, risk,
orders, paper trading or live execution.

## Required acceptance evidence

The implementation PR must demonstrate:

1. strict schemas with `additionalProperties=false`;
2. deterministic run1/run2 artifacts with identical checksums;
3. exact canonical ↔ venue symbol round-trip tests;
4. tick, lot, quantity and min-notional boundary tests;
5. spot/perpetual/future/option applicability tests;
6. stale, incomplete, ambiguous and revised metadata fail-closed tests;
7. anti-future-state and source-lineage tests;
8. no network or credential dependency;
9. Ruff, mypy, architecture, security and dependency gates;
10. full repository non-regression and three anti-flake repetitions;
11. targeted line/branch coverage and mutation score at or above repository thresholds.

## Promotion boundary

```text
lot32_implementation_started=false
lot33_status=PLANNED_LOCKED
```

Lot 33 remains locked until Lot 32 is implemented, certified on its exact commit, squash
merged and independently audited post-merge.
