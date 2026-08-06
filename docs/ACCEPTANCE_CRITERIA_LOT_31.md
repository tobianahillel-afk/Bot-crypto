# Acceptance Criteria — Lot 31

Lot 31 is accepted only when every criterion below is evidenced on the exact PR head.

## Contracts and ownership

- [ ] `MarketDataGovernanceDomain` is the sole owner.
- [ ] All implementation code remains under `src/crypto_quant_bot/data_governance`.
- [ ] The five required output contracts are represented and schema-versioned.
- [ ] Every capability has an owner, contract, status and gate.
- [ ] Lot 32 remains `PLANNED_LOCKED`.

## Source registry

- [ ] Exactly one approved source of truth exists.
- [ ] Every backup source exists and the graph is acyclic.
- [ ] Source IDs are unique and canonically ordered.
- [ ] All 14 gate-required metadata fields are explicit.
- [ ] Unknown, duplicate, self-referencing or cyclic sources are rejected.
- [ ] A source revision is positive and uses immutable versioned replacement.

## Connectivity and secrets

- [ ] Every source has `auth_mode=NONE`.
- [ ] Every source has `enabled=false` and `connection_status=DISABLED`.
- [ ] No networking library is imported by the Lot 31 domain.
- [ ] No credential, key, password or token is accepted as source metadata.
- [ ] No remote request is executed by tests, runner or validator.

## Time, lineage and replay

- [ ] Lineage is bound to the certified Lot 30 closure artifact.
- [ ] `event_time`, `available_at` and `generated_at` are explicit UTC.
- [ ] `event_time <= available_at <= generated_at`.
- [ ] Two runs on one code commit produce byte-identical artifacts.
- [ ] State and audit checksums independently recompute.
- [ ] The audit binds state and configuration checksums.

## Safety

- [ ] Analysis-only is true.
- [ ] Decision, ingestion, trading and execution permissions are false.
- [ ] `approved_size=0`.
- [ ] Instrument normalization, data quality and continuous-market-data capabilities remain disabled.
- [ ] Forecast, signal and trade-execution capabilities remain forbidden.

## Engineering evidence

- [ ] Compilation, Ruff and mypy pass.
- [ ] Targeted line coverage is at least 95%.
- [ ] Targeted branch coverage is at least 90%.
- [ ] Critical mutation score is at least 80%.
- [ ] Architecture, ownership, traceability and engineering-deviation gates pass.
- [ ] Bandit and dependency audit pass.
- [ ] Full repository regression passes.
- [ ] Three Lot 31 anti-flake repetitions pass.
- [ ] No unresolved review thread remains.

## Promotion verdict

Only an exact-head report with every item passing may state:

```text
GO_LOT31_SOURCE_REGISTRY_VALIDATED_METADATA_ONLY
```
