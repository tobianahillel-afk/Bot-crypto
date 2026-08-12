# Lot 43 — Book Resilience & Replenishment Engine

## 1. Identity

- Lot: `43`
- Version: `V4_MICROSTRUCTURE_LIQUIDITY`
- Owner: `MicrostructureDomain`
- Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- Gate merge: `ed8845e0e56151348fe57c0e9bceaf4646ea49aa`
- Gate checksum: `4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d`
- Audited predecessor: Lot 42 / release `0.42.0`
- Next lot: Lot 44, `PLANNED_LOCKED`

## 2. Falsifiable objective

Given the certified deterministic L2 observation history already used by Lot 42, detect sufficiently large observed depletion events, measure whether observable liquidity subsequently returns at the same price or an adjacent price, distinguish structural mid-price displacement from quantity replenishment, and publish side/horizon resilience measurements conditioned by an explicitly defined local observed-book volatility bucket.

The implementation is correct only if every reported depletion, recovery, elapsed time, recovery fraction, horizon status and volatility bucket can be replayed exactly from the frozen Lot 38 snapshot plus Lot 39 deltas without network data or inferred participant intent.

## 3. Non-goals and forbidden authority

Lot 43 does not infer why liquidity changed and never attributes a cancellation or replenishment to a participant. It does not classify aggressor trades, compute CVD/order flow, infer hidden liquidity, infer stops, generate scenarios, forecasts or signals, approve risk, route orders, trade or execute.

`trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.

## 4. Canonical inputs

Lot 43 binds to:

- merged Lot 43 gate and checksum;
- `roadmap_lifecycle_overlay_lot42.json`;
- frozen Lot 42 engine state, audit and `LiquidityZoneSetV1`;
- frozen Lot 42 config;
- frozen Lot 38 snapshot state;
- frozen Lot 39 reconstructed book and delta fixture;
- deterministic decision time from versioned Lot 43 config.

The observation history is reconstructed through the already-certified Lot 39/Lot 42 path. No external ingestion is introduced. Every certified observation used by Lot 43 must have `receive_time <= decision_time`; observations newer than the injected decision boundary fail closed before volatility or outcome computation.

## 5. Output contracts

### `BookDepletionEventV1`

A deterministic observed depletion record containing:

- side and depleted price;
- prior and post-depletion quantities;
- depleted quantity and depletion ratio;
- depletion sequence/timestamps;
- first qualifying replenishment classification, if any;
- replenishment sequence/time/quantity when observed;
- recovered fraction capped at the depleted quantity;
- directional mid shift in bps;
- maximum-window status;
- explicit participant intent `NOT_INFERRED`;
- reason codes and checksum.

Depletion timestamps are UTC `Z` timestamps with `depletion_event_time <= depletion_receive_time`. When a replenishment sequence exists, it must be strictly greater than the depletion sequence.

### `BookResilienceSliceV1`

A side/horizon/volatility-bucket aggregation containing:

- side;
- horizon in microseconds;
- volatility bucket and method;
- depletion event count;
- recovered, mid-shifted, expired and pending counts;
- versioned `replenishment_min_recovery_ratio` used to derive the descriptive status;
- mean recovered fraction or `null` when there are no events;
- mean observed replenishment time in microseconds or `null` when no quantity recovery exists;
- descriptive resilience status;
- reason codes and checksum.

The slice is self-descriptive: direct model validation can reproduce the same `RESILIENT` threshold decision as the analysis without hardcoding a policy value.

### `BookResilienceStateV1`

The published Lot 43 analytical state containing identity/time/sequence information, reconstructed history IDs, the exact configured `resilience_horizons_us` set, the local observed-book volatility measurement, all depletion events and all resilience slices. Direct construction must contain exactly one `BID` and one `ASK` slice for every declared horizon; omitting both sides for a configured horizon is invalid and fails closed.

### Engine state/audit

- `BookResilienceReplenishmentEngineStateV1`
- `BookResilienceReplenishmentEngineAuditV1`

Both bind exact lineage, safety, deterministic metrics and canonical checksums.

## 6. Mathematical definitions

All sensitive numerical operations use `Decimal` under `calculation_decimal_precision=50`.

### 6.1 Depletion

For a side and exact price level `p` across consecutive certified observations `t-1` and `t`:

`q_prev = observed quantity at p in t-1`

`q_now = observed quantity at p in t, or 0 if the level disappeared`

`depleted_quantity = max(q_prev - q_now, 0)`

For `q_prev > 0`:

`depletion_ratio = depleted_quantity / q_prev`

A depletion event exists only when both:

- `depleted_quantity >= depletion_min_quantity`;
- `depletion_ratio >= depletion_min_ratio`.

Reference thresholds are versioned config values:

- `depletion_min_quantity=0.1` base units;
- `depletion_min_ratio=0.25`.

A small observed decrease below either threshold is not promoted to a Lot 43 depletion event.

### 6.2 Same-price replenishment

Let the post-depletion observation be the baseline. At any later certified observation inside the maximum configured window:

`same_gain = max(q_future(p) - q_baseline(p), 0)`

`same_recovery_fraction = min(same_gain, depleted_quantity) / depleted_quantity`

Same-price replenishment qualifies when:

`same_recovery_fraction >= replenishment_min_recovery_ratio`.

### 6.3 Adjacent-price replenishment

For prices `p_i != p` whose distance from depleted price is within `adjacent_replenishment_distance_bps`, compare future quantity with the post-depletion baseline quantity at the same exact price:

`adjacent_gain = sum(max(q_future(p_i) - q_baseline(p_i), 0))`

`adjacent_recovery_fraction = min(adjacent_gain, depleted_quantity) / depleted_quantity`

Adjacent replenishment qualifies when the recovery fraction is at least the configured minimum.

Same-price evidence takes precedence over adjacent-price evidence at the same future observation because it is the more specific match. This precedence is deterministic and not an inference of participant intent.

### 6.4 Mid-shift classification

Mid shift is not quantity replenishment. It is a separate structural outcome when no qualifying same/adjacent recovery exists at an observation.

For a BID depletion:

`directional_mid_shift_bps = max(mid_baseline - mid_future, 0) / mid_baseline * 10000`

For an ASK depletion:

`directional_mid_shift_bps = max(mid_future - mid_baseline, 0) / mid_baseline * 10000`

A `MID_SHIFT` outcome qualifies at or above `mid_shift_min_bps`.

For `MID_SHIFT`, replenished quantity remains `0` and recovered fraction remains `0`; no quantity recovery is fabricated.

### 6.5 Replenishment elapsed time

Elapsed time is based on certified `receive_time`, not wall-clock time:

`replenishment_time_us = receive_time_replenishment - receive_time_depletion`

It must be strictly positive. If no qualifying recovery or mid shift is observed, the value is `null`, never zero. A replenishment observation must also have `replenishment_sequence_id > depletion_sequence_id`.

For any published recovery or mid-shift evidence:

`replenishment_time_us <= decision_time - depletion_receive_time`

Evidence whose implied receive time is after the injected `decision_time` is future evidence and fails closed, even if its elapsed time would otherwise fit a configured resilience horizon.

### 6.6 Maximum-window status

Let `H_max` be the largest configured resilience horizon and `decision_time` the injected deterministic decision time.

- qualifying same/adjacent recovery within `H_max` -> `REPLENISHED`;
- qualifying mid shift within `H_max` -> `MID_SHIFTED`;
- no qualifying event and age at decision `>= H_max` -> `EXPIRED_NO_REPLENISHMENT`;
- otherwise -> `PENDING_WINDOW`.

Observations after `H_max` cannot retroactively count as replenishment.

### 6.7 Horizon-specific outcome

For each configured horizon `H` and depletion event:

- same/adjacent recovery with elapsed time `<=H` -> recovered;
- mid shift with elapsed time `<=H` -> shifted;
- otherwise, if age at decision `>=H` -> expired;
- otherwise -> pending.

This is evaluated independently per horizon. Horizons are never voted together. The state publishes the authoritative configured horizon tuple as `resilience_horizons_us`, and the slice matrix must be exactly `BID/ASK × resilience_horizons_us`. Every event sequence referenced by the state must exist in `history_sequence_ids`; the event `max_window_status` must equal the outcome recomputed at the largest declared horizon; quantity-recovery events must meet the single published `replenishment_min_recovery_ratio`.

### 6.8 Recovered fraction

For qualifying same/adjacent quantity recovery:

`recovered_fraction = min(replenished_quantity, depleted_quantity) / depleted_quantity`

Domain is `[0,1]`. It is not a probability.

### 6.9 Resilience slice aggregation

For each `side x horizon`:

- `depletion_events_total` = number of observed depletion events on that side;
- `recovered_events_total` = quantity recoveries within horizon;
- `mid_shift_events_total` = qualifying structural shifts within horizon;
- `expired_events_total` = closed horizons without qualifying outcome;
- `pending_events_total` = horizons not yet closed;
- `replenishment_min_recovery_ratio` = strictly positive versioned threshold used by this slice;
- `mean_recovered_fraction` = arithmetic mean over all depletion events, counting non-recovered events as `0`; `null` if no depletion events exist;
- `mean_replenishment_time_us` = arithmetic mean over quantity-recovered events only; `null` if no quantity recovery exists.

Descriptive `resilience_status` is deterministic:

- no depletion events -> `NO_EVENTS`;
- all events quantity-recovered and mean recovered fraction >= the slice's versioned `replenishment_min_recovery_ratio` -> `RESILIENT`;
- all events expired with no recovery/shift -> `FRAGILE`;
- all resolved outcomes are mid shifts with no quantity recovery and no pending event -> `SHIFTED`;
- pending events with no resolved event -> `PENDING`;
- otherwise -> `PARTIAL`.

These labels are descriptive state labels, not probabilities or trade signals.

## 7. Volatility conditioning

Lot 43 does not claim ownership of a broad market-regime model. It publishes a narrowly named local conditioning bucket derived only from the same certified book observations:

`OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS`

For consecutive observation mids:

`move_i = abs(mid_i - mid_{i-1}) / mid_{i-1} * 10000`

`volatility_measure_bps = max(move_i)`

Bucket:

- `QUIET` when measure `<= quiet_max_mid_move_bps`;
- `STRESSED` when measure `>= stressed_min_mid_move_bps`;
- otherwise `NORMAL`.

Reference thresholds:

- quiet max `0.05 bps`;
- stressed min `0.5 bps`.

The method and thresholds are versioned and output explicitly. The bucket is context only and has no signal/execution authority.

## 8. Reference fixture expectation

Certified history:

- seq1001 receive `50ms`;
- seq1002 receive `60ms`;
- seq1003 receive `70ms`;
- deterministic decision time `100ms`.

Reference significant depletion:

- side: `BID`;
- price: `50024.8`;
- prior quantity: `1.25`;
- post-depletion quantity: `0`;
- depleted quantity: `1.25`;
- depletion ratio: `1`;
- depletion sequence: `1003`.

No future certified observation exists after seq1003. With horizons `10,000us` and `25,000us`, age at decision is `30,000us`, so both horizons are closed without replenishment.

Expected reference result:

- observations: `3`;
- declared resilience horizons: `[10,000us, 25,000us]`;
- depletion events: `1`;
- same-price replenishments: `0`;
- adjacent-price replenishments: `0`;
- mid shifts: `0`;
- expired max-window events: `1`;
- volatility measure: `0 bps`;
- volatility bucket: `QUIET`;
- BID resilience at both horizons: `FRAGILE`;
- ASK resilience at both horizons: `NO_EVENTS`.

## 9. Failure and degraded behavior

Fail closed on:

- invalid gate or lifecycle;
- checksum drift;
- non-healthy/unlinked Lot 42 predecessor evidence;
- stale input beyond configured age;
- any observation with `receive_time > decision_time`;
- non-bilateral/crossed observations;
- non-increasing sequence history;
- malformed, non-UTC or non-causal timestamps;
- invalid decimal text, non-finite values or negative quantities;
- duplicate/unsorted/empty declared horizons;
- incomplete or duplicate `BID/ASK × resilience_horizons_us` slice matrix;
- invalid ratio/threshold domains;
- ambiguous identity changes;
- replenishment timestamp before/at depletion;
- replenishment evidence whose implied receive time exceeds `decision_time`;
- replenishment sequence not strictly greater than depletion sequence;
- Lot 44 implementation presence.

No error path converts missing data into successful replenishment.

## 10. Expected implementation files

- `src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py`
- `src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py`
- `src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py`
- `src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_analysis.py`
- `config/microstructure/book_resilience_and_replenishment_engine_v1.json`
- three closed output JSON schemas;
- runner, validator and no-connectivity validator;
- targeted tests and negative tests;
- deterministic audit artifacts only after exact source-head quality gates pass;
- implementation report only after source evidence is frozen.

## 11. Definition of Done

Lot 43 source is not frozen until the same exact source head passes:

- exact gate ancestry;
- Lot 44 absence;
- Ruff and MyPy;
- closed schema validation;
- deterministic replay;
- critical line coverage >=95%;
- critical branch coverage >=90%;
- mutation >=80% with zero timeout/suspicious;
- negative/fail-closed tests;
- domain/roadmap/traceability gates;
- no-connectivity, Bandit and dependency audit;
- full regression;
- 3 anti-flake repetitions.

After merge, an independent Lot 43 post-merge audit is mandatory before any Lot 44 gate may be created.
