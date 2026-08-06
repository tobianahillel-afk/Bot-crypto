# Lot 30 — V2 Market Analysis Closure

Status: `IMPLEMENTATION_IN_PROGRESS`

Runtime ceiling: `LOCAL_OFFLINE_ANALYSIS_ONLY`

Owner: `MarketAnalysisDomain`

## Purpose

Lot 30 closes V2 without creating a new market state, forecast, signal, risk decision,
trade intent, order intent or execution permission. It converts the validated Lot 29 replay
evidence into a final, deterministic and fail-closed V2 closure.

The Lot 29 state remains the canonical aggregate proof for Lots 21–28. Lot 30 does not
reimplement or reinterpret those lots. It independently verifies their referenced files,
validates Lot 29 twice, checks the current lifecycle and publishes a final closure manifest
covering Lots 21–30.

## Canonical inputs

- `data/audit/v2_deterministic_replay_and_audit_lot29.json`;
- `data/audit/v2_deterministic_replay_and_audit_audit_lot29.json`;
- `data/audit/v2_replay_closure_manifest_lot29.json`;
- `data/audit/roadmap_lifecycle_overlay_lot29.json`;
- all eight immutable artefacts referenced by the Lot 29 state;
- `scripts/validate_lot29.py` executed twice on the exact repository head;
- `config/closure/v2_market_analysis_closure_v1.json`.

## Canonical outputs

- `V2MarketAnalysisClosureStateV1`;
- `V2MarketAnalysisClosureAuditV1`;
- `V2FinalClosureManifestV1`;
- `data/audit/v2_market_analysis_closure_lot30.json`;
- `data/audit/v2_market_analysis_closure_audit_lot30.json`;
- `data/audit/closure_manifest_lot30.json`;
- `reports/lot_30_v2_market_analysis_closure_report.md`.

## Self-reference rule

A closure cannot validate its own persisted output before that output exists. The final
manifest therefore separates:

```text
upstream_lot_sequence = 21..28
 direct_validated_lot = 29
          closure_lot = 30
 covered_lot_sequence = 21..30
```

Lots 21–28 are covered through the immutable Lot 29 replay manifest. Lot 29 is directly
validated twice. Lot 30 is covered by its strict schema, deterministic replay, persisted
state validator, negative controls, exact-head CI and human review.

## Mandatory processing sequence

1. Validate the Lot 30 configuration and fail-closed safety policy.
2. Load the Lot 29 state, audit, closure manifest and lifecycle overlay.
3. Recompute the Lot 29 state checksum and verify state/audit/manifest linkage.
4. Verify the Lot 29 replay status, lot sequence and artifact/validator counts.
5. Recompute the file checksum and byte size of every referenced Lot 21–28 artifact.
6. Verify any embedded output checksum against the referenced artifact.
7. Execute `scripts/validate_lot29.py` twice and require identical stdout checksums.
8. Execute all five negative controls and require `PASS` for each one.
9. Build the final chain checksum from the immutable upstream checksums, the three Lot 29
   evidence files, the deterministic validator output and the covered lot sequence.
10. Build the state twice and require byte-for-byte canonical equality.
11. Persist state, audit and manifest atomically.
12. Validate the persisted outputs independently before promotion.

## Negative controls

The following controls are mandatory and versioned:

| Control | Expected consequence |
|---|---|
| `SCHEMA_MISMATCH_REJECTED` | unsupported config is rejected |
| `UPSTREAM_CHECKSUM_TAMPER_REJECTED` | modified evidence is rejected |
| `FORBIDDEN_CAPABILITY_REJECTED` | any permission increase is rejected |
| `VALIDATOR_DIVERGENCE_REJECTED` | non-deterministic validation is rejected |
| `LIFECYCLE_UNLOCK_REJECTED` | unauthorized Lot 30 activation is rejected |

A negative control that does not reject is itself a closure failure.

## Final checksum

The final chain checksum is the canonical SHA-256 of:

```text
ordered Lot 21–28 artefact checksums
+ Lot 29 state file checksum
+ Lot 29 audit file checksum
+ Lot 29 closure file checksum
+ deterministic Lot 29 validator stdout checksum
+ covered lot sequence 21..30
```

The output checksum is the canonical SHA-256 of the complete Lot 30 state excluding only
its `output_checksum` field.

## Safety invariants

```text
analysis_only=true
used_for_decision=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

The following capabilities remain locked:

- `ContinuousMarketStateV1`;
- `MultiHorizonForecastV1`;
- `ParticipantBehaviorScenarioV1`;
- `TradeIntent`;
- `RiskDecisionV1`;
- `RiskReservationV1`;
- `OrderIntent`.

No unknown, missing, stale, divergent or malformed state may be converted into permission.

## Failure modes

- unsupported configuration schema → `BLOCKED_CONFIG`;
- missing or changed upstream artifact → `UPSTREAM_EVIDENCE_MISMATCH`;
- Lot 29 checksum/linkage mismatch → `UPSTREAM_CLOSURE_INVALID`;
- validator non-zero result → `UPSTREAM_VALIDATOR_FAILED`;
- validator output divergence → `NON_DETERMINISTIC_FAIL`;
- unauthorized lifecycle advance → `LIFECYCLE_GATE_VIOLATION`;
- negative control not rejected → `NEGATIVE_CONTROL_FAILURE`;
- persisted state or audit mismatch → `PERSISTED_EVIDENCE_INVALID`.

Every failure is fail-closed and produces no valid Lot 30 output.

## Non-goals

- no V3 ingestion or source registry;
- no exchange connection;
- no market prediction;
- no probability or expected-return claim;
- no strategy or signal;
- no portfolio sizing;
- no paper, sandbox or live execution;
- no automatic unlock of Lot 31.

## Definition of done

- code, configuration, schema, scripts, tests and documentation exist;
- state/audit/manifest are generated and independently validated;
- deterministic replay is `MATCH`;
- all five negative controls pass;
- full regression, line/branch coverage, Ruff, mypy, architecture, traceability, security,
  dependency audit, mutation and three anti-flake repetitions pass on the exact PR head;
- a human-reviewed report records limitations and the final checksum;
- Lot 31 remains locked until a separate post-merge audit and entry gate.
