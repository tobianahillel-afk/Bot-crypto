# Lot 40 — Book Integrity / Desynchronization Detector Report

## Current verdict

`IMPLEMENTATION_CANDIDATE_NOT_FROZEN`

This report intentionally does not claim final coverage, mutation, frozen checksums or merge eligibility yet. Those values will be recorded only from exact-head CI evidence after the production source is stable.

## Authorized base

- Lot40 gate merge: `91df3e378336a791a731cb1561382ba28e6e0978`
- gate checksum: `23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18`
- project release entering implementation: `0.39.0`
- owner: `MicrostructureDomain`
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- Lot41: `PLANNED_LOCKED`

## Implemented candidate scope

- immutable Lot40 run-context and lineage contracts;
- immutable `BookIntegrityStateV1` and `BookHealthVetoV1`;
- immutable detector state/audit contracts;
- strict versioned health policy configuration;
- sequence-continuity health component;
- crossed/locked health component;
- injected-clock freshness component;
- independent canonical checksum revalidation;
- depth-collapse component based only on level counts;
- level validity/monotonicity component;
- deterministic weighted score with published components;
- critical-veto dominance over aggregate score;
- `NONE/WAIT/PAUSE/BLOCK` consequence policy;
- atomic four-artifact persistence;
- deterministic replay validator;
- AST no-connectivity validator;
- compatibility conversion of historical Lot39 CI into archival attestations.

## Reference policy

Weights:

- sequence continuity: `20`;
- crossed/locked: `20`;
- freshness: `15`;
- checksum: `20`;
- depth integrity: `20`;
- level monotonicity: `5`.

Thresholds:

- trade health: `90`;
- system health: `80`;
- critical failure: `BLOCK`;
- system-threshold failure: `PAUSE`.

The score is a deterministic health score and is **not a calibrated probability**.

## Reference expectation

Using the frozen Lot39 reconstructed book and the versioned Lot40 decision clock, the candidate reference output is expected to be:

```text
health_status=HEALTHY
book_health_score=100
consequence=NONE
stale_age_us=30000
bid_depth_levels=2
ask_depth_levels=3
trade_allowed=false
execution_allowed=false
approved_size=0
```

These expectations are executable assertions; final artifact checksums are not recorded until exact-head evidence is frozen.

## Required evidence before GO

- targeted line coverage `>=95%`;
- targeted branch coverage `>=90%`;
- mutation score `>=80%`;
- anti-flake x3;
- deterministic run1/run2 artifact equality;
- full repository regression;
- Ruff/mypy;
- architecture/roadmap/traceability/engineering;
- Bandit and dependency audit;
- institutional quality gates;
- exact source/evidence head separation;
- independent post-merge audit.

## Safety

No network ingestion, real credentials, signal generation, risk approval, routing, trading or execution is introduced. `approved_size` remains `0`. Lot41 remains outside the implementation scope.
