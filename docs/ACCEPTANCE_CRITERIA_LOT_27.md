# Acceptance Criteria — Lot 27 Global Market Context Aggregator

## Functional

- all five configured source IDs are represented in every output;
- only validated sources are included;
- configured weights sum to one and are published;
- missing/invalid/stale sources contribute zero without renormalization;
- category support and aggregate evidence score are deterministic and bounded;
- explicit conflicts and insufficient dominance margin produce `GLOBAL_CONTEXT_MIXED`;
- insufficient source count or weighted coverage produces `GLOBAL_CONTEXT_UNKNOWN`;
- uncalibrated heterogeneous inputs never produce a statistical confidence interval.

## Deterministic integration oracle

Using the canonical Lots 22–26 artifacts:

- available sources: `5/5`;
- weighted coverage: `1.0`;
- aggregate evidence score: `0.5646`;
- dominant state: `GLOBAL_CONTEXT_MIXED`;
- conflict states: `MTF_DIVERGENT`;
- replay: `MATCH`.

## Negative and ablation

- remove each source independently and verify the exact missing configured weight;
- remove two 25% sources and verify `GLOBAL_CONTEXT_UNKNOWN` at 50% coverage;
- mark one source executable and verify fail-closed exclusion;
- make one source stale and verify age and zero contribution;
- alter weights, mappings or permissions and verify configuration rejection;
- tamper output and verify checksum rejection;
- add an unknown field and verify closed-schema rejection.

## Quality

- Python 3.11.9 locked environment;
- Ruff and mypy PASS;
- line coverage ≥95%;
- branch coverage ≥90%;
- mutation score ≥80% for aggregation/classification logic;
- Bandit, architecture and traceability PASS;
- full repository regression and anti-flake PASS;
- no unowned engineering deviation.

## Safety

- `analysis_only=true`;
- every decision, forecast, signal, routing and execution permission is `false`;
- `approved_size=0`;
- no BUY/SELL, probability, expected return, trade intent or order output.

## Promotion gate

Lot 28 remains `PLANNED_LOCKED` until Lot 27 is merged and a post-merge audit passes.
