# Lot 36 — Post-Merge Validation Matrix

| Control | Evidence | Verdict |
|---|---|---|
| Frozen implementation source | `c21b8f242270bd87eebbf7279635ab8bb51b8666` | PASS |
| Canonical evidence freeze | `b3680f5da0a3fd98fdedc31599c829dc60808290` | PASS |
| Exact-head CI attestation | `16f3454c6f912f3f00f79836950047b15687abce`; tree-identical to evidence freeze | PASS |
| Exact implementation merge | `87da195283797247505e4fc650214e33e759e21a` | PASS |
| State checksum | `635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592` | PASS |
| Audit checksum | `ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42` | PASS |
| Closure-candidate manifest checksum | `6a9935e728a93a23a3804106dc54aa216f4f9fedad3635b5507139f4ccbfc37f` | PASS |
| Replay checksum | `cef50b5191c1f3c78baaa3906c4c5ded59f1dd45dad0271a0071b7056b6af91d` | PASS |
| Line coverage ≥ 95% | `100.00%` (`552/552`) | PASS |
| Branch coverage ≥ 90% | `100.00%` (`136/136`) | PASS |
| Mutation ≥ 80% | `83.48%` (`1289/1544`) | PASS |
| Anti-flake | `3` repetitions | PASS |
| Exact-head workflows | `10/10` PASS on `16f3454c6f912f3f00f79836950047b15687abce` | PASS |
| Reference records | `3` | PASS |
| Missing / gap / outage / stale | `0 / 0 / 0 / 0` | PASS |
| Quality score / freshness | `10000 / 10000` bps | PASS |
| Data-quality veto | `ALLOW_ANALYSIS` | PASS |
| Reconciliation veto | `ALLOW_ANALYSIS` | PASS |
| Deterministic replay | `REPLAY_MATCH` | PASS |
| Runtime | `DATA_GOVERNANCE_ONLY` | PASS |
| External connectivity / raw mutation | disabled / disabled | PASS |
| Trading / execution | disabled / disabled | PASS |
| Approved size | `0` | PASS |
| V3 release closure | `CLOSED_POST_MERGE_AUDITED` | PASS |
| Lot 37 | `PLANNED_LOCKED`, `implementation_started=false` | PASS |

The implementation-stage `closure_manifest_lot36.json` intentionally remains an immutable candidate manifest with `v3_closed=false`. Final V3 closure is asserted only by this independent post-merge audit and the Lot36 lifecycle overlay.
