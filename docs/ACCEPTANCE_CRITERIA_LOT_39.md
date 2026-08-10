# Acceptance Criteria — Lot 39

Lot 39 may be declared implemented only when every item below is PASS on one exact source head.

## Scope and ownership

- [ ] `MicrostructureDomain` is the sole business owner.
- [ ] Runtime is exactly `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.
- [ ] Entry gate checksum is exactly `250c67574a8add382915c1b8f0b104f801bd91757c829c3d7d336f8e2e22e0ab`.
- [ ] Implementation descends from gate merge `938a0e9cf92ef5bbda02045486afbd9a32dc67ec`.
- [ ] Lot 40 remains `PLANNED_LOCKED` and has no production implementation.

## Contracts

- [ ] `OrderBookDeltaV1` is explicit, versioned and rejects negative quantities.
- [ ] `OrderBookDeltaSequenceReconstructorStateV1` supports only `SYNCED` or fail-closed `RESYNC_REQUIRED` outcomes.
- [ ] `OrderBookDeltaSequenceReconstructorAuditV1` binds source/config/input/output checksums.
- [ ] `ReconstructedOrderBookV1` can exist only in `SYNCED` state.
- [ ] `SequenceGapEventV1` is required for `RESYNC_REQUIRED` and absent from healthy state.
- [ ] Canonical roadmap-facing module, model, runner and test paths exist.

## Functional behavior

- [ ] Snapshot sequence `1001` + deltas `1002`, `1003` reconstructs exact expected levels.
- [ ] Quantity zero deletes an existing level.
- [ ] Positive quantity upserts an exact level quantity.
- [ ] Gap requires resync and publishes no book.
- [ ] Duplicate/reordered sequence requires resync and publishes no book.
- [ ] Reordered event time requires resync and publishes no book.
- [ ] Missing-level deletion requires resync and publishes no book.
- [ ] Crossed/locked resulting book requires resync and publishes no book.
- [ ] Expected checksum mismatch requires resync and publishes no book.
- [ ] Empty delta sequence is rejected.
- [ ] Incompatible source/venue/instrument/market identity is rejected.
- [ ] Stale/future-dated input is rejected.
- [ ] Run1/run2 outputs are exactly deterministic.

## Persistence and auditability

- [ ] Healthy persistence writes state + audit + book and removes stale gap evidence.
- [ ] Blocked persistence writes state + audit + gap and removes stale book evidence.
- [ ] Every persisted checksum recomputes exactly.
- [ ] Reason codes contain `LOT40_REMAINS_LOCKED`.
- [ ] No decision/trading/execution permission can be inferred from technical success.

## Engineering quality

- [ ] `python -m compileall` PASS.
- [ ] Ruff PASS on all Lot 39 changed Python files.
- [ ] mypy PASS for the microstructure package.
- [ ] Architecture and domain ownership validators PASS.
- [ ] Roadmap and traceability validators PASS.
- [ ] Silent numeric coercion gate PASS.
- [ ] Engineering deviation gate PASS.
- [ ] Bandit PASS for Lot 39 Python surfaces.
- [ ] `pip-audit -r requirements-dev.lock` PASS.
- [ ] No network-capable imports are present in Lot 39 runtime/runner/validator.

## Test quality

- [ ] Targeted unit/integration/negative tests PASS.
- [ ] Full repository non-regression PASS.
- [ ] Line coverage `>=95%` for Lot 39 critical source.
- [ ] Branch coverage `>=90%` for Lot 39 critical source.
- [ ] Mutation score `>=80%` for Lot 39 critical source.
- [ ] Three anti-flake targeted repetitions PASS.
- [ ] Three full-suite anti-flake repetitions PASS where required by institutional CI.

## Evidence and promotion

- [ ] State, audit and canonical output artifacts are frozen to the certified source head.
- [ ] Coverage and mutation summaries are versioned with exact source-head binding.
- [ ] Implementation report records exact commands, CI run IDs/artifact digests and limitations.
- [ ] Final implementation PR is fully green and reviewed before merge.
- [ ] Independent post-merge audit returns zero BLOCKER and zero MAJOR findings.
- [ ] Lot 40 implementation does not start until its own separate green entry gate is merged.
