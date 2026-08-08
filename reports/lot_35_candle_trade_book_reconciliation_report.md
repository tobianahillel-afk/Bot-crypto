# Lot 35 — Candle / Trade / Book Reconciliation Report

## Status

`IMPLEMENTED_AWAITING_EXACT_HEAD_CI`

## Scope implemented

Lot 35 adds deterministic offline reconciliation for candle, trade and book evidence under
`MarketDataGovernanceDomain`. No external connector, live market data, source mutation,
forecast, signal, risk approval, order routing, trading or execution path is introduced.

## Reference fixture

```text
reports=3
MATCH=2
TOLERATED_DIFF=1
MINOR_DIVERGENCE=0
CRITICAL_DIVERGENCE=0
veto=ALLOW_ANALYSIS
```

The tolerated trade difference is explicit and bounded:

```text
fee_abs=0.005 <= 0.01
timestamp_us=50000 <= 100000
```

## Certified reference checksums

```text
state_output_checksum=8fc7243beffdf985fd6947557b87ab7bd27f9191520eb2d5d9af25d1e7a886b4
audit_checksum=98a88396f5b2e5ffc1cde02435399540ad213f5ec361b33e8a19c08b0fedf1de
reference_code_commit=a4501bb0d400c6c1b5cf970fc5aa6456ad8c6ea8
```

## Classification policy

- exact equality -> `MATCH`;
- non-zero deltas within versioned tolerance -> `TOLERATED_DIFF`;
- above tolerance but within critical multiplier -> `MINOR_DIVERGENCE` -> `PAUSE`;
- critical boundary exceeded, identifier mismatch, orphan or unknown source ownership ->
  `CRITICAL_DIVERGENCE` -> `KILL_SWITCH` governance semantics.

The veto is evidence only. Safety remains:

```text
external_connectivity_allowed=false
network_ingestion_allowed=false
raw_data_mutation_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## CI evidence

Exact-head line/branch coverage, mutation score, full regression, anti-flake, security and
architecture evidence will be frozen here only after GitHub Actions passes on the final
implementation head. No provisional metric is promoted as certified evidence.

## Promotion

Lot 35 remains awaiting CI/merge/audit. Lot 36 remains `PLANNED_LOCKED`.
