# Lot 33 — Timestamp, Clock & Timezone Governance

## Status

`IMPLEMENTATION_IN_PROGRESS_OFFLINE_ONLY`

## Responsibility

Lot 33 is the sole owner of deterministic timestamp, clock and timezone governance inside
`MarketDataGovernanceDomain`. It consumes only the certified offline Lot 32 instrument
registry and produces no live market event.

## Inputs

- immutable Lot 33 entry gate;
- `InstrumentRegistryV1` and exact Lot 32 state/audit lineage;
- versioned offline temporal configuration;
- explicit aware raw timestamp envelopes.

## Outputs

- `RawTimestampEnvelopeV1`;
- `CanonicalTimeEnvelopeV1`;
- `ClockHealthStateV1`;
- `TimestampClockTimezoneGovernanceStateV1`;
- `TimestampClockTimezoneGovernanceAuditV1`;
- standalone canonical-envelope collection.

## Canonical timestamp contract

Each record preserves:

```text
raw_timestamp
source_timezone
timestamp_precision
source_time
exchange_time
event_time
receive_time
process_time
available_at
usable_from
monotonic_time
clock_domain
sequence_id
revision_id
```

Wall-clock timestamps are ISO-8601 and timezone-aware. The raw offset must be valid for the
explicit IANA timezone at that instant. Canonical values are UTC and retain the declared
seconds, milliseconds or microseconds precision.

## Causal availability

```text
event_time <= receive_time <= process_time <= available_at <= usable_from
```

A record is never usable before `available_at`. A negative transport, processing or total
latency is rejected. Unknown or contradictory time state produces no valid output.

## Exact duration arithmetic

All durations use integer microseconds:

```text
clock_drift_us
transport_latency_us
processing_latency_us
total_latency_us
out_of_order_delay_us
```

Binary floating-point duration coercion is forbidden.

## Ordering

Canonical ordering is:

```text
(event_time_utc, sequence_id, revision_id)
```

Equal event timestamps therefore remain deterministic. Input-order late arrival is measured
against the maximum prior event time and does not rewrite the raw record.

## Clock health

Versioned configuration defines:

- `max_clock_drift_us`;
- `max_out_of_order_delay_us`;
- `max_total_latency_us`.

The certified state is `HEALTHY` when all observations stay within their limits. Exceeding a
limit yields `DEGRADED`; it never grants analysis or trading permission. Invalid or unknown
contract state is rejected fail-closed.

## DST and timezone rules

Ambiguous local wall times are accepted only when the raw timestamp includes an explicit
offset that is valid for the declared IANA timezone. Both sides of a DST fold remain distinct
UTC instants. Nonexistent or offset-inconsistent local timestamps are rejected.

## Persistence

State, audit and canonical-envelope collection are written atomically. The state and audit use
canonical SHA-256 checksums and bind to exact Lot 32 file hashes and the implementation Git
commit.

## Certified fixture

The initial fixture contains three metadata-only records for the certified `BTC/EUR:SPOT`
instrument:

- Bitstamp record with `Europe/Paris` `+02:00` source time;
- Coinbase record sharing the same event timestamp but using `sequence_id=2`;
- Kraken record arriving late and producing an auditable out-of-order delay.

No value is fetched from an exchange at runtime.

## Non-goals

- no network connector or live metadata fetch;
- no market-event publication;
- no Lot 34 quality score or veto;
- no candle/trade/book reconciliation;
- no forecast, probability, signal or TradeIntent;
- no risk approval, reservation, order or execution.

## Safety

```text
runtime_mode=DATA_GOVERNANCE_ONLY
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

Lot 34 remains `PLANNED_LOCKED` until Lot 33 is merged and independently audited.
