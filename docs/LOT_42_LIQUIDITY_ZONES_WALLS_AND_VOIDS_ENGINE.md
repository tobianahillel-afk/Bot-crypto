# Lot 42 — Liquidity Zones, Walls & Voids Engine

## Status

`IMPLEMENTATION_CANDIDATE_NOT_FROZEN`

Lot 42 is implemented only on the implementation branch created from the exact governance gate merge:

`7456c5b80b609ee5958d8b6da0effd489faa308c`

The implementation remains non-production, offline and non-decisional until its source is fully validated, frozen, merged and independently audited post-merge. Lot 43 remains `PLANNED_LOCKED`.

## Objective

Lot 42 converts certified offline order-book observations into descriptive liquidity structures:

- adjacent observed-level clusters;
- displayed walls;
- persistent zones;
- liquidity voids;
- explicit persistence, replenishment, cancellation and distance-to-mid measurements;
- freshness expiry and fail-closed rejection of stale/ambiguous upstream evidence.

It does **not** infer participant intent, predict price, create signals, approve risk, route orders or trade.

## Canonical authority

- roadmap: `docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md`;
- product scope registry: `data/audit/product_scope_roadmap_lot21.jsonl`, line 43;
- entry gate: `docs/LOT_42_V4_ENTRY_GATE.md`;
- gate checksum: `7ab3b17a74d30866fbec4ec15acfe608a9545e8831d80dcb39db2d059e293924`;
- gate merge: `7456c5b80b609ee5958d8b6da0effd489faa308c`;
- owner: `MicrostructureDomain`;
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.

## Upstream evidence and deterministic history

Lot 42 does not create a second order-book reconstruction engine. Historical observations are reconstructed only through the canonical Lot 39 public reconstructor using:

1. the frozen Lot 38 canonical snapshot at sequence `1001`;
2. the frozen Lot 39 delta fixture;
3. deterministic prefix replay to sequences `1002` and `1003`;
4. exact comparison of the final replay with the frozen Lot 39 reconstructed book;
5. exact binding of that final book to the frozen Lot 41 `BookFeatureStateV1`.

The reference history is therefore `1001 -> 1002 -> 1003`. No network source, synthetic hidden history or mutable external state is consumed by the canonical run.

## Versioned configuration

`config/microstructure/liquidity_zones_walls_and_voids_engine_v1.json` is the only configuration owner for Lot 42 thresholds.

Reference configuration:

- decimal precision: `50`;
- adjacent-level cluster distance: `0.025 bps`;
- historical cluster-match distance: `0.05 bps`;
- displayed-wall minimum notional: `25000`;
- persistent-zone minimum observations: `2`;
- persistent-zone minimum observation ratio: `0.66`;
- liquidity-void minimum adjacent-level gap: `0.03 bps`;
- high-confidence wall maximum cancellation rate: `0.50`;
- maximum age of the certified current Lot 41 feature: `40000 us`.

No business threshold is hidden in operator input, environment state or permissive fallback.

## Mathematical definitions

For positive prices `p1`, `p2` and positive reference price `m`:

`distance_bps(p1,p2;m) = |p1-p2| / m * 10000`.

Adjacent levels are placed in one cluster only when their pairwise distance is less than or equal to the configured cluster-distance threshold.

For cluster levels `(p_i, q_i)`:

- quantity: `Q = sum(q_i)`;
- notional: `N = sum(p_i * q_i)`;
- quantity-weighted anchor: `A = N / Q`.

All arithmetic uses `Decimal`. Prices and quantities entering Lot 42 through JSON boundaries must remain decimal strings; silent float/int coercion is rejected.

## Historical matching

Current clusters are matched one-to-one against each historical observation by smallest anchor-price bps distance, under the versioned historical-match threshold. The greedy assignment is deterministic because candidate pairs are sorted by:

1. distance;
2. current-cluster index;
3. historical-cluster index.

A historical cluster cannot satisfy two current clusters in the same observation.

## Persistence

For a current zone:

`persistence_ratio = matched_observations / total_observations`.

A zone is classified `PERSISTENT_ZONE` when both are true:

- `matched_observations >= persistent_min_observations`;
- `persistence_ratio >= persistent_min_ratio`.

A current cluster that does not meet any Lot 42 classification is omitted from the active zone set. An empty active zone set is valid if the evidence supports no zone; lack of a detected zone is not itself a data-quality failure.

## Replenishment and cancellation

For two successive matched quantities `q_(t-1)` and `q_t`, absent observations contribute zero quantity only to the historical measurement itself; they never synthesize a book level.

Per transition:

- replenished quantity: `max(q_t - q_(t-1), 0)`;
- cancelled quantity: `max(q_(t-1) - q_t, 0)`;
- normalization base: `max(q_(t-1), q_t)`.

Across the available history:

- `replenishment_ratio = sum(replenished) / sum(base)`;
- `cancellation_rate = sum(cancelled) / sum(base)`.

If the normalization base is zero, both ratios are explicitly `0` because no displayed quantity existed in either side of any measured transition.

These quantities are Lot 42 descriptive attributes. They do not implement the Lot 43 Book Resilience & Replenishment Engine and do not infer intent.

## Displayed wall classification

A current observed cluster is `DISPLAYED_WALL` when its current notional is greater than or equal to the configured wall-notional threshold.

Wall confidence is a deterministic qualitative status, **not a probability**:

- `HIGH_CONFIDENCE` only when the persistence ratio meets its threshold and cancellation rate is no greater than the configured maximum;
- otherwise `LOW_CONFIDENCE`.

The canonical acceptance case “instantaneously cancelled wall” is represented by a wall whose displayed quantity sharply contracts between consecutive observations while remaining present. Such a wall is `LOW_CONFIDENCE` when its cancellation rate exceeds the configured confidence threshold.

## Liquidity voids

For each side independently, consecutive currently observed levels are scanned in canonical book order. A `LIQUIDITY_VOID` is emitted when their bps gap is greater than or equal to the configured void threshold.

Void detection is bilateral: the same rule applies independently to BID and ASK. The canonical frozen reference may contain a void on only one side; synthetic contract tests must prove detection on both sides.

A void describes sparse displayed depth. It is not a forecast that price will traverse the gap.

## Expiry

The engine is fail-closed on stale current upstream evidence. Historical wall candidates that no longer have a matching current cluster are counted as expired candidates; they are not retained as active zones.

There is no silent persistence of a disappeared wall and no hidden grace period.

## Contracts

Outputs:

- `LiquidityZonesWallsVoidsEngineStateV1`;
- `LiquidityZonesWallsVoidsEngineAuditV1`;
- `LiquidityZoneSetV1`.

Critical nested contracts:

- `LiquidityZoneV1`;
- `LiquidityVoidV1`;
- `Lot42RunContextV1`;
- `Lot42LineageEnvelopeV1`;
- `Lot42MetricsV1`.

All runtime contracts are immutable dataclasses and have closed JSON Schemas.

## Checksums and lineage

Every zone and void receives a canonical SHA-256 checksum over its checksum-free payload. The zone set, engine state and audit are independently checksummed.

Lineage binds:

- Lot 42 entry-gate checksum;
- frozen Lot 41 state, audit and feature checksums;
- frozen Lot 39 book checksum;
- frozen Lot 39 delta-fixture file checksum;
- frozen Lot 38 snapshot checksum;
- Lot 42 config checksum;
- upstream availability time;
- exact code commit through `RunContextV1`.

## Persistence

The runner writes exactly three canonical runtime artifacts with the repository atomic JSON writer:

- `data/audit/liquidity_zones_walls_and_voids_engine_lot42.json`;
- `data/audit/liquidity_zones_walls_and_voids_engine_audit_lot42.json`;
- `data/audit/liquidity_zone_set_lot42.json`.

Repeated execution at the same source commit and inputs must produce byte-equivalent semantic payloads and identical checksums.

## Reference outcome before freeze

The versioned fixture is expected to produce:

- history sequences: `1001, 1002, 1003`;
- current sequence: `1003`;
- current mid: `50025`;
- active zones: `3`;
- displayed walls: `3`;
- persistent zones: `2`;
- low-confidence walls: `1`;
- liquidity voids: `1`, on BID;
- participant intent inferred: `false`;
- trade allowed: `false`;
- execution allowed: `false`;
- approved size: `0`.

These values remain implementation-candidate expectations until recomputed and frozen on an exact source head.

## Failure behavior

Lot 42 rejects or blocks computation on:

- invalid or changed gate evidence;
- incompatible lifecycle state;
- changed frozen Lot 41/39/38 checksums;
- unhealthy or vetoed Lot 41 book-quality binding;
- extrapolated Lot 41 depth;
- stale or future current evidence;
- malformed decimal strings or numeric coercion;
- invalid sequence history;
- non-SYNCED prefix reconstruction;
- divergence between canonical prefix replay and frozen Lot 39 book;
- market identity changes inside one historical chain;
- crossed or locked observation;
- invalid ratios, classifications, checksums or safety fields.

There is no error-to-success conversion.

## Explicit non-goals

Lot 42 does not implement:

- Lot 43 resilience scoring;
- aggressor classification;
- order flow, delta or CVD;
- hidden-liquidity inference;
- stop-zone or liquidation-pool inference;
- sweep/fakeout/trap classification;
- derivatives context;
- game-theory scenario aggregation;
- forecasts;
- signals;
- risk approval;
- order routing;
- trading;
- execution;
- participant intent as fact.

## Promotion

The source must pass exact-head lint/type/architecture/security/full regression, critical coverage `>=95% lines / >=90% branches`, mutation `>=80%`, no timeouts/suspicious mutants, and at least three anti-flake repetitions.

Only then may the exact source head be frozen and runtime/coverage/mutation evidence committed. The implementation PR must then pass the frozen-evidence checks and merge. A separate independent post-merge Lot 42 audit is required before release `0.42.0`, lifecycle closure or any Lot 43 gate.
