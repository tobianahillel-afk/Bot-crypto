# Lot 35 — Candle / Trade / Book Reconciliation

## 1. Identity

- Version family: V3 Market Data Governance
- Lot: 35
- Owner: `MarketDataGovernanceDomain`
- Runtime mode: `DATA_GOVERNANCE_ONLY`
- Entry gate: `data/audit/lot35_v3_entry_gate.json`
- Entry gate checksum: `e3ca9847c39a9ab8a043639cda556308506e9d5a497eb7821d3b962278c507ab`

## 2. Falsifiable objective

Given two explicitly declared offline representations of the same candle, trade or book item,
Lot 35 computes exact deltas, applies versioned tolerances, produces one deterministic
classification and emits a fail-closed reconciliation veto. The lot succeeds only if run1 and
run2 are byte-identical for the same code/config/evidence inputs.

## 3. Scope

- identifiers;
- quantity, price and fee deltas;
- balance and position deltas;
- event timestamp deltas in integer microseconds;
- explicit source-of-truth declaration;
- `MATCH`, `TOLERATED_DIFF`, `MINOR_DIVERGENCE`, `CRITICAL_DIVERGENCE`;
- orphan and duplicate detection;
- typed reconciliation report and veto;
- deterministic persistence and replay.

## 4. Non-goals

- no source repair or mutation;
- no live exchange reconciliation;
- no order submission;
- no continuous state publication;
- no forecast, signal, risk approval or trading decision.

## 5. Forbidden scope

The exact forbidden scope remains the Lot 35 gate set: external network, live exchange data,
real credentials, destructive correction, Lot 34 reimplementation, Lot 36 closure,
continuous market-state publication, forecast/signal/risk/order/trading/execution.

## 6. Input contracts

The reference configuration is `config/data_governance/candle_trade_book_reconciliation_v1.json`.
Each reconciliation item contains:

```text
reconciliation_id
entity_type = CANDLE | TRADE | BOOK
source_of_truth = PRIMARY | SECONDARY | UNKNOWN
primary = ReconciliationSnapshotV1 | null
secondary = ReconciliationSnapshotV1 | null
```

A snapshot carries an immutable record id, logical identifier, quantity, price, fee, balance,
position and UTC event time. Numeric source values remain decimal strings.

## 7. Output contracts

- `CandleTradeBookReconciliationStateV1`
- `CandleTradeBookReconciliationAuditV1`
- `ReconciliationReportV1`
- `ReconciliationVetoV1`

Collections are persisted under `data/audit/` and contain no reconstructed source values.

## 8. Entry gates

Before computation, the implementation verifies:

- immutable Lot 35 entry-gate checksum;
- current Lot 34 certified state/audit checksum;
- anomaly collection is empty for the reference evidence;
- Lot 34 veto is `ALLOW_ANALYSIS`;
- Lot 34 raw mutation remains forbidden;
- Lot 36 is not implemented by this lot.

## 9. Ordered processing

1. validate gate and certified Lot 34 evidence;
2. validate config identity, causal timestamps and tolerances;
3. validate each source snapshot without coercive defaults;
4. detect duplicate reconciliation ids;
5. detect orphan and unknown-ownership states;
6. compute exact deltas;
7. classify each reconciliation item;
8. resolve the aggregate veto with the canonical consequence priority;
9. build state and audit with lineage and checksums;
10. persist all four artifacts atomically.

## 10. Mathematical specification

For decimal field `x`:

```text
Delta_x = abs(x_primary - x_secondary)
```

All source values are parsed with `Decimal`. No binary floating-point arithmetic is used.

For timestamps:

```text
Delta_t_us = abs(t_secondary - t_primary)
```

The duration is computed from integer days, seconds and microseconds.

Given versioned tolerance `tau_x` and integer critical multiplier `k >= 1`:

```text
MATCH               iff every Delta = 0
TOLERATED_DIFF      iff every Delta <= tau and at least one Delta > 0
MINOR_DIVERGENCE    iff not tolerated and every Delta <= k * tau
CRITICAL_DIVERGENCE otherwise
```

Identifier mismatch, orphan source or unknown source ownership is always critical. Duplicate
reconciliation ids are at least minor.

## 11. Business and algorithm rules

- identifier equality is exact;
- tolerance equality is inclusive;
- a fee delta above its normal tolerance is at least minor and emits
  `RECONCILIATION_FEE_DIFF_REQUIRES_PAUSE`;
- the implementation never selects, edits or overwrites a source value;
- source-of-truth is recorded, not inferred silently;
- absence of a source never creates a synthetic delta.

## 12. State machine

Per item:

```text
VALIDATED_INPUT
  -> MATCH
  -> TOLERATED_DIFF
  -> MINOR_DIVERGENCE
  -> CRITICAL_DIVERGENCE
```

Aggregate consequence:

```text
critical present -> KILL_SWITCH
else minor present -> PAUSE
else -> ALLOW_ANALYSIS
```

These labels are governance evidence only. `trade_allowed=false` and
`execution_allowed=false` remain invariant.

## 13. Failure behavior

- malformed config or schema -> no valid state;
- invalid decimal/timestamp -> no valid state;
- both sources absent -> no valid state;
- one source absent -> critical report;
- duplicate id -> minor report and pause;
- unknown ownership -> critical report;
- unexplained large difference -> critical report;
- upstream Lot 34 evidence changed -> no valid state.

## 14. Files and artifacts

Production:

- `src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation.py`
- `src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation_models.py`
- `src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation_validation.py`

Execution and validation:

- `scripts/run_lot35_candle_trade_book_reconciliation.py`
- `scripts/validate_lot35.py`
- `scripts/validate_lot35_no_connectivity.py`

Evidence:

- `data/audit/candle_trade_book_reconciliation_lot35.json`
- `data/audit/candle_trade_book_reconciliation_audit_lot35.json`
- `data/audit/reconciliation_reports_lot35.json`
- `data/audit/reconciliation_veto_lot35.json`

## 15. Configuration

Configuration is typed by validation and versioned as
`lot35-candle-trade-book-reconciliation-config-v1`. Business tolerances have an explicit
`tolerance_version`; no hidden threshold is permitted.

## 16. Observability

Metrics include processed reports, validation failures, counts for each classification and
processing latency. The deterministic reference uses zero synthetic processing latency rather
than wall-clock timing.

## 17. Auditability

State and audit bind:

- `run_id`, `correlation_id`, code commit and config version;
- exact Lot 34 state/audit checksums;
- exact file checksums of Lot 34 quality/anomaly/veto collections;
- every reconciliation report, reason code and veto;
- final state/audit checksum.

## 18. Test mapping

Tests cover:

- all four classifications;
- equality at tolerance and critical boundaries;
- all decimal delta fields;
- timestamp boundaries;
- identifier mismatch;
- orphan, duplicate and unknown ownership;
- fee divergence;
- invalid schemas/config/timestamps/tolerances;
- persistence and replay;
- no connectivity;
- checksum and safety invariants.

## 19. Coverage and mutation

Required:

```text
line >= 95%
branch >= 90%
mutation >= 80%
anti-flake repetitions = 3
```

Coverage and mutation apply to all three Lot 35 production modules.

## 20. Performance and complexity

The reference algorithm is linear in reconciliation record count aside from deterministic
sorting. No unbounded retry, external I/O or concurrency is introduced. Functions/classes
remain under the repository engineering limits or the CI fails.

## 21. Migration and rollback

Lot 35 introduces additive contracts/files only. Rollback removes Lot 35 artifacts and source
while retaining the Lot 35 entry gate and all Lot 34 evidence. No historical Lot 34 artifact is
rewritten.

## 22. Risks and debt

The reference fixture is deliberately small and offline. It proves deterministic mechanics,
not exchange correctness or economic value. Live reconciliation belongs to later governed
runtime stages and is forbidden here.

## 23. Definition of done / promotion

Lot 35 is not `IMPLEMENTED_VALIDATED` until:

- all required CI workflows pass on the exact PR head;
- coverage, mutation and anti-flake gates pass;
- run1/run2 are deterministic;
- full regression, architecture, traceability and security gates pass;
- the implementation PR is merged;
- an independent post-merge audit certifies the exact merge commit.

Lot 36 remains `PLANNED_LOCKED` until that post-merge audit and a distinct Lot 36 entry gate.
