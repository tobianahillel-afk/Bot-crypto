# Lot 45 — Order Flow, Delta & CVD Engine Report

Status: **IMPLEMENTATION CANDIDATE — NOT YET FROZEN**

## Objective

Implement the canonical V4 Lot45 order-flow, signed-delta and CVD processing boundary on top of the frozen Lot44 classified-trade evidence while remaining strictly offline, deterministic and non-executable.

## Certified entry

- Lot44 post-merge verdict: `GO_LOT44_POST_MERGE`
- Lot45 entry-gate merge: `390d0779f2be257fa8134faf8f02193a760a09c3`
- Lot45 entry-gate artifact: `9220665913`
- Lot45 entry-gate artifact digest: `sha256:ed5f6eb4d129a2071699240093b4ace78bb84b88dd281f5a3649ac8664617a4e`

## Implemented responsibilities

- deterministic event-time tumbling windows;
- BUY/SELL/UNKNOWN count and volume conservation;
- signed delta and conservative signed imbalance;
- delta impulse without future state;
- CVD accumulation with explicit UTC-day session reset;
- classification and confidence coverage diagnostics;
- frozen Lot44 lineage/checksum validation;
- strict safety mapping and Lot46 lock;
- canonical per-window/order-flow/CVD/state/audit checksums;
- atomic persistence for all final Lot45 JSON artifacts.

## Reference policy

- config: `lot45-order-flow-delta-cvd-config-v1`
- policy: `lot45-order-flow-delta-cvd-policy-v1`
- window policy: `lot45-event-time-tumbling-v1`
- session policy: `lot45-utc-day-session-v1`
- window size: 1,000,000 microseconds
- max upstream age: 2,000,000 microseconds
- max UNKNOWN volume ratio: 0.5
- Decimal calculation precision: 50

## Reference Lot44 input expectation

The frozen reference contains three trades and conserves:

- total volume: `0.16`
- BUY volume: `0.08`
- SELL volume: `0.03`
- UNKNOWN volume: `0.05`
- signed delta: `0.05`
- UNKNOWN ratio: `0.3125`
- classification coverage: `0.6875`
- confidence-weighted coverage: `0.6875`

These values remain provisional until the dedicated Lot45 source validator produces and freezes the exact artifact checksums for the final source candidate.

## Adversarial coverage

Tests cover shuffled/out-of-order events, UNKNOWN signed neutrality, multiple windows, delta impulse recurrence, UTC session resets, mixed-identity rejection, alias mutation resistance, CVD recurrence rejection, canonical signed zero, invalid thresholds, causal timestamps and schema closure/safety bindings.

## Certification still required

This report does **not** declare Lot45 complete. Remaining mandatory sequence:

1. generic PR CI and source corrections;
2. select immutable source candidate;
3. dedicated Lot45 validation and coverage;
4. dedicated mutation assurance;
5. freeze generated state/audit/order-flow/CVD and quality summaries;
6. frozen validator + attestation;
7. exact-head matrix;
8. final Codex review and recursive corrections;
9. merge;
10. independent post-merge audit and exact `GO_LOT45_POST_MERGE`.

Lot46 remains locked until step 10 succeeds.
