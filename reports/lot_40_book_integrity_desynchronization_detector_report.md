# Lot 40 — Book Integrity / Desynchronization Detector Report

## Current verdict

`PASS_FROZEN_IMPLEMENTATION_EVIDENCE`

Lot 40 implementation evidence is frozen against an immutable production source head and independently revalidated. This verdict certifies implementation evidence only; merge still requires all workflows on the final PR head to be green and the post-merge audit remains mandatory before Lot 41 can open.

## Certified commit chain

- Lot 40 entry-gate merge: `91df3e378336a791a731cb1561382ba28e6e0978`
- gate checksum: `23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18`
- frozen production source head: `b9a18a8aaef858b985c3f75ef2aa8955ec521e9f`
- frozen evidence head: `ea04fe826261eeed5a59eea60265b38b68404b6b`
- project release entering implementation: `0.39.0`
- owner: `MicrostructureDomain`
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- Lot 41: `PLANNED_LOCKED`

The source-to-evidence diff contains exactly six frozen evidence files and no production source, config, schema, runner, validator or test changes.

## Certified implementation scope

- immutable Lot 40 run-context and lineage contracts;
- immutable `BookIntegrityStateV1` and `BookHealthVetoV1`;
- immutable detector state/audit contracts;
- strict versioned health policy configuration;
- sequence-continuity validation;
- crossed/locked-state validation;
- deterministic freshness validation from an injected decision clock;
- independent canonical checksum revalidation;
- depth-collapse detection from published level counts;
- strict decimal-text, positive-quantity and level-monotonicity validation;
- deterministic weighted health score with published components;
- critical-veto dominance over aggregate score;
- `NONE/WAIT/PAUSE/BLOCK` consequence policy;
- atomic four-artifact persistence;
- deterministic replay validation;
- AST no-connectivity validation;
- historical Lot 39 gates converted to archival attestations without changing frozen Lot 39 evidence.

## Certified policy

Weights total exactly `100`:

- sequence continuity: `20`, critical;
- crossed/locked state: `20`, critical;
- freshness: `15`, non-critical;
- checksum integrity: `20`, critical;
- depth integrity: `20`, non-critical;
- level monotonicity: `5`, critical.

Thresholds and consequences:

- trade-health threshold: `90`;
- system-health threshold: `80`;
- critical failure consequence: `BLOCK`;
- non-critical score `<80`: `PAUSE`;
- non-critical score `80..89`: `WAIT`;
- score `>=90` with no critical veto: `NONE`.

The score is deterministic and is **not a calibrated probability**.

## Frozen reference result

The certified Lot 39 reconstructed book produces exactly:

```text
health_status=HEALTHY
book_health_score=100
consequence=NONE
sequence_id=1003
synchronization_state=SYNCED
stale_age_us=30000
bid_depth_levels=2
ask_depth_levels=3
trade_allowed=false
execution_allowed=false
approved_size=0
```

Frozen checksums:

- detector state output: `e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477`;
- detector audit: `978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c`;
- `BookIntegrityStateV1`: `35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a`;
- `BookHealthVetoV1`: `000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc`.

## Frozen Lot 39 lineage

- state: `d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0`;
- audit: `1e29d0b8695a1b8825e1fc91728a6254ad93c689e1f961cfa424e6d5fed8ed41`;
- reconstructed book: `a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde`;
- delta fixture: `1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97`.

## Quality evidence

Targeted coverage on the frozen source head:

- line coverage: `97.31%` (`>=95%` required);
- branch coverage: `91.24%` (`>=90%` required);
- anti-flake repetitions: `3`;
- status: `PASS`.

Validation workflow evidence:

- run: `31424334609`;
- artifact: `9076604241` (`lot40-book-integrity-evidence`);
- artifact digest: `sha256:6a2ead16b15d0c4f03c63e29657b2471fcedcf438a6d2069d933cd5a90261699`.

Mutation assurance on the same frozen source head:

- score: `82.32%` (`>=80%` required);
- killed: `1280`;
- survived: `275`;
- evaluated/total: `1555/1555`;
- timeout: `0`;
- suspicious: `0`;
- `max_children=1`;
- `PYTHONHASHSEED=0`;
- mutmut run/results exit codes: `0/0`;
- run: `31424334898`;
- artifact: `9076639786` (`lot40-mutation-evidence`);
- artifact digest: `sha256:6a3a36652f973aa7b1da45b1920f008388a91f4bd0c171f0a7a3f9195594c2dd`.

The frozen source head also passed the complete applicable workflow matrix: Lot 40 validation and mutation, institutional quality, engineering inventory, roadmap/lifecycle, Lot 39 frozen/post-merge/validation/mutation attestations, Lot 37 mutation and Lot 26 foundation validation.

## Frozen-evidence attestation

`script/validate_lot40_frozen_evidence.py` and the dedicated frozen-evidence workflow independently enforce:

- entry-gate → source → evidence → current-head ancestry;
- immutable Lot 40 production source/config/schemas/runners/validators/tests after the source head;
- immutable six-file evidence set after the evidence head;
- canonical checksum recomputation and state/audit/integrity/veto cross-links;
- exact Lot 39 lineage;
- exact coverage and mutation evidence;
- exact safety boundary;
- Lot 41 absence.

## Safety boundary

The frozen state and audit both require:

- analysis-only mode;
- no external connectivity or network ingestion;
- no real credentials;
- no market-event publication or raw-data mutation;
- no signal generation or scenario-to-signal conversion;
- no risk approval or order routing;
- no trading or execution;
- `approved_size=0`;
- `used_for_decision=false`.

## Rollback

Rollback is deterministic: return the implementation branch to the merged Lot 40 gate `91df3e378336a791a731cb1561382ba28e6e0978`. Lot 39 remains the latest independently audited implementation at release `0.39.0`; the frozen Lot 39 evidence is unchanged.

## Progression rule

Lot 41 remains `PLANNED_LOCKED`. It must not receive an implementation gate or source implementation until:

1. PR #48 is merged from an exact fully green final head; and
2. an independent Lot 40 post-merge audit is itself fully green and merged with a `GO_LOT40_POST_MERGE` verdict.
