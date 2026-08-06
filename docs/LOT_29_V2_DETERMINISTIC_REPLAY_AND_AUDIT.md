# Lot 29 — V2 Deterministic Replay & Audit

## Purpose

Lot 29 closes the validated V2 analysis chain by proving that the certified artefacts from Lots 21–28 form one ordered, deterministic and non-executable replay chain.

This lot does not calculate a new market state. It verifies existing evidence, executes every canonical validator, records exact file checksums, produces a closure manifest, and fails closed on the first divergence.

## Scope

The canonical lot sequence is fixed and complete:

```text
21 Product Scope Lock
22 Market Analysis Foundation
23 Technical Indicators
24 Trend / Range / Momentum
25 Volatility / Regime / Confluence
26 Multi-Timeframe Alignment
27 Global Market Context
28 Explanation Core / Why-Not-Trade
```

Exactly one certified `data/audit/*.json` artefact and one canonical validator are registered for every lot.

## Contracts

### Inputs

- versioned replay configuration `v2-deterministic-replay-audit-config-v1`;
- the eight ordered audit artefacts;
- validators `scripts/validate_lot21.py` through `scripts/validate_lot28.py`;
- exact Git commit SHA.

### Outputs

- `V2DeterministicReplayAuditStateV1`;
- `V2DeterministicReplayAuditAuditV1`;
- `ClosureManifestV1`;
- final human-readable report.

## Processing sequence

1. Validate the closed configuration and fail-closed safety policy.
2. Load Lots 21–28 in exact numeric order.
3. Reject missing, non-object, oversized or safety-incompatible artefacts.
4. Compute the SHA-256 of every complete artefact file.
5. Execute every canonical validator with bounded output and timeout.
6. Record validator command, return code, status and stdout/stderr checksum.
7. Compute the ordered chain checksum.
8. Build the state twice and require byte-equivalent canonical output.
9. Persist state, audit, closure manifest and report atomically.
10. Re-read persisted evidence and independently validate checksums, identities, order and safety.

## Fail-closed conditions

The closure is refused when any of the following occurs:

- missing or malformed configuration;
- lot sequence different from 21–28;
- duplicate or non-audit artefact path;
- non-canonical validator path;
- missing, malformed or non-object artefact;
- changed file checksum or embedded checksum type;
- validator non-zero return code, timeout or oversized output;
- validator identity or count mismatch;
- state, audit or closure checksum divergence;
- replay status different from `MATCH`;
- any decision, trading or execution permission enabled.

## Deterministic reason codes

```text
V2_ARTIFACT_CHAIN_MATCH
V2_VALIDATORS_PASS
V2_OFFLINE_ONLY
```

## Security boundary

```text
analysis_only=true
used_for_decision=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

Lot 29 cannot produce a forecast, probability, strategy, signal, risk approval, trade intent, order intent, position or execution instruction.

## Non-objectives

- no new indicator or market-state calculation;
- no rewriting of Lots 21–28 evidence;
- no promotion to paper, sandbox or live mode;
- no implicit repair of a failing validator;
- no partial closure when one lot is absent or divergent.
