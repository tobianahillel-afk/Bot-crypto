# Acceptance Criteria — Lot 37

Lot 37 is accepted only when every criterion below is PASS on the exact implementation evidence commit.

## Scope and ownership

- [ ] Owner is `MicrostructureDomain`.
- [ ] Runtime is exactly `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.
- [ ] Production changes remain inside `src/crypto_quant_bot/microstructure`.
- [ ] No Lot 38+ algorithm is implemented.
- [ ] Lot 38 remains `PLANNED_LOCKED`.

## Entry and lineage

- [ ] Lot 37 gate checksum is exact and valid.
- [ ] V3 post-merge closure is certified.
- [ ] Lot 36 state/audit checksums are bound in lineage.
- [ ] L2/trade prerequisite fixture checksums match the gate.
- [ ] Fixtures are offline, non-canonical and `used_for_decision=false`.

## Contracts

- [ ] Exactly six contracts exist in the Lot 37 registry.
- [ ] Every contract has a versioned schema under `contracts/schemas/`.
- [ ] State, audit, contract registry and capability matrix serialize deterministically.
- [ ] Contract registry persisted artifact equals the registry embedded in state.
- [ ] Capability matrix persisted artifact equals the matrix embedded in state.

## Capability boundary

- [ ] Four Lot 37 governance capabilities are `REQUIRED`.
- [ ] Fifteen Lots 38–52 capabilities are `DISABLED` and `PLANNED_LOCKED`.
- [ ] Eight dangerous capabilities are `FORBIDDEN`.
- [ ] Participant behavior inference must be explicitly labeled.
- [ ] Scenario score is never treated as a signal.
- [ ] Trade aggressor side remains `UNKNOWN` in Lot 37 fixture evidence.

## Safety

- [ ] External connectivity disabled.
- [ ] Network ingestion disabled.
- [ ] Real credentials disabled.
- [ ] Market-event publication disabled.
- [ ] Raw-data mutation disabled.
- [ ] Signal generation disabled.
- [ ] Risk approval disabled.
- [ ] Order routing disabled.
- [ ] Trading disabled.
- [ ] Execution disabled.
- [ ] `approved_size=0`.
- [ ] `used_for_decision=false`.

## Determinism and temporal integrity

- [ ] `event_time <= available_at <= generated_at`.
- [ ] Freshness uses integer microseconds.
- [ ] Run1/run2 produce identical state and audit checksums.
- [ ] No future-state or lookahead dependency is introduced.

## Negative and failure injection

- [ ] Modified gate checksum is rejected.
- [ ] Missing V3 closure is rejected.
- [ ] Missing schema is rejected.
- [ ] Stale fixture is rejected.
- [ ] Decision-enabled fixture is rejected.
- [ ] Future V4 activation is rejected.
- [ ] Forbidden capability weakening is rejected.
- [ ] Invalid runtime, SHA, checksum, timestamp and reason-code forms are rejected.

## Quality gates

- [ ] Ruff PASS.
- [ ] Mypy PASS.
- [ ] Domain architecture PASS.
- [ ] Roadmap semantics PASS.
- [ ] Traceability contract PASS.
- [ ] Full regression PASS.
- [ ] Lot 37 line coverage `>=95%`.
- [ ] Lot 37 branch coverage `>=90%`.
- [ ] Lot 37 mutation score `>=80%`.
- [ ] Anti-flake repetitions `>=3`.
- [ ] Static security scan PASS.
- [ ] Dependency audit PASS.
- [ ] No real secret or network capability introduced.

## Evidence and final gate

- [ ] State/audit/registry/matrix evidence is frozen from the exact source commit.
- [ ] Coverage and mutation summaries identify the exact evidence commit.
- [ ] Implementation PR has zero BLOCKER/MAJOR findings.
- [ ] Post-merge audit is performed separately.
- [ ] Lot 38 receives no implementation authorization until its own distinct gate.
