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
