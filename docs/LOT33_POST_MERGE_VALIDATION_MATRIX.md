# Lot 33 — Post-Merge Validation Matrix

| Requirement | Evidence | Expected result |
|---|---|---|
| Version and lifecycle current | `validate_lot33_post_merge.py` | `0.33.0`, latest 33 |
| Lot 32 history preserved | Lot 33 overlay predecessor/statuses | PASS |
| State checksum recomputes | canonical SHA-256 | PASS |
| Audit checksum recomputes | canonical SHA-256 | PASS |
| Exact Lot 32 file lineage | registry/state/audit SHA-256 | PASS |
| Collection equals state records | standalone collection | PASS |
| UTC and sequence/revision ordering | canonical envelope assertions | PASS |
| Clock health reference values | 1000 / 201000 / 420000 µs | PASS |
| Coverage thresholds | 98.43% / 91.53% | PASS |
| Mutation threshold | 90.57% / 96 of 106 | PASS |
| Safety remains fail-closed | state + audit | PASS |
| Lot 34 remains locked | lifecycle overlay | PASS |
| Canonical historical roadmap validator | permanent repository validator | PASS when runner available |
| Ruff, mypy, Bandit, dependency audit | exact-head workflow | PASS when runner available |
| Full regression and anti-flake | exact-head workflow | PASS when runner available |

No unavailable hosted-runner check is represented as successful. A separate Lot 34 entry gate
is required after this audit is merged.
