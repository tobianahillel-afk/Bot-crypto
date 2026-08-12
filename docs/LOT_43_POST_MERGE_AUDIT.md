# Lot 43 — Independent Post-Merge Audit

## Verdict

`GO_LOT43_POST_MERGE`

Lot 43 — Book Resilience & Replenishment Engine is revalidated after its squash merge. The audited release is `0.43.0` and the lifecycle status is `IMPLEMENTED_VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY`.

This verdict closes Lot 43 only. **Lot 44 remains `PLANNED_LOCKED` and implementation has not started.** A separate governance-only Lot 44 implementation entry gate is required before any Lot 44 business source, config, schema, runner, validator, test, report, or implementation is permitted.

## Governance note

PR #57 was squash-merged under an explicit **owner override** by repository owner `tobianahillel-afk` after the independent technical review found no remaining substantive blocker and the exact final head completed `23/23` applicable workflows with `SUCCESS`. No independent native GitHub `APPROVED` review is retroactively claimed.

The post-merge audit does not erase or reinterpret that override. It independently verifies the merged tree, frozen source/evidence, deterministic behavior, safety boundaries and downstream lock.

## Certified commit chain

- Lot 43 implementation entry-gate merge: `ed8845e0e56151348fe57c0e9bceaf4646ea49aa`;
- frozen production source: `d45f40aec90b26dd1278ec2f49b405fa5b2ed94e`;
- certification anchor: `2b04ea3470f404a57c7a2778b3dccacd889d1fcc`;
- frozen evidence head: `76c0670d7933f29965306993ff217647def0f0d4`;
- frozen validator/certified-content head: `fd5cbe23d22dcd34d85e97c79667d7d98d1ddaff`;
- exact fully green final PR head: `69667b5c46ac2ecf7b2a64656f84c374ee929dbf`;
- implementation squash merge: `0b524b1478272e0a69a06b50c68b1b2c3b092964`;
- implementation pull request: `#57`.

The audit proves the complete pre-merge certification chain and full-tree squash equivalence between `69667b5c...` and `0b524b14...`. It also proves that the implementation merge is an ancestor of the post-merge audit head.

## Frozen evidence provenance

The final certification is segmented and fail-closed:

1. `d45f40a... -> 2b04ea3...`: exactly two commits, only the Lot 43 source-validation and mutation workflows;
2. `2b04ea3... -> 76c0670...`: exactly five evidence commits; the net changed evidence paths are engine state, engine audit, coverage and mutation, while `book_resilience_state_lot43.json` is explicitly byte-identical to the certified source artifact;
3. `76c0670... -> fd5cbe2...`: exactly one frozen-validator commit;
4. `fd5cbe2... -> 69667b5...`: exactly one frozen-attestation workflow commit;
5. `69667b5...` and squash merge `0b524b14...`: complete tree equivalence.

No Lot 43 production source, config, schema, implementation contract, acceptance contract, runner, validator, or test changes after the certified source are accepted by the post-merge audit.

## Frozen runtime evidence

Canonical checksums:

- engine state output: `30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6`;
- engine audit: `3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67`;
- `BookResilienceStateV1`: `598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb`.

Reference behavior remains:

```text
history_sequence_ids=[1001, 1002, 1003]
sequence_id=1003
resilience_horizons_us=[10000, 25000]
one BID depletion at 50024.8, quantity 1.25 -> 0
max_window_status=EXPIRED_NO_REPLENISHMENT
volatility_measure_bps=0
volatility_regime=QUIET
BID 10ms=FRAGILE
BID 25ms=FRAGILE
ASK 10ms=NO_EVENTS
ASK 25ms=NO_EVENTS
replenishment_min_recovery_ratio=0.25
observed_book_only=true
participant_intent_inferred=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

The direct-model hardening additionally binds event sequence IDs to published history, rejects evidence after decision time or after the maximum declared horizon, enforces the authoritative complete side×horizon matrix and requires quantity recovery to meet the published versioned threshold.

## Exact certification evidence

### Source validation

- exact source: `d45f40aec90b26dd1278ec2f49b405fa5b2ed94e`;
- workflow run: `31642595060` — `SUCCESS`;
- artifact: `9159515091`;
- digest: `sha256:7878366052c7188221d2819f1b0bb447d265c82e8b701d80b675f7c22d024b90`.

### Mutation assurance

- workflow run: `31642595056` — `SUCCESS`;
- artifact: `9159605334`;
- digest: `sha256:124ffd3b1b8d18310fd86cbdfc314ebab904a6a329594a3249f5201683d660f5`.

Certified quality:

- targeted line coverage: `98.07%` (`>=95%` required);
- targeted branch coverage: `96.88%` (`>=90%` required);
- mutation score: `82.13%` (`>=80%` required);
- killed mutants: `2357/2870`;
- survived mutants: `513`;
- timeout mutants: `0`;
- suspicious mutants: `0`;
- anti-flake: `3` repetitions PASS.

### Frozen-evidence attestation

- workflow run: `31643513115` — `SUCCESS`;
- artifact: `9159962077`;
- digest: `sha256:c34bea93fb5f0afb0a36810a6df72d0c71982531f3d000f325c485e984925ace`.

It proves provenance v5, source/evidence immutability, exact hashes/checksums/quality, deterministic replay, architecture/security regression and the Lot 44 lock.

## Exact pre-merge matrix

The exact final implementation head `69667b5c46ac2ecf7b2a64656f84c374ee929dbf` completed **23/23 applicable GitHub Actions workflows with `SUCCESS`** before squash merge.

Notable runs include:

- Lot 43 frozen evidence: `31643513115` — SUCCESS;
- Lot 43 source-validation replay: `31643513136` — SUCCESS;
- Lot 43 mutation replay: `31643513097` — SUCCESS;
- institutional quality: `31643513204` — SUCCESS;
- Lot 43 V4 entry gate: `31643513144` — SUCCESS;
- Lot 42 mutation regression: `31643513029` — SUCCESS;
- Lot 39 order-book delta regression: `31643513112` — SUCCESS.

## Safety and non-goals

The audited boundary remains strictly descriptive/offline:

- runtime `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`;
- no external connectivity or network ingestion;
- no live exchange data or real credentials;
- no raw market-data mutation;
- no participant intent asserted as fact;
- no forecast or signal authority;
- no risk approval;
- no order routing;
- no trading;
- no execution;
- `approved_size=0`.

## Lifecycle promotion

After this audit PR is merged:

- release: `0.43.0`;
- latest implemented lot: `43`;
- Lot 43: `IMPLEMENTED_VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY`;
- Lot 44: `PLANNED_LOCKED`;
- Lot 44 implementation started: `false`.

## Final decision

The post-merge audit requires all of the following to pass on the audit PR head: squash equivalence, frozen-source immutability, frozen-evidence immutability, frozen validator replay, deterministic source replay, release/lifecycle validation, architecture/roadmap/traceability/engineering gates, security/dependency scan, full regression, three Lot 43 anti-flake repetitions and physical Lot 44 absence.

With those controls green, the decision is:

**`GO_LOT43_POST_MERGE`.**

This decision authorizes only the next **Lot 44 governance entry-gate phase**. It does not itself authorize Lot 44 implementation.
