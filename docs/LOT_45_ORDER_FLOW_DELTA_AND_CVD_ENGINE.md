# Lot 45 — Order Flow, Delta & CVD Engine

## Scope

Lot 45 consumes the frozen Lot 44 classified trades and produces deterministic, offline-only order-flow, signed-delta and cumulative-volume-delta artifacts. It remains inside `MicrostructureDomain` and `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.

This lot is descriptive research infrastructure only. Its outputs cannot authorize a signal, a risk decision, an order, a trade or an execution.

## Certified prerequisite

Implementation begins only after the merged Lot 45 V4 entry gate at `390d0779f2be257fa8134faf8f02193a760a09c3`, which is itself bound to `GO_LOT44_POST_MERGE`.

Frozen upstream identities used by the reference build:

- Lot 44 state checksum: `1a461cef0bedc0e2b34185ff538a64b1b53373b12b0633b749a34cee2b3c5541`
- Lot 44 audit checksum: `03ceda1c49746509f95e7f2ed039e8cc321e8e3cb4adbb946f1aef4ed3eba07d`
- Lot 44 confidence checksum: `7cb11e078d7f0d9ed0858229d8c6fe31a7cf653a238b280b05dbdd84d1250f05`
- Lot 44 post-merge checksum: `b8b531b2fcb09a30728549cc480d54d9be71504356468704c102ff085c39ea9a`

## Runtime contracts

Inputs:

- `RunContextV1`
- `LineageEnvelopeV1`
- frozen `ClassifiedTradeV1` records from Lot 44

Outputs:

- `OrderFlowDeltaCVDEngineStateV1`
- `OrderFlowDeltaCVDEngineAuditV1`
- `OrderFlowStateV1`
- `CVDSeriesV1`

All Python runtime contracts are frozen dataclasses. Sequence fields are defensively copied to tuples and safety mappings are copied to immutable mapping proxies.

## Event-time windowing

The reference policy uses fixed tumbling event-time windows of `1_000_000` microseconds. Trades are sorted deterministically by:

1. event time;
2. receive time;
3. trade id.

A window is identified from the trade event time, never from arrival order. The window event timestamp is the maximum source event timestamp in the window, and its receive timestamp is the maximum source receive timestamp.

No calculation may use a future trade or future state.

All published Lot45 timestamp fields use one canonical representation: a real Gregorian calendar date, UTC `Z`, and exactly six fractional-second digits. Schema constraints reject impossible calendar dates such as 31 February and apply the Gregorian leap-year rule in addition to the canonical text constraint. Runtime parsing and published schemas therefore accept the same timestamp domain. That domain is not narrowed by the Unix epoch: canonical Gregorian instants before 1970 are represented internally with signed microsecond offsets and retain the same deterministic tumbling-window semantics.

Every causal ordering check first passes `event_time`, `receive_time` and `generated_at` through the Lot45 canonical timestamp parser. A timestamp that is causally ordered but textually non-canonical cannot enter a valid Lot45 state.

## Order-flow accounting

For each window the engine preserves three disjoint classes:

- `BUY_AGGRESSOR`
- `SELL_AGGRESSOR`
- `UNKNOWN`

Volume conservation is mandatory:

`total_volume = buy_volume + sell_volume + unknown_volume`

Signed delta is:

`signed_delta = buy_volume - sell_volume`

UNKNOWN volume is never imputed to either side and therefore contributes exactly zero signed volume.

The conservative signed imbalance is:

`signed_imbalance = signed_delta / total_volume`

so UNKNOWN remains in the denominator rather than being silently removed.

## Numerical determinism

Every Decimal-derived calculation and every Decimal-derived model invariant executes under one complete Lot45 context. The context freezes precision, `ROUND_HALF_EVEN`, `Emin`, `Emax`, clamp and the trap policy. Caller/thread ambient Decimal settings therefore cannot alter a calculation, validation decision or checksum. Ambient `Inexact`/`Rounded` traps and hostile exponent limits are explicit adversarial test cases.

## Coverage and confidence

Classification coverage is:

`(buy_volume + sell_volume) / total_volume`

Confidence-weighted coverage is:

`sum(trade_quantity * classification_confidence) / total_volume`

Both are descriptive diagnostics, not probabilities of future price direction and not trading signals.

The configured `max_unknown_volume_ratio` is explicit and versioned. Exceeding it blocks publication fail-closed.

## Delta impulse

Within a session:

`delta_impulse[t] = signed_delta[t] - signed_delta[t-1]`

For the first window of a session, impulse equals that window's signed delta. The calculation therefore depends only on the current and immediately previous event-time window.

## CVD

CVD is accumulated in the same deterministic event-time window order:

`cvd[t] = cvd[t-1] + signed_delta[t]`

The reference session policy is `lot45-utc-day-session-v1`. CVD resets to zero at an explicit UTC calendar-day boundary before applying the first window of the new session.

Every CVD point binds one-to-one to an `OrderFlowWindowV1` through its `window_checksum`.

## Lineage and checksums

The state lineage binds the exact Lot 45 entry gate merge and frozen Lot 44 state, audit, confidence, config and post-merge evidence.

Every window has a canonical checksum. Order-flow and CVD artifacts have independent canonical checksums. The engine state binds both, and the audit binds state, config, gate and upstream Lot 44 checksums.

Canonical JSON serialization uses sorted keys and compact separators through the repository's canonical checksum helper.

The claimed `code_commit` binds the executable Python tree, but an in-process check alone cannot establish startup integrity because Python imports `sitecustomize`/`usercustomize` before the runner module executes. Therefore every **certified** Lot45 Python launch is mediated by `scripts/lot45_trusted_prelaunch.sh`. The trusted shell wrapper resolves the exact claimed commit, proves the bound tracked/working/staged tree is unchanged, and inspects `src/` with ignored and untracked paths included **before Python starts**. Any unexpected source-tree object therefore fails closed, including self-deleting startup source, sourceless `.pyc`/`.pyo`, native `.so`/`.pyd`, symlinks, packages or other ignored/untracked startup artifacts. Only after this pre-launch proof does the wrapper start Python with the repository `src` path explicitly set, user-site disabled, safe-path enabled and bytecode writes disabled. The in-process `*.py` inventory remains a second defense, not the certification root of trust.

## Persistence

The runner calls the engine's `write_lot45_artifacts`, which writes all four final artifacts using the repository `atomic_write_json` primitive. Direct non-atomic `Path.write_text` persistence is not used for Lot 45 evidence.

## Fail-closed conditions

Publication/attestation is rejected when, among other cases:

- gate or frozen Lot 44 evidence changes;
- source lineage/checksums diverge;
- the trusted pre-launch source tree differs from the claimed `code_commit`;
- any ignored/untracked object exists below the certified `src/` root before Python startup;
- an executable Python source under `src/` is absent from the claimed `code_commit` tree;
- input is stale or causally impossible;
- a timestamp is non-canonical or not a real Gregorian calendar instant;
- schema/config/policy version changes unexpectedly;
- trade identities are mixed;
- trade ids collide;
- volume/count conservation fails;
- UNKNOWN ratio exceeds the explicit policy;
- CVD recurrence or session reset is inconsistent;
- any safety permission is enabled;
- Lot 46 implementation appears before the Lot 45 post-merge gate.

## Downstream lock

Lot 46 — Trade Classification Confidence Engine remains `PLANNED_LOCKED` until Lot 45 has completed dedicated validation, mutation assurance, frozen evidence, final exact-head review, merge, and independent post-merge audit with an explicit `GO_LOT45_POST_MERGE` verdict.