# Lot 41 — Spread, Depth & Imbalance Engine

## Status

`IMPLEMENTATION_CANDIDATE` — authorized by the merged Lot 41 entry gate `75822f8ea7c6f67f73649d2f43be6efba840ab67`. This document fixes the mathematics and contracts before implementation evidence is frozen. Lot 42 remains `PLANNED_LOCKED`.

## Boundary

Owner: `MicrostructureDomain`  
Package: `src/crypto_quant_bot/microstructure`  
Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
Canonical output: `BookFeatureStateV1`

The engine consumes only certified offline lineage. It does not ingest a network feed, infer participant intent, cluster liquidity zones/walls/voids, forecast, generate signals, approve risk, route orders, trade or execute.

## Mandatory upstream gates

A publishable Lot 41 state requires all of the following:

- exact Lot 41 entry-gate checksum `1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe`;
- audited lifecycle latest implemented lot `40` and Lot 41 historical status `PLANNED_LOCKED` at gate time;
- certified Lot 40 detector state checksum `e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477`;
- certified Lot 40 audit checksum `978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c`;
- `BookIntegrityStateV1` checksum `35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a`;
- `BookHealthVetoV1` checksum `000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc`;
- reconstructed book checksum `a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde`;
- synchronization state `SYNCED`, health `HEALTHY`, score `100`, consequence `NONE`, no active veto;
- identical source / venue / instrument / market type / sequence and causal timestamps across the certified book-quality lineage.

Any mismatch is fail-closed and no valid Lot 41 output is published.

## Versioned numeric configuration

`config/microstructure/spread_depth_and_imbalance_engine_v1.json` is part of the lineage and fixes:

- decimal calculation precision: `50` significant decimal digits;
- feature horizon: `BOOK_SNAPSHOT`;
- depth bands in bps from the mid: `0.025`, `0.05`, `0.10`;
- required upstream book health: `HEALTHY`;
- required upstream consequence: `NONE`.

Prices and quantities are decimal **strings**. Numeric JSON coercion is forbidden. Values must be finite and strictly positive. A published book must be bilateral, strictly monotonic, open and uncrossed.

## Mathematics

For best bid `(P_b, Q_b)` and best ask `(P_a, Q_a)`:

```text
spread_abs = P_a - P_b
mid = (P_a + P_b) / 2
spread_bps = spread_abs / mid * 10000
microprice = (P_a * Q_b + P_b * Q_a) / (Q_b + Q_a)
```

The microprice uses opposite-side queue weighting: a larger bid queue moves it toward the ask and a larger ask queue moves it toward the bid. `Q_b + Q_a` must be strictly positive; no fallback is permitted.

For a configured band `B` in bps and mid `M`:

```text
bid_distance_bps(P) = (M - P) / M * 10000
ask_distance_bps(P) = (P - M) / M * 10000
bid_depth(B) = sum(Q_i for observed bids with bid_distance_bps(P_i) <= B)
ask_depth(B) = sum(Q_i for observed asks with ask_distance_bps(P_i) <= B)
imbalance(B) = (bid_depth(B) - ask_depth(B)) / (bid_depth(B) + ask_depth(B))
```

If the imbalance denominator is zero, the feature value is `null`, status is `UNDEFINED_ZERO_DENOMINATOR`, and the reason code is explicit. No synthetic zero is substituted.

Cumulative depth is calculated level-by-level in the original certified order:

```text
C_bid(k) = sum(Q_i, i=1..k)
C_ask(k) = sum(Q_i, i=1..k)
```

Every published cumulative entry includes the observed level price, quantity, cumulative quantity and distance to mid in bps.

## No-extrapolation contract

Depth is **observed-depth-only**. The engine never assumes that an input book is complete beyond its last observed level and never estimates missing levels. Each band publishes observed level counts and `coverage_status=OBSERVED_LEVELS_ONLY`. The state publishes the furthest observed bid/ask distances and `extrapolated=false`.

A configured band may extend beyond the furthest observed level; the reported depth is then still only the sum of observed levels inside that band. It is not labeled complete market depth.

## Determinism and time

`decision_time` is versioned configuration. Input `event_time <= receive_time <= decision_time`; any future input is rejected. The engine does not read wall-clock time for deterministic outputs. Same input/config/code commit must produce byte-identical persisted artifacts and checksums.

## Outputs

### `BookFeatureStateV1`

Descriptive market-book features with identity, sequence, horizon, spread/mid/microprice, top-of-book, depth-band states, cumulative depth, book-quality binding, no-extrapolation evidence, reason codes and `feature_checksum`.

### `SpreadDepthImbalanceEngineStateV1`

Run context, lineage, validation state `VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY`, embedded `BookFeatureStateV1`, uncertainty, metrics, safety and `output_checksum`.

### `SpreadDepthImbalanceEngineAuditV1`

Immutable state/feature/config/gate/upstream checksums, deterministic validation evidence, reason codes, safety and `audit_checksum`.

All outputs preserve:

```text
analysis_only=true
used_for_decision=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## Reference fixture expectations

For the certified reconstructed sequence `1003`:

```text
best_bid = 50024.9 @ 0.9
best_ask = 50025.1 @ 0.65
spread_abs = 0.2
mid = 50025.0
spread_bps = 0.039980009995002498750624687656171914042978510744628...
microprice = 50025.016129032258064516129032258064516129032258065...
```

Depth-band expected quantities:

| band bps | bid qty | ask qty | imbalance |
|---:|---:|---:|---:|
| 0.025 | 0.9 | 0.65 | 0.16129032258064516129032258064516129032258064516129... |
| 0.05 | 0.9 | 1.75 | -0.32075471698113207547169811320754716981132075471698... |
| 0.10 | 1.4 | 2.15 | -0.21126760563380281690140845070422535211267605633803... |

## Lot 42 lock

Lot 41 stops at descriptive spread/depth/imbalance features. `Liquidity Zones, Walls & Voids Engine` remains `PLANNED_LOCKED`. No Lot 42 source, runner, validator, state schema or evidence may be created in this implementation.
