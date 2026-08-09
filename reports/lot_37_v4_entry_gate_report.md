# Lot 37 — V4 Entry Gate Report

## Verdict

`GO_LOT37_IMPLEMENTATION_ENTRY`

The audited V3 release at `33fba0abf7463fc54a36282476ee51655ff09919` satisfies the version-transition prerequisites for opening the first V4 lot. This report authorizes **Lot 37 scope/contracts implementation only**; it does not implement microstructure business engines and does not unlock Lot 38.

## Canonical identity

- Lot: `37`
- Title: `Microstructure Scope & Offline Data Contracts`
- Version: `V4_MICROSTRUCTURE_LIQUIDITY`
- Owner: `MicrostructureDomain`
- Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- Package boundary: `src/crypto_quant_bot/microstructure`
- Canonical roadmap blob: `84de51bda788a8d124fb7d344419c4a4b12030b5`
- Canonical roadmap line: `38`
- Gate checksum: `37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d`

## V3 closure evidence

- audited release: `0.36.0`;
- lifecycle latest lot: `36`;
- V3 closed: `true`;
- Lot 36 status: `IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY`;
- post-merge audit merge: `33fba0abf7463fc54a36282476ee51655ff09919`;
- state checksum: `635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592`;
- audit checksum: `ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42`;
- manifest checksum: `6a9935e728a93a23a3804106dc54aa216f4f9fedad3635b5507139f4ccbfc37f`;
- replay checksum: `cef50b5191c1f3c78baaa3906c4c5ded59f1dd45dad0271a0071b7056b6af91d`;
- coverage: `100.00%` lines / `100.00%` branches;
- mutation: `83.48%`;
- anti-flake: `3` repetitions PASS.

## Offline input availability proof

Two deterministic fixtures prove that representative L2 and trade-shaped input is available for contract-definition tests:

- L2: `tests/fixtures/lot37/offline_l2_availability_fixture_v1.json` — SHA-256 `f3715a14e8f04395b9ca5b514ac01ff8fcf924b82812f3388fdf500d6ecf5ece`;
- trades: `tests/fixtures/lot37/offline_trade_availability_fixture_v1.json` — SHA-256 `b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8`.

Both are `fixture_only=true`, `canonical_contract=false`, `used_for_decision=false`. They are not live ingestion and do not implement Lot 38. Trade sides remain `UNKNOWN`, so this gate does not perform aggressor classification.

## Authorized implementation

Lot 37 may define:

- V4 domain scope and ownership;
- versioned offline data contracts;
- contract registry;
- capability matrix;
- public API and dependency boundaries;
- configuration/lineage binding;
- deterministic state/audit persistence;
- fail-closed validation and forbidden-capability tests.

Required outputs are exactly:

- `MicrostructureScopeOfflineDataContractsStateV1`;
- `MicrostructureScopeOfflineDataContractsAuditV1`;
- `MicrostructureScopeOfflineDataContractsContractRegistryV1`;
- `MicrostructureScopeOfflineDataContractsCapabilityMatrixV1`.

## Locked capabilities

Lot 38+ microstructure algorithms remain locked: canonical L2 snapshot, deltas/sequencing, book integrity, spread/depth/imbalance, liquidity zones, resilience, aggressor classification, order flow/CVD, hidden-liquidity inference, stop-zone inference, trap/sweep scenarios, derivatives context and game-theory aggregation.

Forecasts, signals, risk approval, order routing, trading and execution remain forbidden. Participant intent may never be represented as fact without evidence, and `scenario_score != signal`.

## Safety

External connectivity, network ingestion, live exchange data, real credentials, raw mutation, market publication, signal generation, risk approval, order routing, trading and execution remain disabled. `approved_size=0`.

## Next boundary

Lot 38 remains `PLANNED_LOCKED`. It requires Lot 37 implementation + validation + independent post-merge audit followed by a distinct entry gate.
