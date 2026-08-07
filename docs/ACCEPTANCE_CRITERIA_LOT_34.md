# Lot 34 — Acceptance Criteria

## Contract and lineage

- [ ] Exact Lot 34 entry-gate checksum is recomputed and valid.
- [ ] Lot 33 state/audit lineage is exact and certified.
- [ ] Canonical-time collection is referenced by checksum.
- [ ] State, audit and standalone quality/anomaly/veto artifacts are mutually consistent.

## Quality detection

- [ ] Missing intervals are detected with configured timeframe boundaries.
- [ ] Duplicate event identity is detected.
- [ ] Out-of-order arrival is detected from event/sequence/revision order.
- [ ] Stale data is detected with exact integer-microsecond timing.
- [ ] Invalid OHLC relationships are detected.
- [ ] Negative volume is detected.
- [ ] Impossible spread is detected while an equal bid/ask boundary is accepted.
- [ ] Schema field/version drift is detected.
- [ ] Each anomaly family has positive, negative and boundary tests.

## Scoring and veto

- [ ] Coverage, freshness, completeness and consistency are integer basis-point scores.
- [ ] Aggregate quality score is deterministic and versioned by configuration.
- [ ] Unknown quality blocks analysis/trading.
- [ ] Any blocking anomaly blocks analysis/trading.
- [ ] Score below threshold blocks analysis/trading.
- [ ] Healthy quality can allow analysis only; it never authorizes trading.

## Non-destructive quarantine

- [ ] Every anomaly is quarantined by raw record reference.
- [ ] `correction_permitted=false` for every Lot 34 anomaly.
- [ ] Raw input objects are unchanged by detection.
- [ ] No raw edit/fill/round/delete path exists.

## Numeric and temporal integrity

- [ ] Prices/volumes use explicit decimal strings and `Decimal`.
- [ ] Timing uses integer microseconds; no float timing coercion.
- [ ] `available_at < event_time` fails closed.
- [ ] Unknown timeframe interval fails closed.
- [ ] Malformed decimal/timestamp/config values fail closed.

## Determinism and persistence

- [ ] Same inputs/config/commit produce byte-identical five output artifacts.
- [ ] State and audit checksums recompute independently.
- [ ] Atomic persistence is used.
- [ ] Three targeted anti-flake repetitions pass.

## Quality gates

- [ ] Targeted line coverage >= 95%.
- [ ] Targeted branch coverage >= 90%.
- [ ] Targeted mutation score >= 80%.
- [ ] Ruff and mypy pass.
- [ ] Bandit and dependency audit pass.
- [ ] Architecture, roadmap, traceability and silent numeric coercion checks pass.
- [ ] Full repository regression passes.

## Safety and promotion

- [ ] No forbidden network import or credential path.
- [ ] External connectivity and network ingestion remain false.
- [ ] Raw-data mutation and market-event publication remain false.
- [ ] Signal, risk approval, routing, trading and execution remain false.
- [ ] `approved_size=0`.
- [ ] Lot 35 remains locked before the independent Lot 34 post-merge audit.
