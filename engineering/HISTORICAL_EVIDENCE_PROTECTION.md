# Historical Evidence Protection — ENG-00.4

Historical immutability is **commit-anchored**, not a ban on all future documentation edits.

The policy therefore separates:

1. exact Git anchors that prove Lot44 certification and the Lot45 entry gate;
2. current-tree files explicitly frozen by those certification chains;
3. status/overview files that are intentionally allowed to evolve.

This avoids two opposite failures:

- weakening auditability by silently editing certified artifacts;
- freezing the entire repository forever because a filename existed in an old certification.

The machine-readable policy is `engineering/HISTORICAL_EVIDENCE_PROTECTION.json`.
During the engineering-foundation branch, its protected current-tree paths must remain
byte-identical to `origin/main`.

A single separately approved migration is recorded under `approved_protected_path_migrations`: it binds the Lot44 frozen-attestation workflow to its exact source commit, parent, and before/after Git blob IDs. The validator accepts that exact path only when the commit is an ancestor of HEAD and the current blob still matches the approved target. All other protected-path drift remains invalid.
