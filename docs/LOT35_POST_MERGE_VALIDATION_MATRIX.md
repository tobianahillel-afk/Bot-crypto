# Lot 35 — Post-Merge Validation Matrix

| Control | Evidence | Verdict |
|---|---|---|
| Historical audited release | `0.35.0` | PASS |
| Exact implementation merge | `d083d4f27c89759ebed37b2ecacccbe88dccad11` | PASS |
| Exact CI evidence head | `09701c7d5ebefbeba41143a2838564b09ea5fb3a` | PASS |
| State checksum | `8fc7243beffdf985fd6947557b87ab7bd27f9191520eb2d5d9af25d1e7a886b4` | PASS |
| Audit checksum | `98a88396f5b2e5ffc1cde02435399540ad213f5ec361b33e8a19c08b0fedf1de` | PASS |
| Line coverage ≥ 95% | `96.43%` | PASS |
| Branch coverage ≥ 90% | `93.75%` | PASS |
| Mutation ≥ 80% | `83.73%` (`1029/1229`) | PASS |
| Anti-flake | `3` repetitions | PASS |
| Reference reports | `3 = 2 MATCH + 1 TOLERATED_DIFF` | PASS |
| Reference veto | `ALLOW_ANALYSIS` | PASS |
| Runtime | `DATA_GOVERNANCE_ONLY` | PASS |
| External connectivity | disabled | PASS |
| Raw-data mutation | disabled | PASS |
| Trading / execution | disabled / disabled | PASS |
| Approved size | `0` | PASS |
| Lot 36 | `PLANNED_LOCKED`, `implementation_started=false` | PASS |

The quality metrics above are frozen from the exact final implementation-head GitHub Actions artifacts. A later audit run may revalidate the repository, but it must not silently replace this certified implementation evidence.
