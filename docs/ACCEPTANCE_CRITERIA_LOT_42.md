# Acceptance Criteria — Lot 42

## Gate and scope

- AC42-001 — implementation branch descends from gate merge `7456c5b80b609ee5958d8b6da0effd489faa308c`.
- AC42-002 — entry-gate checksum remains `7ab3b17a74d30866fbec4ec15acfe608a9545e8831d80dcb39db2d059e293924`.
- AC42-003 — owner is `MicrostructureDomain` and runtime is `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.
- AC42-004 — Lot 43 remains `PLANNED_LOCKED` and no Lot 43 production file exists.
- AC42-005 — no external network, live exchange data, real credentials, trading or execution capability is introduced.

## Upstream evidence

- AC42-006 — frozen Lot 38 state/snapshot checksums are verified exactly.
- AC42-007 — frozen Lot 39 state/book checksums and delta-fixture file checksum are verified exactly.
- AC42-008 — Lot 39 prefix replay through the canonical reconstructor is `SYNCED` for every accepted prefix.
- AC42-009 — final prefix replay is exactly equal to the frozen Lot 39 reconstructed book.
- AC42-010 — frozen Lot 41 state/audit/feature checksums and links are verified exactly.
- AC42-011 — Lot 41 book quality must be `HEALTHY`, score `100`, consequence `NONE`.
- AC42-012 — upstream depth must be observed only and non-extrapolated.
- AC42-013 — stale, future-dated or identity-incompatible current evidence fails closed.

## Numeric and configuration contracts

- AC42-014 — all price, quantity, bps, ratio and notional JSON inputs are decimal strings; silent numeric coercion is rejected.
- AC42-015 — critical calculations use `Decimal` at configured precision `50`.
- AC42-016 — cluster, history-match, wall, persistence, void, cancellation and freshness thresholds are versioned configuration.
- AC42-017 — configuration shape and version are closed; extra or missing fields are rejected.

## Clustering

- AC42-018 — adjacent observed levels are clustered only when pairwise bps distance is within the configured threshold.
- AC42-019 — cluster quantity is the exact sum of observed quantities.
- AC42-020 — cluster notional is the exact sum of `price * quantity`.
- AC42-021 — cluster anchor is exact quantity-weighted average price.
- AC42-022 — historical matching is deterministic and one-to-one per observation.
- AC42-023 — changing best bid/ask does not itself change market identity.

## Persistence, replenishment and cancellation

- AC42-024 — persistence count equals the number of matched historical observations for the current zone.
- AC42-025 — persistence ratio equals `matched / total` at canonical decimal precision.
- AC42-026 — `PERSISTENT_ZONE` requires both minimum observation count and minimum ratio.
- AC42-027 — replenished quantity sums positive displayed-quantity increases only.
- AC42-028 — cancelled quantity sums positive displayed-quantity decreases only.
- AC42-029 — replenishment and cancellation ratios are deterministic and bounded in `[0,1]`.
- AC42-030 — missing historical match contributes no synthetic book level and cannot be represented as observed liquidity.

## Walls

- AC42-031 — `DISPLAYED_WALL` depends only on currently observed cluster notional and the versioned threshold.
- AC42-032 — wall confidence is qualitative status, never probability.
- AC42-033 — a persistent wall with cancellation rate under threshold may be `HIGH_CONFIDENCE`.
- AC42-034 — an instant/sharp cancellation case over threshold is `LOW_CONFIDENCE`.
- AC42-035 — a wall or zone never asserts participant intent.

## Voids and expiry

- AC42-036 — a `LIQUIDITY_VOID` is emitted only from a current observed same-side adjacent-level gap meeting the configured bps threshold.
- AC42-037 — bilateral synthetic fixtures demonstrate independent BID and ASK void detection.
- AC42-038 — a void is descriptive sparse depth and is never converted to forecast or signal.
- AC42-039 — historical wall candidates without a matching current cluster are expired, not silently retained active.
- AC42-040 — an empty active zone set is a valid deterministic result when evidence supports no current zone.

## Contracts, lineage and audit

- AC42-041 — `LiquidityZoneSetV1`, state and audit JSON Schemas are closed with `additionalProperties=false` at critical nested boundaries.
- AC42-042 — `participant_intent=NOT_INFERRED` and `participant_intent_inferred=false` are schema-locked.
- AC42-043 — state embeds the exact published zone set.
- AC42-044 — audit references exact state and zone-set checksums.
- AC42-045 — every zone, void, zone set, state and audit checksum is canonical and tamper-evident.
- AC42-046 — lineage binds the gate, frozen upstream evidence, config and availability time.
- AC42-047 — run context binds the exact code commit.
- AC42-048 — repeated build at identical commit/input is deterministic.
- AC42-049 — repeated atomic persistence is deterministic and produces exactly the three Lot 42 runtime artifacts.

## Reference fixture

- AC42-050 — canonical history sequences are exactly `[1001, 1002, 1003]`.
- AC42-051 — canonical current sequence is `1003` and mid is `50025`.
- AC42-052 — candidate reference produces 3 active zones and 3 displayed walls.
- AC42-053 — candidate reference produces 2 persistent zones and 1 low-confidence wall.
- AC42-054 — candidate reference produces 1 current liquidity void on BID.
- AC42-055 — reference output has no participant-intent inference, no decision authority and no execution authority.

## Safety and forbidden capabilities

- AC42-056 — `analysis_only=true`.
- AC42-057 — `used_for_decision=false`.
- AC42-058 — `trade_allowed=false`.
- AC42-059 — `execution_allowed=false`.
- AC42-060 — `approved_size=0`.
- AC42-061 — external connectivity, network ingestion and real credentials remain disabled.
- AC42-062 — no resilience engine, aggressor classification, CVD, hidden-liquidity inference, stop pools, sweep/fakeout/trap, derivatives, game-theory, forecast, signal, risk, routing or execution capability is added.

## Quality gates

- AC42-063 — Ruff passes on all Lot 42 changed Python files.
- AC42-064 — MyPy passes on `src/crypto_quant_bot/microstructure`.
- AC42-065 — no-connectivity validator passes.
- AC42-066 — targeted Lot 42 tests pass with line coverage `>=95%` and branch coverage `>=90%` on critical Lot 42 modules.
- AC42-067 — full repository regression passes.
- AC42-068 — targeted Lot 42 suite passes at least three additional anti-flake repetitions.
- AC42-069 — Bandit and dependency audit pass.
- AC42-070 — architecture, domain ownership, roadmap, traceability, coercion and engineering gates pass.
- AC42-071 — targeted mutation score is `>=80%`, with zero timeout and zero suspicious mutants.

## Freeze, merge and promotion

- AC42-072 — source head is not called frozen until all source-phase exact-head controls are recomputed green.
- AC42-073 — frozen evidence records exact source head, runtime artifact checksums, coverage and mutation results.
- AC42-074 — implementation merge is locked to the exact reviewed/frozen PR head.
- AC42-075 — Lot 42 is not marked `IMPLEMENTED_VALIDATED` by implementation merge alone.
- AC42-076 — a separate independent post-merge audit is required before lifecycle/release closure.
- AC42-077 — release `0.42.0` occurs only through successful post-merge closure.
- AC42-078 — Lot 43 remains locked until the Lot 42 post-merge audit is merged and a separate Lot 43 entry gate is approved.

## Definition of Done

Lot 42 is done only after all applicable AC42 controls are evidenced, the exact frozen implementation is merged, the independent post-merge audit returns GO, release/lifecycle are updated to `0.42.0`, and Lot 43 is still locked pending its own governance gate.
