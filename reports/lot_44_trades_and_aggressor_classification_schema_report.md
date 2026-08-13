# Lot 44 — Trades & Aggressor Classification Schema Report

## Status

Implementation candidate — offline deterministic microstructure research only.

Owner: `MicrostructureDomain`  
Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
Gate: `GO_LOT44_IMPLEMENTATION_ENTRY`  
Gate merge: `6bbf4fcc5543f2599378bcab93263e2c8cebcec6`

## Implemented scope

- Lot 37 trade fixture consumption without mutating raw `UNKNOWN` side.
- Canonical Lot 38 `OrderBookSnapshotV1` quote source.
- Quote-test-first aggressor classification.
- Policy-gated tick-rule fallback only when quote data is absent.
- `BUY_AGGRESSOR`, `SELL_AGGRESSOR`, `UNKNOWN` with method attribution.
- Descriptive confidence metadata, not probability/model inference.
- Unknown-volume preservation and conservation metrics.
- Causal quote checks and explicit future/stale/locked degradation.
- Deterministic state/audit/confidence artifacts with lineage and checksums.

## Reference oracle

| trade | price | quantity | result | method |
|---|---:|---:|---|---|
| fixture-trade-001 | 50025.00 | 0.05 | UNKNOWN | NONE |
| fixture-trade-002 | 50025.10 | 0.08 | BUY_AGGRESSOR | QUOTE_TEST |
| fixture-trade-003 | 50024.90 | 0.03 | SELL_AGGRESSOR | QUOTE_TEST |

Expected volumes: total `0.16`, buy `0.08`, sell `0.03`, unknown `0.05`; `unknown_volume_ratio=0.3125`.

## Frozen input lineage

- Lot 44 entry gate checksum: `100d21ea18cfd7d9fe275ac0bea162c76a0bb7e5f85e319b543b4053e3c4d5ef`
- Lot 43 state: `30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6`
- Lot 43 audit: `3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67`
- Lot 43 resilience: `598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb`
- Lot 43 post-merge audit: `167c69b324377ceefd322d59fab7f42d9f7998efde94503d6d86ca4a51ed9c14`
- Lot 37 trade fixture SHA256: `b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8`
- Lot 38 snapshot checksum: `0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16`

## Safety

No network, live data, credentials, signal, risk approval, routing, trading or execution. `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.

Lot 45 Order Flow/Delta/CVD and Lot 46 Trade Classification Confidence Engine remain outside this implementation and physically locked.

## Validation target

Final source certification must demonstrate line coverage >=95%, branch coverage >=90%, mutation >=80%, deterministic replay, full repository regression, three targeted anti-flake replays and substantive review with no blocker before merge.
