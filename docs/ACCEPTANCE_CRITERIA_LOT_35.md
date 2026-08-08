# Acceptance Criteria — Lot 35 Candle / Trade / Book Reconciliation

## Functional

- [ ] `CANDLE`, `TRADE` and `BOOK` reference records are reconciled deterministically.
- [ ] Exact equality yields `MATCH`.
- [ ] Non-zero deltas inside versioned tolerances yield `TOLERATED_DIFF`.
- [ ] Deltas above tolerance but within the critical multiplier yield `MINOR_DIVERGENCE`.
- [ ] Deltas above the critical boundary yield `CRITICAL_DIVERGENCE`.
- [ ] Identifier mismatch is critical.
- [ ] Orphan source is critical and has no fabricated delta.
- [ ] Duplicate reconciliation id is at least minor.
- [ ] Unknown source ownership is critical.
- [ ] Fee divergence above tolerance triggers a pause reason.

## Numerical and temporal

- [ ] Decimal fields use `Decimal`, never binary floating point.
- [ ] All five decimal deltas are absolute and exact.
- [ ] Timestamp delta is integer microseconds.
- [ ] Tolerance and critical boundaries are inclusive and tested.
- [ ] `event_time <= available_at <= generated_at` is enforced.

## Contracts and persistence

- [ ] `CandleTradeBookReconciliationStateV1` is emitted.
- [ ] `CandleTradeBookReconciliationAuditV1` is emitted.
- [ ] `ReconciliationReportV1` collection is emitted.
- [ ] `ReconciliationVetoV1` is emitted.
- [ ] State and audit checksums recompute exactly.
- [ ] Persistence is atomic.
- [ ] Run1 and run2 produce byte-identical artifacts for equal inputs and code commit.

## Safety

- [ ] `analysis_only=true`.
- [ ] `used_for_decision=false`.
- [ ] `external_connectivity_allowed=false`.
- [ ] `network_ingestion_allowed=false`.
- [ ] `real_credentials_allowed=false`.
- [ ] `market_event_publication_allowed=false`.
- [ ] `raw_data_mutation_allowed=false`.
- [ ] `signal_generation_allowed=false`.
- [ ] `risk_approval_allowed=false`.
- [ ] `order_routing_allowed=false`.
- [ ] `trade_allowed=false`.
- [ ] `execution_allowed=false`.
- [ ] `approved_size=0`.
- [ ] No forbidden network import exists in Lot 35 production modules.

## Lineage

- [ ] Lot 35 entry-gate checksum is verified.
- [ ] Lot 34 state checksum is verified.
- [ ] Lot 34 audit checksum is verified.
- [ ] Lot 34 quality/anomaly/veto collection hashes are linked.
- [ ] Certified Lot 34 anomaly collection remains empty for the reference fixture.
- [ ] Lot 34 quality veto remains `ALLOW_ANALYSIS` for the reference fixture.

## Quality gates

- [ ] Ruff PASS.
- [ ] mypy PASS.
- [ ] architecture / ownership PASS.
- [ ] roadmap semantics PASS.
- [ ] traceability PASS.
- [ ] silent numeric coercion gate PASS.
- [ ] engineering inventory/deviation gate PASS.
- [ ] line coverage >= 95%.
- [ ] branch coverage >= 90%.
- [ ] mutation score >= 80%.
- [ ] anti-flake repetition x3 PASS.
- [ ] Bandit PASS.
- [ ] dependency audit PASS.
- [ ] full repository regression PASS.

## Promotion

- [ ] PR merged only from exact green head.
- [ ] Independent post-merge audit performed on exact merge commit.
- [ ] Lot 36 remains `PLANNED_LOCKED` until a separate entry gate.
