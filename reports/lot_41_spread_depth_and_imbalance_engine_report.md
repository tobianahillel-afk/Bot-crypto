# Lot 41 — Spread, Depth & Imbalance Engine Report

## Current verdict

`PASS_FROZEN_IMPLEMENTATION_EVIDENCE`

Lot 41 implementation evidence is frozen against an immutable production source head and independently revalidated. This verdict certifies implementation evidence only. PR #51 is not merged by this report, and Lot 42 remains locked until an independent Lot 41 post-merge audit is itself fully green and merged.

## Certified commit chain

- Lot 41 entry-gate merge: `75822f8ea7c6f67f73649d2f43be6efba840ab67`;
- entry-gate checksum: `1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe`;
- frozen production source head: `14c0d8da1b02d076b3c43a07a34ac96c673018b0`;
- frozen evidence head: `7ada0ca6c4d439505ef453b988dedd4aa96c1a32`;
- owner: `MicrostructureDomain`;
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`;
- project release entering implementation: `0.40.0`;
- Lot 42: `PLANNED_LOCKED`.

The source-to-evidence diff contains exactly five files and no production source, config, schema, runner, validator, test, package export, or workflow changes:

1. `data/audit/book_feature_state_lot41.json`;
2. `data/audit/spread_depth_and_imbalance_engine_audit_lot41.json`;
3. `data/audit/spread_depth_and_imbalance_engine_lot41.json`;
4. `reports/lot41/coverage_summary.json`;
5. `reports/lot41/mutation_summary.json`.

The dedicated frozen-evidence workflow proves this exact five-file delta and separately proves that the certified implementation inventory is unchanged after `SOURCE_HEAD`.

## Certified implementation scope

Lot 41 publishes deterministic descriptive order-book features only:

- absolute spread;
- spread in basis points;
- mid price;
- opposite-queue-weighted microprice;
- observed depth inside versioned bps bands `0.025`, `0.05`, and `0.10`;
- observed cumulative bid and ask depth;
- symmetric depth imbalance `(bid_depth - ask_depth) / (bid_depth + ask_depth)`;
- explicit `UNDEFINED_ZERO_DENOMINATOR` state when both depths are zero;
- strict Lot 40 health/veto/checksum/identity/time binding;
- deterministic state/feature/audit checksums;
- atomic JSON persistence;
- deterministic run1/run2 replay;
- AST no-connectivity validation;
- fail-closed safety and Lot 42 lock enforcement.

No missing order-book depth is estimated or extrapolated. Published depth is `OBSERVED_LEVELS_ONLY` and `extrapolated=false`.

## Frozen reference result

For certified reconstructed sequence `1003`:

```text
best_bid=50024.9 @ 0.9
best_ask=50025.1 @ 0.65
spread_absolute=0.2
mid_price=50025
spread_bps=0.03998000999500249875062468766
microprice=50025.01612903225806451612903
band_bps=[0.025, 0.05, 0.1]
bid_depth=[0.9, 0.9, 1.4]
ask_depth=[0.65, 1.75, 2.15]
sequence_id=1003
book_health_status=HEALTHY
book_health_score=100
book_health_consequence=NONE
observed_depth_only=true
extrapolated=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

Frozen canonical checksums:

- spread/depth/imbalance state: `23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573`;
- spread/depth/imbalance audit: `af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd`;
- `BookFeatureStateV1`: `77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5`.

## Frozen Lot 40 lineage

The Lot 41 state and audit are bound exactly to:

- Lot 40 state: `e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477`;
- Lot 40 audit: `978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c`;
- `BookIntegrityStateV1`: `35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a`;
- `BookHealthVetoV1`: `000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc`;
- reconstructed Lot 39 book: `a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde`.

The frozen upstream book is `HEALTHY`, score `100`, consequence `NONE`; Lot 41 fails closed on degraded/critical upstream health, active veto, crossed/locked state, identity mismatch, invalid causal time, checksum drift, or malformed book levels.

## Exact coverage evidence

Critical Lot 41 coverage on `SOURCE_HEAD`:

- `spread_depth_and_imbalance_engine.py`: `158` statements, `0` missed; `44` branches, `0` partial;
- `spread_depth_and_imbalance_engine_models.py`: `225` statements, `0` missed; `48` branches, `0` partial;
- `spread_depth_and_imbalance_engine_validation.py`: `77` statements, `0` missed; `40` branches, `0` partial;
- total: `460` statements and `132` branches;
- line coverage: `100.00%` (`>=95%` required);
- branch coverage: `100.00%` (`>=90%` required);
- targeted Lot 41 tests: `64`;
- anti-flake repetitions: `3`;
- status: `PASS`.

Validation workflow evidence on the exact source head:

- run: `31483147929`;
- artifact: `9098042735` (`lot41-spread-depth-imbalance-evidence`);
- artifact digest: `sha256:c72bf3a6eda3e006132b924bbe6bdee896bfd89522aff2efcbf64aee1a073daa`.

## Exact mutation evidence

Mutation assurance on the same `SOURCE_HEAD`:

- score: `81.93%` (`>=80%` required);
- killed: `966`;
- survived: `213`;
- evaluated/completed/total: `1179/1179/1179`;
- timeout: `0`;
- suspicious: `0`;
- `max_children=1`;
- `PYTHONHASHSEED=0`;
- mutmut run/results exit codes: `0/0`;
- status: `PASS`.

Mutation workflow evidence:

- run: `31483147942`;
- artifact: `9098069057` (`lot41-mutation-evidence`);
- artifact digest: `sha256:0790745bf018c8ccfa6d5f6c88445d11d8a416d95025d0193b793208146f8037`.

## Exact-head source certification

Before the source was frozen, all 16 applicable workflows on `SOURCE_HEAD=14c0d8da1b02d076b3c43a07a34ac96c673018b0` completed `SUCCESS`, including:

- Lot 41 validation and Lot 41 mutation assurance;
- Institutional code quality gates;
- Lot 41 and Lot 40 historical entry-gate attestations;
- Lot 40 validation, frozen evidence, engineering diagnostic, mutation, and independent post-merge audit;
- Lot 39 validation, frozen evidence, mutation, and independent post-merge audit;
- Lot 37 mutation assurance;
- roadmap documentation and Lot 26 foundation/lifecycle validation.

The institutional workflow passed full tests, repository-wide Ruff/mypy, architecture/ownership, roadmap semantics, decision traceability, silent numeric coercion, engineering deviations, static security, dependency audit, targeted mutation, three full-suite anti-flake repetitions, and repository-wide coverage.

## Frozen-evidence attestation

The dedicated `Lot 41 frozen evidence attestation` independently passed on head `cc52ef04e3f88ba5a678908fdaf729a1b18099d7`.

It enforces:

- gate merge → source head → evidence head → current-head ancestry;
- exact five-file source-to-evidence delta;
- immutable certified Lot 41 source/config/schemas/runners/validators/tests/package export/docs/workflows after `SOURCE_HEAD`;
- immutable five-file evidence set after `EVIDENCE_HEAD`;
- canonical state/audit/feature checksum recomputation and cross-links;
- exact Lot 40 lineage and reference math;
- exact `100/100` coverage evidence;
- exact `81.93%` mutation evidence with zero timeout/suspicious mutants;
- exact fail-closed safety;
- current Lot 42 absence;
- full regression, Bandit, dependency audit, and three Lot 41 anti-flake repetitions.

Attestation CI evidence:

- run: `31483957208`;
- artifact: `9098368828` (`lot41-frozen-evidence-attestation`);
- artifact digest: `sha256:69f18b62d15bfc5be3776fa92d0d5e5538846c20eedfae0b9f3c7a8b1d8f13fe`;
- conclusion: `SUCCESS`.

## Safety boundary

The frozen state and audit require:

- `analysis_only=true`;
- `used_for_decision=false`;
- no external connectivity or network ingestion;
- no live exchange data or real credentials;
- no market-event publication or raw-data mutation;
- no participant-intent fact or scenario-to-signal conversion;
- no signal generation;
- no risk approval;
- no order routing;
- `trade_allowed=false`;
- `execution_allowed=false`;
- `approved_size=0`.

## Rollback

Rollback is deterministic: return the implementation branch to the merged Lot 41 gate `75822f8ea7c6f67f73649d2f43be6efba840ab67`. Lot 40 remains the latest independently audited implementation at release `0.40.0`; all frozen Lot 40 evidence remains unchanged.

## Progression rule

Lot 42 remains `PLANNED_LOCKED`. It must not receive an implementation gate or source implementation until:

1. PR #51 is merged from an exact fully green final head with no blocking reviews/threads; and
2. a separate independent Lot 41 post-merge audit is fully green and merged with an explicit `GO_LOT41_POST_MERGE` verdict.
