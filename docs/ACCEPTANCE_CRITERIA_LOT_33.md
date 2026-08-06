# Lot 33 — Acceptance Criteria

## Contract and lineage

- [ ] Entry-gate checksum is recomputed and immutable.
- [ ] Lot 32 instrument registry, state and audit file hashes are exact.
- [ ] Unknown instrument or source identifiers are rejected.
- [ ] State, audit and standalone collection are linked by checksum/content.

## Timestamp governance

- [ ] Every wall-clock timestamp is timezone-aware.
- [ ] The declared IANA timezone agrees with the raw timestamp offset.
- [ ] Raw timestamp, timezone and precision are preserved.
- [ ] Canonical timestamps are UTC with exact declared precision.
- [ ] Seconds, milliseconds and microseconds are supported explicitly.
- [ ] Timezone-naive, malformed or precision-inconsistent values are rejected.
- [ ] DST fold offsets map to distinct deterministic UTC instants.

## Causality and ordering

- [ ] `event <= receive <= process <= available_at <= usable_from`.
- [ ] Negative latency is rejected.
- [ ] Equal event timestamps are ordered by sequence and revision IDs.
- [ ] Duplicate record/order keys are rejected.
- [ ] Late arrivals produce exact non-negative out-of-order delay.
- [ ] Revisions remain explicit and auditable.
- [ ] Monotonic time and clock domain are either both valid or explicitly absent.

## Clock health

- [ ] Thresholds are versioned and use integer microseconds.
- [ ] Healthy fixture observations are exact.
- [ ] Each exceeded threshold yields `DEGRADED`.
- [ ] Degraded state does not enable any permission.
- [ ] Unknown threshold/config state fails closed.

## Determinism and persistence

- [ ] Two builds on the same commit are byte-identical.
- [ ] State and audit SHA-256 values recompute independently.
- [ ] Atomic persistence never accepts partial output.
- [ ] Serialization/deserialization preserves every contract field.
- [ ] Three anti-flake repetitions pass.

## Quality gates

- [ ] Targeted line coverage >= 95%.
- [ ] Targeted branch coverage >= 90%.
- [ ] Targeted mutation score >= 80%.
- [ ] No new engineering-deviation finding.
- [ ] Ruff, mypy, Bandit and dependency audit pass when runners are available.
- [ ] Full repository regression passes when runners are available.

## Safety and promotion

- [ ] No forbidden network import or secret-like configuration key.
- [ ] All fail-closed fields retain their exact values.
- [ ] No market event, quality score, signal, risk decision or execution path exists.
- [ ] Lot 34 remains `PLANNED_LOCKED` and `implementation_started=false`.
- [ ] A separate post-merge audit is required before the Lot 34 entry gate.
