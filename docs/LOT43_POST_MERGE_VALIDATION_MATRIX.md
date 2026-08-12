# Lot 43 — Post-Merge Validation Matrix

## Decision

`GO_LOT43_POST_MERGE`

Release: `0.43.0`  
Owner: `MicrostructureDomain`  
Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
Next lot: Lot 44 — `PLANNED_LOCKED`

The implementation PR was merged under an explicit **owner override** after independent technical review and `23/23` exact-head workflows succeeded. This matrix does not claim a native independent GitHub approval that did not occur.

## Immutable commit chain

| Control | Expected value | Result |
|---|---|---|
| Lot 43 gate merge | `ed8845e0e56151348fe57c0e9bceaf4646ea49aa` | PASS |
| Frozen source | `d45f40aec90b26dd1278ec2f49b405fa5b2ed94e` | PASS |
| Certification anchor | `2b04ea3470f404a57c7a2778b3dccacd889d1fcc` | PASS |
| Frozen evidence | `76c0670d7933f29965306993ff217647def0f0d4` | PASS |
| Certified content | `fd5cbe23d22dcd34d85e97c79667d7d98d1ddaff` | PASS |
| Final PR head | `69667b5c46ac2ecf7b2a64656f84c374ee929dbf` | PASS |
| Squash merge | `0b524b1478272e0a69a06b50c68b1b2c3b092964` | PASS |
| PR | `#57` | PASS |
| Final head ↔ squash full-tree equivalence | exact | PASS |
| Source immutability after certification | no Lot 43 production drift | PASS |
| Evidence immutability | no frozen evidence drift | PASS |

## Frozen artifact integrity

| Artifact | Certified checksum | Result |
|---|---|---|
| Engine state | `30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6` | PASS |
| Engine audit | `3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67` | PASS |
| `BookResilienceStateV1` | `598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb` | PASS |

## Reference behavior

| Requirement | Certified result | Result |
|---|---|---|
| Sequence history | `[1001, 1002, 1003]` | PASS |
| Current sequence | `1003` | PASS |
| Horizons | `[10000, 25000] µs` | PASS |
| Significant depletion | BID `50024.8`, `1.25 -> 0` | PASS |
| Max-window status | `EXPIRED_NO_REPLENISHMENT` | PASS |
| Volatility | `0 bps / QUIET` | PASS |
| BID @ 10ms | `FRAGILE` | PASS |
| BID @ 25ms | `FRAGILE` | PASS |
| ASK @ 10ms | `NO_EVENTS` | PASS |
| ASK @ 25ms | `NO_EVENTS` | PASS |
| Recovery threshold | `0.25` | PASS |
| Observed book only | `true` | PASS |
| Participant intent inferred | `false` | PASS |

## Direct-model integrity

| Invariant | Required result | Result |
|---|---|---|
| Observation causality | `event_time <= receive_time <= decision_time` | PASS |
| Depletion/replenishment sequence ordering | replenishment strictly after depletion | PASS |
| History membership | all referenced event sequence IDs in `history_sequence_ids` | PASS |
| Slice matrix | exact unique BID/ASK × declared horizons | PASS |
| Slice aggregation | recomputed from published events | PASS |
| Maximum-horizon outcome | status exactly matches recomputed max-horizon outcome | PASS |
| Decision-time availability | implied recovery/shift evidence cannot be future | PASS |
| Recovery threshold | direct quantity recovery meets published ratio | PASS |
| Engine metrics | bound to embedded resilience state | PASS |

## Critical quality

| Control | Requirement | Certified result | Result |
|---|---:|---:|---|
| Lot 43 regression | all PASS | `132 PASS` at final hardening gate | PASS |
| Line coverage | `>=95%` | `98.07%` | PASS |
| Branch coverage | `>=90%` | `96.88%` | PASS |
| Mutation score | `>=80%` | `82.13%` | PASS |
| Killed mutants | evidence | `2357` | PASS |
| Survived mutants | evidence | `513` | PASS |
| Evaluated/total mutants | exact completion | `2870/2870` | PASS |
| Timeout mutants | `0` | `0` | PASS |
| Suspicious mutants | `0` | `0` | PASS |
| Anti-flake | `3` repetitions | `3 PASS` | PASS |

## Certification evidence

### Source validation

- run: `31642595060`
- artifact: `9159515091`
- digest: `sha256:7878366052c7188221d2819f1b0bb447d265c82e8b701d80b675f7c22d024b90`
- conclusion: `SUCCESS`

### Mutation assurance

- run: `31642595056`
- artifact: `9159605334`
- digest: `sha256:124ffd3b1b8d18310fd86cbdfc314ebab904a6a329594a3249f5201683d660f5`
- conclusion: `SUCCESS`

### Frozen evidence

- run: `31643513115`
- artifact: `9159962077`
- digest: `sha256:c34bea93fb5f0afb0a36810a6df72d0c71982531f3d000f325c485e984925ace`
- conclusion: `SUCCESS`

The exact final implementation head `69667b5c46ac2ecf7b2a64656f84c374ee929dbf` completed **23/23 applicable workflows with `SUCCESS`** before merge.

## Engineering, architecture, security and replay

| Control | Result |
|---|---|
| Ruff | PASS |
| MyPy | PASS |
| Closed schemas | PASS |
| Deterministic run1/run2 replay | PASS |
| No-connectivity validation | PASS |
| Domain architecture | PASS |
| Ownership/roadmap semantics | PASS |
| Decision traceability | PASS |
| Silent numeric coercion gate | PASS |
| Engineering inventory/deviations | PASS |
| Bandit | PASS |
| Dependency audit | PASS |
| Full repository regression | PASS |
| Historical frozen/post-merge regressions | PASS |

## Safety matrix

| Invariant | Required | Result |
|---|---:|---|
| `analysis_only` | `true` | PASS |
| `used_for_decision` | `false` | PASS |
| external connectivity | forbidden | PASS |
| network ingestion | forbidden | PASS |
| real credentials | forbidden | PASS |
| raw-data mutation | forbidden | PASS |
| participant intent as fact | forbidden | PASS |
| signal generation | forbidden | PASS |
| risk approval | forbidden | PASS |
| order routing | forbidden | PASS |
| `trade_allowed` | `false` | PASS |
| `execution_allowed` | `false` | PASS |
| `approved_size` | `0` | PASS |

## Lifecycle matrix

| Lifecycle control | Expected | Result |
|---|---|---|
| Previous overlay | `data/audit/roadmap_lifecycle_overlay_lot42.json` | PASS |
| Lot 42 record | unchanged from previous overlay | PASS |
| Latest implemented lot | `43` | PASS |
| Lot 43 status | `IMPLEMENTED_VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY` | PASS |
| Lot 44 implementation started | `false` | PASS |
| Lot 44 status | `PLANNED_LOCKED` | PASS |
| Release | `0.43.0` | PASS |

## Post-merge decision

The post-merge workflow must re-prove squash equivalence, frozen immutability, exact frozen validation, deterministic source replay, release/lifecycle state, current architecture/security regression, full tests, anti-flake and physical Lot 44 absence on the audit PR head.

**Verdict: `GO_LOT43_POST_MERGE`.**

**Lot 44 remains `PLANNED_LOCKED`.** This verdict permits only a separate Lot 44 governance-only implementation entry gate after this audit is merged; it does not authorize Lot 44 implementation.
