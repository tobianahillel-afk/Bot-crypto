# Lot 32 — Acceptance Criteria

## Functional contracts

- [ ] `InstrumentSpecificationV1`, `InstrumentRegistryV1`, state and audit schemas exist and reject additional properties.
- [ ] The certified registry contains exactly one canonical `BTC/EUR:SPOT` instrument and three versioned venue aliases.
- [ ] Canonical-to-venue and venue-to-canonical round-trips pass for every alias.
- [ ] Canonical IDs, canonical symbols and `(venue, exchange_symbol)` aliases are unique.
- [ ] Spot, perpetual, dated future and option applicability rules are tested.
- [ ] Non-applicable fields are explicitly null.

## Decimal and boundary behavior

- [ ] Only canonical positive decimal strings are accepted for increments and minimums.
- [ ] Binary floats, zero, negatives, exponent notation and non-canonical strings are rejected.
- [ ] Price is floored to `tick_size` and quantity is floored to `lot_size`.
- [ ] Price precision equals tick-size decimal places.
- [ ] Quantity precision equals lot-size decimal places.
- [ ] Quantized quantities below `min_qty` are rejected.
- [ ] Quantized notionals below `min_notional` are rejected.

## Lineage and revision safety

- [ ] The immutable Lot 32 gate checksum is verified before implementation logic.
- [ ] SourceRegistryV1 checksum, Lot 31 state checksum and Lot 31 audit checksum are recorded.
- [ ] Unknown sources, venue mismatches and source revision mismatches are rejected.
- [ ] Enabled, authenticated or connected sources are rejected.
- [ ] Ambiguous or unsafe revisions fail closed as `INSTRUMENT_FROZEN` behavior.
- [ ] Event, available and generated timestamps preserve causal ordering.

## Determinism and persistence

- [ ] Two builds on the same inputs and code commit produce identical state and audit payloads.
- [ ] State and audit checksums recompute independently.
- [ ] The standalone registry equals the registry embedded in state.
- [ ] Audit state checksum equals the state output checksum.
- [ ] All three artifacts are persisted atomically.

## Security and architecture

- [ ] No network-client import exists in the V3 governance package.
- [ ] No endpoint URL, API key, token, credential or secret key exists in Lot 32 configuration.
- [ ] Runtime remains `DATA_GOVERNANCE_ONLY`.
- [ ] Every safety permission remains fail-closed and `approved_size=0`.
- [ ] No timestamp governance, data-quality, forecast, signal, risk, order or execution capability is added.
- [ ] Lot 33 remains `PLANNED_LOCKED`.

## Quality gates

- [ ] Python compilation passes on 3.11.9.
- [ ] Ruff and mypy pass.
- [ ] Targeted line coverage meets the repository threshold.
- [ ] Targeted branch coverage meets the repository threshold.
- [ ] Mutation score is at least 80%.
- [ ] Architecture, ownership, traceability and no-silent-coercion gates pass.
- [ ] Bandit and dependency audit pass.
- [ ] Full repository regression passes.
- [ ] Three complete anti-flake repetitions pass.
- [ ] Exact-head CI evidence is recorded before merge, unless an explicitly documented external infrastructure exception is required and no failing test is waived.

## Promotion decision

Lot 32 may be promoted only when every applicable criterion is PASS, the exact implementation
commit is identified, the implementation PR is squash-merged, and a separate post-merge audit
confirms version/lifecycle state. Lot 33 remains locked until then.
