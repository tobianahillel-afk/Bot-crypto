# Lot 32 — Instrument, Symbol & Contract Normalization

## Status

`IMPLEMENTATION_IN_PROGRESS_AWAITING_EXACT_COMMIT_VALIDATION`

## Objective

Lot 32 is the only owner of deterministic instrument identity, venue-symbol aliases and
contract metadata inside `MarketDataGovernanceDomain`. It converts approved metadata-only
records into `InstrumentRegistryV1` without performing any network request or enabling any
decision or execution capability.

## Runtime and ownership

```text
owner=MarketDataGovernanceDomain
package=src/crypto_quant_bot/data_governance
runtime_mode=DATA_GOVERNANCE_ONLY
external_connectivity_allowed=false
network_ingestion_allowed=false
```

## Inputs

- `RunContextV1`-compatible Lot 32 context;
- Lot 32 entry gate;
- certified Lot 31 `SourceRegistryV1`;
- certified Lot 31 state and audit checksums;
- versioned offline instrument metadata configuration.

A source is usable only when its exact `source_id`, venue and revision exist in the Lot 31
registry and the source remains approved, unauthenticated, disabled and connection-disabled.

## Outputs

- `InstrumentSpecificationV1`;
- `InstrumentRegistryV1`;
- `InstrumentSymbolContractNormalizationStateV1`;
- `InstrumentSymbolContractNormalizationAuditV1`.

The persisted artifacts are:

```text
data/audit/instrument_symbol_and_contract_normalization_lot32.json
data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json
data/audit/instrument_registry_lot32.json
```

## Canonical identity

An instrument owns one stable `instrument_id` and one canonical symbol:

```text
canonical_symbol = BASE/QUOTE:MARKET_TYPE
```

The closed market-type registry is:

```text
SPOT
PERPETUAL
DATED_FUTURE
OPTION
```

Venue symbols are aliases nested under the canonical instrument. A venue alias is unique by
`(venue, exchange_symbol)` and contains its own tick, lot, minimums, precision, fee and
source-lineage metadata.

## Certified configuration

The initial certification fixture contains one canonical instrument:

```text
instrument_id=btc-eur-spot
canonical_symbol=BTC/EUR:SPOT
```

Its metadata-only aliases are:

```text
BITSTAMP -> btceur
COINBASE -> BTC-EUR
KRAKEN   -> XBTEUR
```

This configuration is a deterministic reference contract, not a live claim about current
exchange production settings. Updating an alias requires a versioned source/config revision
and a new certification run.

## Bidirectional round-trip

For every alias the following identities must both hold:

```text
canonical_symbol + venue -> exchange_symbol
venue + exchange_symbol -> canonical_symbol
```

Unknown aliases, duplicate aliases, duplicate canonical symbols or non-deterministic mappings
are rejected.

## Decimal and quantization policy

All economic values are canonical decimal strings. Python binary floats, exponent notation,
leading zeros, trailing insignificant zeros, NaN and infinity are rejected.

```text
q_price = floor(price / tick_size) * tick_size
q_qty   = floor(quantity / lot_size) * lot_size
notional = q_price * q_qty
```

After quantization:

- price and quantity must remain positive;
- quantity must satisfy `min_qty`;
- notional must satisfy `min_notional`;
- price precision must match `tick_size` decimal places;
- quantity precision must match `lot_size` decimal places.

A boundary violation rejects the candidate. Lot 32 does not create an order intent.

## Contract applicability

### Spot

```text
contract_size=null
expiry_time=null
strike_price=null
option_type=null
settlement_asset=quote_asset
margin_mode=null
leverage_policy=FORBIDDEN
```

### Perpetual

- `contract_size` required;
- `expiry_time`, `strike_price`, `option_type` null.

### Dated future

- `contract_size` and `expiry_time` required;
- option fields null.

### Option

- `contract_size`, `expiry_time`, `strike_price` and `option_type` required;
- `option_type` is `CALL` or `PUT`.

A non-applicable field is explicitly null. Missing or implicit applicability is rejected.

## Freeze policy

The following conditions are fail-closed and represented operationally as
`INSTRUMENT_FROZEN` before any valid state may be published:

- ambiguous canonical identity;
- duplicate venue alias;
- unknown source;
- source venue mismatch;
- source revision mismatch;
- unexpected metadata revision;
- incomplete contract applicability;
- invalid decimal or precision metadata;
- unsafe gate or lineage divergence.

The certified artifact contains zero frozen instruments. A failing record is not silently
excluded and cannot become a valid instrument.

## Determinism and persistence

- inputs are versioned files only;
- timestamps are explicit UTC values;
- source, state and audit lineage checksums are recorded;
- JSON serialization is sorted and UTF-8 canonical for checksums;
- writes use temporary files, `fsync` and atomic replacement;
- two runs on the same code/config/input commit must be byte-identical.

## Safety boundary

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

Lot 32 does not own canonical time, data-quality scoring, forecasting, signals, portfolio
risk, orders or execution.

## Completion gate

Completion requires strict schemas, unit/integration/negative/replay/security tests, targeted
line and branch coverage, mutation score at or above 80%, full repository non-regression and
three anti-flake repetitions on the exact implementation head.

Lot 33 remains `PLANNED_LOCKED` until Lot 32 is squash-merged and independently audited.
