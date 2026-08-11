# Lot 41 V4 Entry Gate Report

## Verdict

`PASS_CANDIDATE_GATE` — governance-only authorization candidate for **Lot 41 — Spread, Depth & Imbalance Engine**.

The candidate is based on exact audited `main` commit `20975b505c7f8b527751fb5d3bce034c6e55dcc2` and project version `0.40.0`. The final gate verdict becomes actionable only after the gate PR itself is fully green and merged.

## Immutable authority

- registry: `data/audit/product_scope_roadmap_lot21.jsonl`;
- registry blob: `84de51bda788a8d124fb7d344419c4a4b12030b5`;
- Lot 41 line: `42` — `Spread, Depth & Imbalance Engine`;
- Lot 42 line: `43` — `Liquidity Zones, Walls & Voids Engine`;
- owner: `MicrostructureDomain`;
- runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`;
- Lot 42 status: `PLANNED_LOCKED`.

## Lot 40 prerequisite evidence

| Evidence | Certified value |
|---|---|
| Independent audit merge | `20975b505c7f8b527751fb5d3bce034c6e55dcc2` |
| Post-merge verdict | `GO_LOT40_POST_MERGE` |
| Source head | `b9a18a8aaef858b985c3f75ef2aa8955ec521e9f` |
| Evidence head | `ea04fe826261eeed5a59eea60265b38b68404b6b` |
| Final PR head | `1268772c07cbb76c18b3267aef12dad5ba58af31` |
| Implementation merge | `88f0dac660e262a1c468d9cd75c5e7996ce4817b` |
| State checksum | `e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477` |
| Audit checksum | `978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c` |
| Integrity checksum | `35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a` |
| Health-veto checksum | `000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc` |
| Lines / branches | `97.31% / 91.24%` |
| Mutation | `82.32%` |
| Anti-flake | `3` PASS |
| Reference health | `HEALTHY`, score `100`, consequence `NONE` |

The gate validator re-runs the independent Lot 40 post-merge validator, validates the lifecycle overlay and compares the complete prerequisite object exactly.

## Authorized Lot 41 boundary

Authorized calculations are limited to absolute spread, spread bps, mid, microprice, configured bps-band depth, cumulative depth and symmetric imbalance with explicit zero-denominator handling. Results must remain bound to observed book depth and certified book-quality lineage; no extrapolation beyond observed depth is permitted.

Required outputs are `SpreadDepthImbalanceEngineStateV1`, `SpreadDepthImbalanceEngineAuditV1` and `BookFeatureStateV1`. Their production schemas/configuration are intentionally absent from this gate and may be created only after gate merge.

## Locked downstream boundary

Lot 42 remains `PLANNED_LOCKED`. Liquidity zones/walls/voids, persistence/replenishment/cancellation inference, resilience, aggressor/order-flow/CVD, hidden-liquidity/stop-zone inference, sweep/fakeout/trap engines, derivatives context, game theory, forecasts, signals, risk approval, routing, trading and execution remain forbidden.

## Quality and safety requirements

- critical Lot 41 coverage: lines `>=95%`, branches `>=90%`;
- mutation score `>=80%` with final evidence expected to have zero timeout/suspicious mutants;
- anti-flake `>=3`;
- full regression, architecture, roadmap, traceability, engineering, Bandit and dependency audit required;
- `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`, `used_for_decision=false`;
- no network/live data/real credentials.

## Gate artifact

Canonical gate checksum:

`1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe`

Gate files must be exactly the seven governance files listed by `.github/workflows/lot41-entry-gate.yml`; the workflow rejects any Lot 41 production file or any Lot 42 implementation file before merge.

## Human conclusion

The prerequisite audit permits submission of the Lot 41 entry gate. This report does **not** claim the gate PR is green or merged until GitHub Actions proves the exact PR head and the merge is independently verified. Lot 42 remains locked throughout.
