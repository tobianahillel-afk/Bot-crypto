# Lot 40 — Book Integrity / Desynchronization Detector

## Status

Implementation candidate under `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`, authorized by the merged Lot 40 entry gate `91df3e378336a791a731cb1561382ba28e6e0978`.

Lot 41 remains `PLANNED_LOCKED`. This lot is analysis-only and cannot produce signal, risk approval, order routing, trading permission or execution.

## Purpose

Lot 40 consumes the certified, reconstructed Lot 39 order-book surface and determines whether that surface is sufficiently coherent to remain usable by later offline research. It does **not** compute spread, depth bands, imbalance, microprice or any Lot 41 feature.

The detector publishes four canonical surfaces:

- `BookIntegrityDesynchronizationDetectorStateV1`;
- `BookIntegrityDesynchronizationDetectorAuditV1`;
- `BookIntegrityStateV1`;
- `BookHealthVetoV1`.

## Inputs and lineage

Canonical roadmap inputs remain exactly:

- `RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)`;
- `LineageEnvelopeV1 des artefacts produits par les lots préalables`.

The implementation binds those generic contracts to an immutable Lot40 run context and lineage envelope containing:

- Lot40 entry-gate checksum;
- frozen Lot39 state checksum;
- frozen Lot39 audit checksum;
- frozen reconstructed-book checksum;
- frozen Lot39 delta-fixture checksum;
- input availability time.

The reference run consumes only the certified Lot39 offline artifacts. No network ingestion is present.

## Health components

The versioned configuration publishes six components. Their weights total exactly `100` and the score is a deterministic weighted sum, **not a probability**.

| Component | Weight | Critical | Exact responsibility |
|---|---:|---|---|
| `SEQUENCE_CONTINUITY` | 20 | yes | `SYNCED`, positive applied count and `sequence_id = base_sequence_id + applied_delta_count` |
| `CROSSED_LOCKED_STATE` | 20 | yes | both sides parsable and `best_bid < best_ask` |
| `FRESHNESS` | 15 | no | `decision_time - receive_time <= max_stale_age_us` |
| `CHECKSUM_INTEGRITY` | 20 | yes | canonical reconstructed-book checksum exactly matches payload |
| `DEPTH_INTEGRITY` | 20 | no | published level counts meet configured minimums |
| `LEVEL_MONOTONICITY` | 5 | yes | unique positive prices, non-negative finite quantities, bids strictly descending, asks strictly ascending |

No hidden threshold or hidden component is allowed.

## Score and health state

For each component `i`:

```text
component_score_i = weight_i if component_i passes else 0
book_health_score = sum(component_score_i)
```

The score is bounded in `[0,100]` because the weights are positive and total exactly `100`.

Health status is deterministic:

```text
if any critical component fails: CRITICAL
else if any component fails:     DEGRADED
else:                            HEALTHY
```

A high score cannot override a critical component failure. In particular, an isolated monotonicity failure gives score `95` but status `CRITICAL` and consequence `BLOCK`.

## Veto consequence policy

Thresholds and consequences are versioned in `config/microstructure/book_integrity_desynchronization_detector_v1.json`:

```text
trade_health_threshold  = 90
system_health_threshold = 80
critical consequence    = BLOCK
system consequence      = PAUSE
```

Priority:

```text
critical failure                        -> BLOCK
no critical failure and score < 80      -> PAUSE
no critical failure and 80 <= score <90 -> WAIT
otherwise                               -> NONE
```

Examples encoded in tests:

- reference book: `100 / HEALTHY / NONE`;
- freshness-only failure: `85 / DEGRADED / WAIT`;
- depth-only failure: `80 / DEGRADED / WAIT`;
- freshness + depth: `65 / DEGRADED / PAUSE`;
- monotonicity-only failure: `95 / CRITICAL / BLOCK`;
- checksum, crossed/locked or sequence failure: `BLOCK`.

`WAIT`, `PAUSE` and `BLOCK` are offline health consequences. They never imply a trade or execution capability.

## Temporal semantics

The reference run uses an injected deterministic decision clock. The detector distinguishes:

- order-book `event_time`;
- order-book `receive_time`;
- configured `decision_time`;
- artifact `generated_at`.

Required ordering is:

```text
event_time <= receive_time <= decision_time <= generated_at
```

Future-dated input is rejected fail-closed rather than clamped to zero age.

## Structural integrity

Level validation is exact-decimal and deterministic. The detector rejects or critically degrades unprovable structures; it never silently sorts, repairs or coerces the source book. Duplicate prices and invalid/negative levels cannot become a healthy state.

The checksum component recomputes the canonical checksum from the raw reconstructed-book payload. It does not trust the checksum merely because Lot39 produced it historically.

## Persistence

The reference runner atomically persists:

- `data/audit/book_integrity_desynchronization_detector_lot40.json`;
- `data/audit/book_integrity_desynchronization_detector_audit_lot40.json`;
- `data/audit/book_integrity_state_lot40.json`;
- `data/audit/book_health_veto_lot40.json`.

State, audit, integrity and veto are checksum-linked. Replaying the same inputs, config, clock and code commit must produce byte-equivalent JSON semantics and identical checksums.

## Failure behavior

- missing/malformed mandatory input: no valid output; fail closed;
- future-dated receive time: no valid output; fail closed;
- critical integrity failure on otherwise parseable book: valid `CRITICAL` state plus `BLOCK` veto;
- non-critical stale/depth degradation: deterministic `WAIT` or `PAUSE` according to configured thresholds;
- unknown config field or weight/threshold inconsistency: no valid output;
- Lot39 prerequisite checksum/lifecycle drift: no valid output;
- entry-gate drift: no valid output.

No error path falls back to a healthy state.

## Quality gates

- line coverage `>=95%`;
- branch coverage `>=90%`;
- mutation score `>=80%`;
- anti-flake repetitions `>=3`;
- full regression PASS;
- Ruff/mypy PASS;
- architecture/roadmap/traceability/engineering PASS;
- Bandit and dependency audit PASS;
- no-connectivity AST validation PASS.

## Explicit non-goals

Lot 40 does not implement:

- Lot41 spread/depth/imbalance/microprice features;
- liquidity walls/voids/zones;
- resilience/replenishment;
- aggressor/order-flow/CVD;
- participant intent or game-theory scenarios;
- forecasts or signals;
- risk approval, orders, routing, trading or execution.

Safety remains `analysis_only=true`, `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.
