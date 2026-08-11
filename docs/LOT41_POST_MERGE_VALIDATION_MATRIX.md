# Lot 41 — Post-Merge Validation Matrix

Verdict target: `GO_LOT41_POST_MERGE`

Exact chain:

- gate merge: `75822f8ea7c6f67f73649d2f43be6efba840ab67`;
- source head: `14c0d8da1b02d076b3c43a07a34ac96c673018b0`;
- evidence head: `7ada0ca6c4d439505ef453b988dedd4aa96c1a32`;
- final PR head: `89ae244db77f16f31d226a7494d78b65b904dcd9`;
- implementation merge: `a253ce35c97303e8b8c65707c07597e996b3a832`;
- release: `0.41.0`.

| Control | Required result | Frozen / exact evidence |
|---|---|---|
| Gate ancestry | PASS | `75822f8e…` |
| Frozen source | PASS | `14c0d8da…` |
| Frozen evidence | PASS | `7ada0ca6…` |
| Final PR head | PASS | `89ae244d…`, 17/17 workflows SUCCESS |
| Implementation merge | PASS | `a253ce35…` |
| Frozen state checksum | exact | `23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573` |
| Frozen audit checksum | exact | `af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd` |
| Frozen feature checksum | exact | `77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5` |
| Line coverage | `>=95%` | `100.00%` |
| Branch coverage | `>=90%` | `100.00%` |
| Mutation score | `>=80%` | `81.93%` |
| Mutation killed | exact | `966/1179` |
| Mutation timeout | `0` | `0` |
| Mutation suspicious | `0` | `0` |
| Anti-flake | `3` | `3` targeted and institutional full-suite repetitions |
| Deterministic run1/run2 | identical | PASS |
| Observed depth only | true | `observed_depth_only=true`, `extrapolated=false` |
| Book health binding | healthy/no veto | `HEALTHY`, score `100`, consequence `NONE` |
| No connectivity | PASS | AST validator + Bandit + runtime mode |
| Trading authority | forbidden | `trade_allowed=false`, `execution_allowed=false`, `approved_size=0` |
| Release | exact | `0.41.0` |
| Lifecycle latest | exact | `41` |
| Lot 40 lifecycle | unchanged | exact copy from Lot40 audited overlay |
| Lot 41 lifecycle | implemented | `IMPLEMENTED_VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY` |
| Lot 42 lifecycle | locked | `PLANNED_LOCKED`, `implementation_started=false` |
| Lot 42 files | absent | required |
| Architecture | PASS | domain/ownership validators |
| Roadmap semantics | PASS | roadmap validators |
| Traceability | PASS | mandatory traceability gate |
| Silent coercion | PASS | no-silent-numeric-coercion gate |
| Engineering limits | PASS | inventory + owned deviation gate |
| Full regression | PASS | `pytest -q` |
| Static security | PASS | Bandit |
| Dependency audit | PASS | `pip-audit` |

## Exact final-head CI artifacts

Validation:

- run `31484227338`;
- artifact `9098457077`;
- digest `sha256:61431809213962e498f548bf87ed75f5519ac53e7da9bb876f3e118389863320`.

Mutation:

- run `31484227363`;
- artifact `9098475166`;
- digest `sha256:b64f1b9b5452586f3dfba0b2c456ad911e6fa9d688b023ce78b6100f263c4ab8`.

Frozen evidence attestation:

- run `31484227389`;
- artifact `9098452090`;
- digest `sha256:7ffb95dd0ec22987f705999af139104100995ec1225fdb2bb51a206c3fc563e9`.

## Frozen reference math

```text
spread_absolute=0.2
mid_price=50025
spread_bps=0.03998000999500249875062468766
microprice=50025.01612903225806451612903
band_bps=[0.025,0.05,0.1]
bid_depth=[0.9,0.9,1.4]
ask_depth=[0.65,1.75,2.15]
```

The matrix is satisfied only when `scripts/validate_lot41_post_merge.py` returns `PASS` with verdict `GO_LOT41_POST_MERGE` and the post-merge audit workflow is green on the exact audit PR head. Lot 42 remains locked until the audit PR is merged.
