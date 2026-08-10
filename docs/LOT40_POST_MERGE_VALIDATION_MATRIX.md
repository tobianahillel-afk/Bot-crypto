# Lot 40 Post-Merge Validation Matrix

| Control | Certified evidence | Required result |
|---|---|---|
| Entry gate ancestry | `91df3e378336a791a731cb1561382ba28e6e0978` → `b9a18a8aaef858b985c3f75ef2aa8955ec521e9f` → `ea04fe826261eeed5a59eea60265b38b68404b6b` → `1268772c07cbb76c18b3267aef12dad5ba58af31` → `88f0dac660e262a1c468d9cd75c5e7996ce4817b` | PASS |
| Implementation PR | `#48`, final head `1268772c07cbb76c18b3267aef12dad5ba58af31` | merged |
| Final-head matrix | 14/14 applicable workflows | SUCCESS |
| Validation workflow | run `31425236798` | SUCCESS |
| Validation artifact | `9076940399` | present |
| Validation artifact digest | `sha256:50e77a5ae432979142621402980ad2a42022857fef1303b69a805b84d3d2d9a5` | exact |
| Mutation workflow | run `31425236875` | SUCCESS |
| Mutation artifact | `9077043930` | present |
| Mutation artifact digest | `sha256:e5ef9cdec8365862eca6c011ea71895f890ff16047290220377d0ebda56d1c8e` | exact |
| Frozen source head | `b9a18a8aaef858b985c3f75ef2aa8955ec521e9f` | immutable |
| Frozen evidence head | `ea04fe826261eeed5a59eea60265b38b68404b6b` | immutable |
| Line coverage | `97.31%` | >=95% |
| Branch coverage | `91.24%` | >=90% |
| Anti-flake | `3` repetitions | PASS |
| Mutation score | `82.32%` | >=80% |
| Mutation counts | killed `1280`, survived `275`, total/evaluated `1555/1555` | exact |
| Mutation anomalies | timeout `0`, suspicious `0` | exact |
| Mutation determinism | `max_children=1`, `PYTHONHASHSEED=0` | exact |
| State checksum | `e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477` | exact |
| Audit checksum | `978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c` | exact |
| Integrity checksum | `35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a` | exact |
| Veto checksum | `000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc` | exact |
| Reference health | `HEALTHY / 100 / NONE` | exact |
| Reference sequence | `1003`, `SYNCED` | exact |
| Reference depths | bids `2`, asks `3` | exact |
| Reference stale age | `30000us` | exact |
| Release | `0.40.0` | exact |
| Lifecycle | latest implemented `40` | exact |
| Lot 40 status | `IMPLEMENTED_VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY` | exact |
| Lot 41 | `PLANNED_LOCKED`, `implementation_started=false` | exact |
| No source drift | merge `88f0dac660e262a1c468d9cd75c5e7996ce4817b` → audit head on Lot40 source/config/schemas | no diff |
| No evidence drift | merge `88f0dac660e262a1c468d9cd75c5e7996ce4817b` → audit head on six frozen evidence files | no diff |
| No connectivity | AST validator + workflow | PASS |
| Full regression | repository-wide pytest | PASS |
| Architecture / roadmap / traceability | canonical validators | PASS |
| Engineering inventory | no new unowned deviation | PASS |
| Security | Bandit | PASS |
| Dependencies | `pip-audit` locked requirements | PASS |
| Trading | `trade_allowed=false` | exact |
| Execution | `execution_allowed=false` | exact |
| Approved size | `0` | exact |

## Audit verdict

The matrix is satisfied only when the independent audit workflow is green on the exact final audit PR head. The target verdict is `GO_LOT40_POST_MERGE`.

Lot 41 remains locked after this audit. A separate Lot 41 entry gate is required after the audit merge.
