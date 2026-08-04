# V2 Product Roadmap — document historique

Ce fichier est conservé pour compatibilité avec les artefacts du Lot 21.

La roadmap canonique est :

- [`ROADMAP_V1_TO_V21.md`](ROADMAP_V1_TO_V21.md)
- [`roadmap/`](roadmap/)
- [`FUNCTIONAL_COVERAGE_REGISTRY.md`](FUNCTIONAL_COVERAGE_REGISTRY.md)
- `data/audit/product_scope_roadmap_lot21.jsonl`

## État courant

- V1 / Lots 0–20 : fermée et archivée.
- Lot 21 : scope lock validé.
- Lots 22–25 : Market Analysis descriptive implémentée.
- P0 institutionnel : fusionné.
- Lot 26 : prochain lot, encore `PLANNED_LOCKED`.
- Lots 26–177 : planifiés et verrouillés.

## Addendum normatif Lot 26

- [`PRE_LOT26_ENTRY_GATE.md`](PRE_LOT26_ENTRY_GATE.md)
- [`LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md`](LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [`ACCEPTANCE_CRITERIA_LOT_26.md`](ACCEPTANCE_CRITERIA_LOT_26.md)
- [`LOT26_REQUIREMENT_TEST_MATRIX.md`](LOT26_REQUIREMENT_TEST_MATRIX.md)
- [`roadmap/V02_LOT26_NORMATIVE_ADDENDUM.md`](roadmap/V02_LOT26_NORMATIVE_ADDENDUM.md)

Le Lot 26 v1 active uniquement `timebar-5m → timebar-15m`, mais son interface doit rester extensible. Il ne produit ni forecast, ni probability, ni signal, ni ordre.

## Architecture quantitative future

- [`TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md`](TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md)
- [`STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md`](STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md)
- [`PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md`](PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md)
- [`PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md`](PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md)
- [`roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md`](roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md)

Ces documents répartissent les responsabilités entre V3 flux continu, V4 microstructure/Game Theory, V5 prévision multi-horizon, V6 validation, V7 risque et V15 OMS/ordres protecteurs.

L'ancienne projection V2→V11 / Lots 22→147 ne doit plus être utilisée comme plan d'exécution.
