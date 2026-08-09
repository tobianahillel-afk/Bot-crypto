# Lot 36 — Freshness, Gap, Outage Audit & V3 Closure

## 1. Identity, version, status, runtime

- Version family: `V3_MARKET_DATA_GOVERNANCE`
- Lot: `36`
- Canonical title: `Freshness, Gap, Outage Audit & V3 Closure`
- Owner: `MarketDataGovernanceDomain`
- Package boundary: `src/crypto_quant_bot/data_governance`
- Runtime: `DATA_GOVERNANCE_ONLY`
- Entry gate: `GO_LOT36_IMPLEMENTATION_ENTRY`
- Entry gate checksum: `ccddc668b83267effb6e82827c6a0f1f8d5879803f7d3e5cc6f9cfc745ba78a5`
- Lot 37: `PLANNED_LOCKED`

## 2. Falsifiable objective and owner

Lot 36 must deterministically prove whether the certified V3 market-data-governance chain is a valid
**closure candidate** at one immutable offline reference point. It is successful only when freshness,
gaps, outages, Lot 34 quality evidence, Lot 35 reconciliation evidence and exact replay all agree.
Any unknown, stale, incompatible or divergent prerequisite blocks the candidate.

`MarketDataGovernanceDomain` is the sole owner of this result.

## 3. Scope, non-goals, forbidden capability

In scope:

- freshness/gap/outage audit;
- deterministic replay of certified Lot 34 and Lot 35 builders;
- re-audit of the eight Lot 34 anomaly families using the Lot 34 public detector;
- immutable lineage to the canonical roadmap and prior lot checksums;
- V3 chain validation for Lots 31–36;
- closure-candidate manifest;
- fail-closed quality veto;
- atomic evidence persistence.

Out of scope and forbidden:

- network access, live exchange data or real credentials;
- raw-data correction or mutation;
- reimplementation of Lot 34 or Lot 35 algorithms;
- V4 microstructure or later-version capability;
- forecast, signal, risk approval, order routing, trading or execution;
- declaring `v3_closed=true` inside the implementation PR.

## 4. Input contracts

Lot 36 consumes only versioned, immutable inputs:

- `data/audit/lot36_v3_entry_gate.json`;
- canonical roadmap blob `84de51bda788a8d124fb7d344419c4a4b12030b5`, line 37;
- Lot 34 certified quality state/audit/config and public detector/builder;
- Lot 35 certified reconciliation state/audit and public builder;
- `freshness-gap-outage-v3-closure-config-v1`.

The reference fixture remains offline Kraken BTC/EUR 1m data. Input order is not authoritative.

## 5. Output contracts

Canonical outputs:

1. `FreshnessGapOutageAuditV3ClosureStateV1`;
2. `FreshnessGapOutageAuditV3ClosureAuditV1`;
3. `ReplayEvidenceV1`;
4. `LotValidationReportV1`;
5. `ClosureManifestV1`;
6. `DataQualityStateV1` (Lot 34-owned contract, reused);
7. `DataAnomalyV1` (Lot 34-owned contract, reused);
8. `DataQualityVetoV1` (Lot 34-owned contract, reused).

Each critical persisted payload is versioned, deterministic and checksummed.

## 6. Entry gates

Implementation must refuse to run unless:

- gate checksum and `GO_LOT36_IMPLEMENTATION_ENTRY` match;
- gate base is the independently audited Lot 35 state;
- canonical roadmap Git blob and Lot 36 record identity match;
- historical lifecycle says latest implemented lot is 35 and Lot 36 was locked;
- all safety fields remain fail-closed.

## 7. Ordered processing

1. Verify the Lot 36 entry gate.
2. Verify the canonical roadmap blob and record.
3. Verify historical lifecycle evidence.
4. Validate the versioned Lot 36 config.
5. Replay Lot 34 with its certified implementation commit; compare state/audit checksums.
6. Replay Lot 35 with its certified implementation commit; compare state/audit checksums.
7. Re-run the Lot 34 public anomaly detector on the immutable certified quality input.
8. Compute Lot 36 freshness/gap/outage evidence.
9. Build a fail-closed data-quality veto.
10. Combine quality and reconciliation consequences.
11. Build the Lots31–36 validation report and closure-candidate manifest.
12. Compute canonical state/audit checksums.
13. Execute run1/run2 replay and compare exact checksums.
14. Persist state, audit, quality collection, anomaly collection, veto, replay and manifest atomically.

## 8. Mathematical specification

For one `(source_id, instrument_id, timeframe)` group, let ordered unique event timestamps be
`t_0 < ... < t_n` and configured interval `Δ > 0` microseconds.

```text
expected_interval_count = floor((t_n - t_0) / Δ) + 1
observed_interval_count = count(unique event timestamps)
missing_interval_count = max(expected_interval_count - observed_interval_count, 0)
gap_i = 1[(t_i - t_{i-1}) > Δ]
outage_i = 1[(t_i - t_{i-1}) >= outage_interval_multiplier * Δ]
```

Freshness uses causal availability, never event time alone:

```text
freshness_age_us = freshness_reference_time - latest_available_at
stale = freshness_age_us > max_staleness_seconds * 1_000_000
```

All durations are exact integer microseconds. No binary floating-point duration arithmetic is
permitted. A future `latest_available_at` relative to the reference time is invalid rather than
silently clamped.

Lot 36 does not invent a new probabilistic score. It reuses the Lot 34 `freshness_bps` evidence and
sets closure freshness evidence to zero only when the latest data is stale or quality state is
unknown. Basis points remain in `[0, 10000]`.

## 9. Business and algorithm rules

A freshness group is `PASS` only when:

- matching Lot 34 quality state exists and is `PASS`;
- missing intervals = 0;
- gaps = 0;
- outages = 0;
- latest data is not stale.

The closure quality veto is `ALLOW_ANALYSIS` only when quality is known, minimum quality is met,
no anomaly is present and every freshness group passes. Otherwise it is
`BLOCK_ANALYSIS_OR_TRADING`.

The V3 closure candidate is ready only when both the closure quality veto and Lot 35 reconciliation
veto allow analysis and every freshness audit passes.

## 10. State machine

```text
ENTRY_UNVERIFIED
  -> BLOCKED_V3_CLOSURE          on invalid/unknown prerequisite
  -> VALIDATED_V3_CLOSURE_CANDIDATE on all deterministic closure invariants PASS
```

A validated candidate does **not** transition to final V3 closure inside this implementation.
Final closure requires an independent post-merge audit and human review.

## 11. Failures and degraded behavior

- Missing/incompatible schema: fail closed, no valid closure output.
- Missing quality state: `UNKNOWN/BLOCKED` consequence.
- Stale data: block.
- Gap/outage: block.
- Lot 34 or 35 checksum divergence: fail closed.
- Quality/reconciliation veto: block.
- Run1/run2 checksum mismatch: `REPLAY_DIVERGENCE` / non-deterministic failure.
- Future availability relative to reference: reject.
- Unclassified exception: no valid closure certification.

No failure path enables trading or execution.

## 12. Expected files, functions, scripts and artifacts

Required implementation surface includes:

- `freshness_gap_outage_audit_and_v3_closure.py`;
- `freshness_gap_outage_audit_and_v3_closure_models.py`;
- `freshness_gap_outage_audit_and_v3_closure_validation.py`;
- versioned JSON schemas;
- `run_lot36_freshness_gap_outage_audit_and_v3_closure.py`;
- `validate_lot36.py` and `validate_lot36_no_connectivity.py`;
- `validate_all_until_lot36.py`;
- `diagnose_exact_chain_until_lot36.py`;
- `run_required_chain_until_lot36.sh`;
- Lot 36 tests, evidence artifacts, report and acceptance criteria.

## 13. Configuration

`config/data_governance/freshness_gap_outage_v3_closure_v1.json` owns all Lot 36 thresholds:

- `max_staleness_seconds`;
- `outage_interval_multiplier`;
- freshness reference time;
- required lots;
- immutable path to the certified Lot 34 quality config.

No hidden business threshold is permitted in implementation code.

## 14. Observability

Metrics include:

- records processed;
- validation failures;
- gap count;
- outage count;
- stale latest-record count;
- anomaly count;
- exact processing latency in microseconds.

Stable reason codes accompany freshness evidence, state, veto, replay and manifest.

## 15. Auditability

Evidence must reconstruct:

- code commit;
- gate checksum;
- canonical roadmap Git blob;
- Lot 34 and Lot 35 state/audit checksums;
- config checksum;
- state/audit/manifest/replay checksums;
- timestamps and causal availability;
- quality/reconciliation veto actions;
- Lots31–36 validation coverage;
- safety state and next-lot lock.

## 16. Test mapping

Tests must cover:

- reference PASS candidate;
- exact gap and outage boundaries;
- stale latest data;
- future-state rejection;
- input-order independence;
- deterministic serialization/replay;
- raw-input immutability;
- all eight Lot 34 anomaly families;
- anomaly-to-veto fail-closed consequence;
- schema incompatibility;
- Lot37 lock and no premature final V3 closure;
- full historical V3 chain.

Every bug discovered during review receives a permanent regression test.

## 17. Coverage, branch and mutation quality

Mandatory implementation PR gates:

```text
line coverage >= 95%
branch coverage >= 90%
mutation score >= 80%
anti-flake repetitions = 3
```

Coverage is evidence, not correctness proof. Mutation and negative tests remain mandatory.

## 18. Performance and complexity

Lot 36 is offline and bounded by the certified fixture/data set. Processing must be deterministic,
memory-bounded for configured input, and free of unbounded retry. Engineering defaults remain:
function <= 50 logical lines, cyclomatic complexity <= 10, nesting <= 4 and module <= 800 lines.
Any deviation requires explicit registered governance; new Lot 36 code should instead be refactored.

## 19. Migration and rollback

Lot 36 introduces additive contracts and artifacts only. Rollback removes the Lot 36 implementation
commit and restores the gate-only main state. Prior Lot 31–35 artifacts are immutable and are never
rewritten by rollback.

## 20. Risks and debt

Primary risks:

- confusing event freshness with availability freshness;
- duplicating Lot 34 anomaly logic;
- treating technical PASS as final V3 closure;
- allowing later-lot scope to leak into the closure layer;
- embedding mutable current-head values into historical evidence.

Mitigations are encoded as tests, canonical lineage and post-merge audit requirements. No critical
known debt is accepted at GO.

## 21. Definition of Done

Lot 36 implementation is eligible for merge only when:

- canonical contracts and artifacts exist;
- reference candidate and negative paths pass;
- run1/run2 replay matches;
- complete V3 chain validators pass;
- line/branch/mutation/anti-flake gates pass;
- architecture, engineering, security and dependency gates pass;
- no review blocker/major remains;
- exact-head CI is green;
- Lot37 remains locked.

## 22. Final audit

After implementation merge, a separate governance-only PR must independently re-run and verify the
merged Lot 36 state, exact CI evidence, checksums, replay, chain continuity, safety and documentation.
Only that audit may decide whether V3 is finally closed.

A green implementation CI alone is never the final V3 closure verdict.

## 23. Promotion and next-lot lock

During implementation:

```text
closure_status=CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT
v3_closed=false
lot37_status=PLANNED_LOCKED
```

Lot 37 cannot receive an implementation entry gate until the independent Lot 36 post-merge audit
returns GO, freezes the merged evidence and explicitly authorizes the V3→V4 transition boundary.
