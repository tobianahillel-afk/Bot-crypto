# Lot 27 — Post-Merge Audit

Status: `AUDIT_IN_PROGRESS`

## Audited baseline

- merged pull request: `#8`;
- merge commit: `a36856f5a0a80f9fc4a0b5e27c9a433f43bb551d`;
- certified implementation head: `bb6318a5b5ce9abbd924e3da5d70d67da6a42b36`;
- certified implementation logic commit: `bae0633d1fb28a77eb91111796d35549a5a365c8`;
- release version: `0.27.0`.

## Permanent assertions

`tests/test_lot27_post_merge_state.py` verifies that:

- Lot 27 remains the latest implemented lot;
- its lifecycle status is final and offline descriptive only;
- the committed state checksum is independently recomputed;
- the audit references the exact state and reports `MATCH` replay;
- the deterministic oracle remains `GLOBAL_CONTEXT_MIXED`, score `0.5646`, coverage `1.0`;
- `MTF_DIVERGENT` remains visible rather than silently resolved;
- all decision, trading and execution permissions remain disabled;
- Lot 28 remains `PLANNED_LOCKED`;
- no one-shot reconciliation or auto-fix files remain.

## Required verdict

This audit becomes `PASS` only when every workflow triggered by this PR succeeds against the merged `main` baseline. Lot 28 remains locked until then.
