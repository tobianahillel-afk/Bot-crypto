# Acceptance Criteria — Lot 36

## Entry and scope

- [ ] Lot 36 entry gate checksum is exact and `GO_LOT36_IMPLEMENTATION_ENTRY`.
- [ ] Canonical roadmap blob SHA is `84de51bda788a8d124fb7d344419c4a4b12030b5` and line 37 is the authoritative Lot 36 record.
- [ ] Owner/runtime remain `MarketDataGovernanceDomain` / `DATA_GOVERNANCE_ONLY`.
- [ ] No external connectivity, live data, real credentials, raw mutation, V4 capability, forecast, signal, risk approval, order, trading or execution code is added.

## Deterministic predecessor evidence

- [ ] Lot 34 is replayed with its certified implementation commit and state/audit checksums match exactly.
- [ ] Lot 35 is replayed with its certified implementation commit and state/audit checksums match exactly.
- [ ] The eight Lot 34 anomaly families are re-audited through the Lot 34-owned detector, not duplicated.
- [ ] Certified Lot 35 reconciliation veto is consumed without bypass or reinterpretation.

## Freshness, gap and outage

- [ ] Records are grouped by canonical `(source_id, instrument_id, timeframe)`.
- [ ] Ordering is deterministic and independent of input order.
- [ ] Durations use exact integer microseconds.
- [ ] Expected/observed/missing interval counts follow the normative formula.
- [ ] Gap boundary is strictly `delta > interval`.
- [ ] Outage boundary is `delta >= outage_interval_multiplier * interval`.
- [ ] Freshness uses `latest_available_at`, not event time alone.
- [ ] Future availability relative to the reference time is rejected.
- [ ] Missing, stale, gap, outage or unknown quality blocks closure.

## Data quality and reconciliation veto

- [ ] Quality state is known and meets the configured minimum before `ALLOW_ANALYSIS`.
- [ ] Any anomaly forces `BLOCK_ANALYSIS_OR_TRADING`.
- [ ] Any non-PASS freshness evidence forces `BLOCK_ANALYSIS_OR_TRADING`.
- [ ] Lot 35 `PAUSE`/`KILL_SWITCH` consequence blocks the closure candidate.
- [ ] No technical score is interpreted as probability or trading permission.

## Closure contracts

- [ ] `FreshnessGapOutageAuditV3ClosureStateV1` is versioned and checksummed.
- [ ] `FreshnessGapOutageAuditV3ClosureAuditV1` links state/config/manifest and prior lot checksums.
- [ ] `ReplayEvidenceV1` proves run1/run2 equality or records divergence.
- [ ] `LotValidationReportV1` covers Lots 31–36.
- [ ] `ClosureManifestV1` covers Lots 31–36 and keeps Lot37 locked.
- [ ] Implementation manifest has `v3_closed=false`.
- [ ] Implementation manifest requires independent post-merge audit and human review.
- [ ] Existing `DataQualityStateV1`, `DataAnomalyV1` and `DataQualityVetoV1` contracts are reused.

## Persistence and auditability

- [ ] State, audit, quality states, anomalies, veto, replay and manifest persist atomically.
- [ ] Every critical checksum recomputes from canonical JSON.
- [ ] Lineage includes entry gate, canonical roadmap and Lot34/Lot35 state/audit checksums.
- [ ] Stable reason codes explain PASS/BLOCKED decisions.
- [ ] Config version and config checksum are bound to the audit.
- [ ] Raw input remains byte/logically unchanged after audit.

## Tests and negative cases

- [ ] Reference fixture produces a closure candidate, not final V3 closure.
- [ ] Missing interval injection is detected.
- [ ] Duplicate injection is detected.
- [ ] Out-of-order injection is detected.
- [ ] Stale-data injection is detected.
- [ ] Invalid OHLC injection is detected.
- [ ] Negative-volume injection is detected.
- [ ] Impossible-spread injection is detected.
- [ ] Schema-drift injection is detected.
- [ ] Gap and exact outage boundaries have regression tests.
- [ ] Input reversal produces identical freshness evidence.
- [ ] Serialization is deterministic.
- [ ] Run1/run2 produces identical state checksum.
- [ ] Complete Lots31–36 validator chain passes.
- [ ] Connectivity validator passes.

## Engineering and CI gates

- [ ] Ruff PASS.
- [ ] Mypy PASS for the V3 package.
- [ ] Architecture/ownership/roadmap/traceability PASS.
- [ ] Engineering inventory/deviation gate PASS with no new unowned deviation.
- [ ] Targeted line coverage >= 95%.
- [ ] Targeted branch coverage >= 90%.
- [ ] Targeted mutation score >= 80%.
- [ ] Full repository regression PASS.
- [ ] Targeted anti-flake repetitions x3 PASS.
- [ ] Bandit PASS.
- [ ] Dependency audit PASS.
- [ ] Exact-head CI is fully green before merge.

## Promotion

- [ ] Implementation is squash-merged only after all exact-head gates pass.
- [ ] Independent post-merge Lot36 audit is opened on the merged commit.
- [ ] V3 is not marked closed before that audit returns GO.
- [ ] Lot37 remains `PLANNED_LOCKED` until the separate post-merge promotion decision.
