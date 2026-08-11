# Lot 41 — Spread, Depth & Imbalance Engine Report

## Current status

`IMPLEMENTATION_CANDIDATE_NOT_FROZEN`

Entry gate merge: `75822f8ea7c6f67f73649d2f43be6efba840ab67`  
Entry gate checksum: `1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe`  
Owner: `MicrostructureDomain`  
Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
Lot 42: `PLANNED_LOCKED`

This report intentionally does not claim frozen source, final coverage, mutation score or merge status yet. Those fields may be promoted only from exact-head CI evidence after the implementation source stops changing.

## Implemented candidate boundary

The candidate implements only deterministic descriptive order-book features:

- absolute spread;
- spread in bps;
- mid price;
- opposite-queue-weighted microprice;
- observed depth inside versioned bps bands `0.025`, `0.05`, `0.10`;
- observed cumulative bid/ask depth;
- symmetric imbalance with explicit zero-denominator undefined state;
- strict Lot 40 health/veto/checksum/identity/time binding;
- deterministic canonical state/feature/audit checksums;
- atomic JSON persistence;
- fail-closed safety and no-connectivity validation.

No missing depth is estimated. Every band is `OBSERVED_LEVELS_ONLY`; `extrapolated=false`.

## Reference values

For certified reconstructed sequence `1003`:

- best bid `50024.9 @ 0.9`;
- best ask `50025.1 @ 0.65`;
- absolute spread `0.2`;
- mid `50025`;
- spread bps begins `0.039980009995002498750624687656...`;
- microprice begins `50025.016129032258064516129032...`;
- band bid depth: `0.9`, `0.9`, `1.4`;
- band ask depth: `0.65`, `1.75`, `2.15`.

## Safety

The candidate preserves `analysis_only=true`, `used_for_decision=false`, `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`. External connectivity, network ingestion, live exchange data and real credentials remain forbidden.

## Certification still required

Before this report can become `PASS_FROZEN_IMPLEMENTATION_EVIDENCE`:

1. Ruff, mypy, schema/no-connectivity and all contract tests must pass.
2. Critical Lot 41 line coverage must be at least `95%`, branch coverage at least `90%`.
3. Full repository regression and three anti-flake repetitions must pass.
4. Architecture, roadmap semantics, traceability, silent-coercion and engineering gates must pass.
5. Bandit and dependency audit must pass.
6. Mutation must be at least `80%`, with timeout and suspicious counts equal to zero for final evidence.
7. Exact source head must then be frozen without later production-source changes.
8. Three deterministic output artifacts and CI evidence must be committed as evidence-only changes.
9. Final exact PR head must be fully green and review-clean before merge.
10. An independent post-merge audit is required before Lot 42 can be unlocked.
