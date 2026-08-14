# Lot 45 — V4 implementation entry gate

## Decision

`GO_LOT45_IMPLEMENTATION_ENTRY`

This gate authorizes implementation work for **Lot 45 — Order Flow, Delta & CVD Engine** only after the independent Lot 44 post-merge audit has been merged and has emitted `GO_LOT44_POST_MERGE`.

## Certified prerequisite

- Lot 44 post-merge audit PR head: `0ddf2c3150b339b8573fead8c942c4b1efa4b300`
- Lot 44 post-merge audit merge / gate base: `1fd85f26102f94d4c42a8f515b522c23028bac89`
- Lot 44 post-merge verdict: `GO_LOT44_POST_MERGE`
- Lot 44 post-merge checksum: `b8b531b2fcb09a30728549cc480d54d9be71504356468704c102ff085c39ea9a`

## Lot 45 scope

Owner: `MicrostructureDomain`  
Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
Package boundary: `src/crypto_quant_bot/microstructure`

Canonical outputs:

- `OrderFlowDeltaCVDEngineStateV1`
- `OrderFlowDeltaCVDEngineAuditV1`
- `OrderFlowStateV1`
- `CVDSeriesV1`

The implementation must remain research-only and fail closed. It cannot authorize a signal, risk decision, order route, trade or execution.

## Gate transition and predecessor archival

The Lot 44 implementation entry workflow is retained for manual historical replay but its `pull_request` trigger is archived in this transition. This is required because the predecessor gate intentionally proved Lot 45 implementation paths absent and must not run as a current-tree lock after `GO_LOT44_POST_MERGE`.

The Lot 45 gate itself is frozen as an immutable historical transition. On future Lot 45 implementation PRs, the workflow locates that transition in Git history and replays the gate snapshot in a detached worktree instead of requiring Lot 45 implementation paths to remain absent on the current PR head.

## Gate guarantees

The gate validator proves that:

1. the gate descends from the exact Lot 44 post-merge audit merge;
2. the merge parents are the stabilized post-remediation `main` and the certified Lot 44 audit PR head;
3. the canonical roadmap blob and Lot 45 record are unchanged;
4. the gate transition contains governance artifacts only, including archival of the predecessor trigger;
5. no Lot 45 implementation path existed at the frozen gate snapshot;
6. Lot 46 remains `PLANNED_LOCKED` and physically absent on the current tree;
7. the published JSON Schema itself fixes the exact contracts, safety policy and quality thresholds;
8. safety remains fail-closed with approved size zero and no execution capability.

The pre-gate branch `agent/lot45-order-flow-delta-cvd-engine` is not part of this certified transition and must not be merged as-is.
