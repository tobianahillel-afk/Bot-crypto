# Lot 37 — Microstructure Scope & Offline Data Contracts — Implementation Report

## Status

`IMPLEMENTATION_CANDIDATE_EXACT_HEAD_EVIDENCE_FROZEN_AWAITING_MERGE`

Lot 37 production source was certified on exact source head `59b189e9980772245993a9212b6c8ad5e9a88a00`. Evidence commits after that source head are attestatory only and are required to preserve a zero diff under `src/`.

## Scope implemented

- V4 `MicrostructureDomain` package boundary created.
- Six versioned contracts registered: two offline input contracts and four Lot 37 outputs.
- Four Lot 37 public outputs implemented and frozen under `data/audit/`.
- Capability matrix keeps Lots 38–52 `PLANNED_LOCKED`.
- Dangerous capabilities remain explicitly forbidden.
- Two V4-entry fixtures are consumed only as offline, non-canonical, non-decision contract-shape evidence.
- Deterministic canonical state/audit checksums and atomic JSON persistence implemented.
- Independent persisted-artifact and frozen-evidence validators implemented.
- Contract schema paths fail closed on directory traversal (`..`).

## Explicitly not implemented

No Lot 38+ microstructure algorithm is present. Lot 37 does not perform order-book snapshot normalization, delta reconstruction, book-health scoring, spread/depth/imbalance calculation, liquidity inference, aggressor classification, order-flow/CVD calculation, derivatives modeling, scenario generation, signal generation, risk approval, order routing, trading or execution.

## Frozen upstream authority

- Audited V3 closure commit: `33fba0abf7463fc54a36282476ee51655ff09919`
- Merged V4/Lot37 entry-gate commit: `b2ec1f8ffa03c9dd48a04fe62f42c4f9986e2167`
- Lot 37 gate checksum: `37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d`
- Lot 36 state checksum: `635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592`
- Lot 36 audit checksum: `ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42`

## Exact source-head assurance

Certified source head: `59b189e9980772245993a9212b6c8ad5e9a88a00`.

The following pull-request workflows all passed on that same source head:

- Lot 37 microstructure scope and offline contracts validation — run `31325582304`;
- Lot 37 mutation assurance — run `31325582303`;
- Institutional code quality gates — run `31325582322`;
- Roadmap documentation validation — run `31325582305`;
- Lot 26 foundation and lifecycle validation — run `31325582346`.

Measured critical quality:

- line coverage: `100.00%` (minimum `95%`);
- branch coverage: `100.00%` (minimum `90%`);
- anti-flake repetitions: `3`;
- mutation: `1098 / 1368` killed, `270` survived, `0` timeout, `0` suspicious;
- mutation score: `80.26%` (minimum `80%`).

Frozen GitHub Actions evidence:

- validation/coverage artifact id `9041433151`, digest `sha256:c163bd5855ddb6ce99b36fbd52834702ee8ea9706d162acc47fe0e474a37dab4`;
- mutation artifact id `9041434170`, digest `sha256:1ce9b7ac4d87465a441403262e3764cb8bef824cdff0c3eae59bc6bf68dcef68`.

## Frozen canonical outputs

- state output checksum: `ea960217eb9a2159c4a99c56257a37c43869ffad0da86555fef24eb356e5f8e7`;
- audit checksum: `aa2df489e636860c119eb2ed54f7a5f03ede09838dfbd056dae0bb5a8a2a482f`;
- contract registry checksum: `129140ffb7e812afd59d0174d318c5e3388d23bc49cc554168bde558bc0bf590`;
- capability matrix checksum: `f7132fcfdab898af3f733b2715e0836d23e6284f8c0c1f3e7dd92ccf0070f1b4`;
- config checksum: `a6e79dae8567aeafd5b25e3793a901097dd1714e9ec6c5f19a771417e78d6a78`.

Reference membership remains fixed at 6 contracts, 27 capabilities, 4 required Lot37 capabilities, 15 future disabled V4 capabilities, 8 forbidden capabilities, 4 public API symbols and 2 offline fixtures.

## Safety

The frozen state and audit require `analysis_only=true`, `used_for_decision=false`, `external_connectivity_allowed=false`, `network_ingestion_allowed=false`, `real_credentials_allowed=false`, `market_event_publication_allowed=false`, `raw_data_mutation_allowed=false`, `scenario_score_is_signal=false`, `signal_generation_allowed=false`, `risk_approval_allowed=false`, `order_routing_allowed=false`, `trade_allowed=false`, `execution_allowed=false`, and `approved_size=0`. Participant-behavior inference must remain explicitly labeled.

## Evidence boundary

`reports/lot37/coverage_summary.json` and `reports/lot37/mutation_summary.json` freeze the exact source-head quality evidence. `scripts/validate_lot37_frozen_evidence.py` cross-checks the state, audit, registry, capability matrix, quality thresholds and Lot38 lock. The dedicated frozen-evidence workflow additionally proves that no `src/` file changed after the certified source head.

## Promotion boundary

Implementation CI passing is not a Lot38 GO. Lot 38 remains locked. After this implementation PR is merged, an independent governance-only Lot 37 post-merge audit is mandatory. Only that audit may authorize a separate Lot38 entry-gate PR.
