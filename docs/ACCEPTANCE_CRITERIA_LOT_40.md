# Acceptance Criteria — Lot 40

Lot 40 is accepted only when every mandatory criterion below is PASS on one exact production source head and the resulting evidence is frozen before merge.

## Scope and architecture

- implementation is owned only by `MicrostructureDomain`;
- runtime is exactly `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`;
- entry gate `23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18` is revalidated;
- frozen Lot39 state/audit/reconstructed-book/fixture lineage is revalidated;
- Lot41 remains locked and unimplemented;
- no network/live credentials or exchange connector is introduced.

## Canonical contracts

The following outputs exist, are immutable typed models, serialize deterministically and have strict schemas:

- `BookIntegrityDesynchronizationDetectorStateV1`;
- `BookIntegrityDesynchronizationDetectorAuditV1`;
- `BookIntegrityStateV1`;
- `BookHealthVetoV1`.

Each output has explicit lineage, reason codes and checksum linkage.

## Health semantics

The implementation evaluates exactly six versioned components:

1. sequence continuity;
2. crossed/locked state;
3. freshness;
4. checksum integrity;
5. depth integrity;
6. level monotonicity.

The weights total exactly `100`. `book_health_score` is the sum of passed weights and is explicitly not a probability.

Critical failures are sequence continuity, crossed/locked state, checksum integrity and level monotonicity.

## Consequence semantics

Using the versioned reference policy:

- any critical failure -> `BLOCK` regardless of aggregate score;
- no critical failure and score `<80` -> `PAUSE`;
- no critical failure and `80 <= score <90` -> `WAIT`;
- score `>=90` with no critical failure -> `NONE`.

Mandatory boundary tests include:

- healthy reference -> score `100`, `HEALTHY`, `NONE`;
- freshness-only -> score `85`, `DEGRADED`, `WAIT`;
- depth-only -> score `80`, `DEGRADED`, `WAIT`;
- freshness+depth -> score `65`, `DEGRADED`, `PAUSE`;
- monotonicity-only -> score `95`, `CRITICAL`, `BLOCK`;
- checksum mismatch -> `BLOCK`;
- crossed book -> `BLOCK`;
- locked book -> `BLOCK`;
- sequence discontinuity -> `BLOCK`;
- duplicate level -> critical monotonicity failure;
- future-dated receive time -> fail closed with no valid output.

## Determinism and persistence

- deterministic run1/run2 state and audit equality;
- four atomically persisted artifacts;
- persisted state/audit/integrity/veto equal replay outputs;
- canonical checksum for each artifact validates after persistence;
- audit links state, integrity and veto checksums exactly.

## Negative validation

- unknown config field rejected;
- component weight set drift rejected;
- weights not totaling 100 rejected;
- invalid threshold ordering rejected;
- critical/system consequence drift rejected;
- Lot40 gate checksum drift rejected;
- Lot39 prerequisite checksum or lifecycle drift rejected;
- invalid safety boundary rejected;
- Lot41 implementation presence rejected before promotion.

## Quality

- line coverage `>=95%` on Lot40 production modules;
- branch coverage `>=90%`;
- mutation score `>=80%` with deterministic single-child policy;
- anti-flake `>=3` repetitions;
- full repository regression PASS;
- Ruff PASS;
- mypy PASS;
- architecture/roadmap/traceability/engineering PASS;
- Bandit PASS;
- dependency audit PASS;
- AST no-connectivity validator PASS.

## Safety

The frozen state and audit must prove:

```text
analysis_only=true
used_for_decision=false
external_connectivity_allowed=false
network_ingestion_allowed=false
real_credentials_allowed=false
market_event_publication_allowed=false
raw_data_mutation_allowed=false
scenario_score_is_signal=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

A positive health score never bypasses these boundaries.

## Definition of done

Lot 40 is not complete on green unit tests alone. Completion requires:

1. exact-head validation workflow PASS;
2. exact-head mutation workflow PASS;
3. frozen deterministic artifacts and quality summaries;
4. full institutional/non-regression workflow PASS;
5. no BLOCKER/MAJOR audit finding;
6. human-reviewed PR merge on the certified head;
7. independent post-merge audit before any Lot41 gate.
