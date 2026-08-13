# Lot 44 — Trades & Aggressor Classification Schema

## Scope

Lot 44 implements only deterministic offline **trade aggressor classification** inside `MicrostructureDomain` under merged gate `GO_LOT44_IMPLEMENTATION_ENTRY` (`6bbf4fcc5543f2599378bcab93263e2c8cebcec6`).

Runtime is `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`. The implementation is descriptive and non-executable.

## Canonical inputs

Lot 44 does not create a parallel market-data source.

- Trade availability source: Lot 37 `MicrostructureOfflineTradeInputV1`, fixture `tests/fixtures/lot37/offline_trade_availability_fixture_v1.json`, frozen SHA256 `b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8`.
- Quote/book source: canonical Lot 38 `OrderBookSnapshotV1`, persisted at `data/audit/order_book_snapshot_lot38.json`, snapshot checksum `0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16`.

The Lot 37 trade fixture contains an event/availability envelope rather than individual timestamps. Lot 44 maps each contained record to `TimestampedTradeV1` while preserving the exact envelope `event_time` and `available_at` as the trade `event_time` and `receive_time`. Raw `side` must remain `UNKNOWN`.

## Classification policy

Quote test is primary. A quote is usable only when source/venue/instrument/market identity matches, its `receive_time` is not after the trade, its age is within the versioned `max_quote_age_us`, and the venue is not `LOCKED`.

For a usable quote:

- trade price `>= best_ask` → `BUY_AGGRESSOR`, method `QUOTE_TEST`;
- trade price `<= best_bid` → `SELL_AGGRESSOR`, method `QUOTE_TEST`;
- price strictly inside the spread → `UNKNOWN`, method `NONE`.

A quote that exists but is future, stale, locked, or otherwise unusable degrades to `UNKNOWN`. It must **not** trigger tick-rule fallback. This prevents future quote backfill and permissive recovery from invalid quote state.

Tick-rule fallback is allowed only when quote data is genuinely unavailable and the policy enables it. With a causally prior trade:

- current price greater than previous → `BUY_AGGRESSOR`;
- current price lower than previous → `SELL_AGGRESSOR`;
- equal price → `UNKNOWN`.

No previous trade means `UNKNOWN`.

## Confidence semantics

`AggressorConfidenceStateV1` is descriptive method-quality metadata, **not a probability and not the Lot 46 Trade Classification Confidence Engine**.

Policy `lot44-aggressor-confidence-v1`:

- quote-test classification: `1`;
- tick-rule fallback: `0.5`;
- unknown/degraded: `0`.

The semantic label is `DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY`.

## Reference fixture result

Lot 38 best bid/ask is `50024.9 / 50025.1`. Lot 37 trades are:

1. `fixture-trade-001`, price `50025.00`, quantity `0.05` → `UNKNOWN`;
2. `fixture-trade-002`, price `50025.10`, quantity `0.08` → `BUY_AGGRESSOR`;
3. `fixture-trade-003`, price `50024.90`, quantity `0.03` → `SELL_AGGRESSOR`.

Reference conservation:

- total volume `0.16`;
- buy `0.08`;
- sell `0.03`;
- unknown `0.05`;
- `unknown_volume_ratio = 0.3125`.

Unknown volume is never discarded or reassigned.

## Outputs

- `TradesAggressorClassificationSchemaStateV1`
- `TradesAggressorClassificationSchemaAuditV1`
- `ClassifiedTradeV1`
- `AggressorConfidenceStateV1`

All contracts are deterministic, checksum-bound and fail-closed.

## Explicit non-goals

Lot 44 does not implement or compute:

- Order Flow / Delta / CVD (Lot 45);
- Trade Classification Confidence Engine (Lot 46);
- absorption, hidden liquidity, volume clusters, stop zones, sweeps/fakeouts/traps;
- participant identity or intent as fact;
- forecast, signal, risk approval, routing, trading or execution;
- external network access, live exchange access or credentials.

Safety remains `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.
