# Roadmap canonique V1 → V21 — Lots 0 à 177

Projet : **Crypto Quant Bot V3.1-Ops**

## État actuel

- Dernier lot dont l'implémentation est terminée : **Lot 30**.
- Version courante : `0.30.0`.
- Baseline P0 institutionnelle : fusionnée.
- Gate transversal P0.6 : fusionné et conservé comme preuve historique.
- Lot 26 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 27 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 28 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 29 : `IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY`.
- Lot 30 : `IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY`.
- Lots 31–177 : planifiés et verrouillés.
- V2 Market Analysis Offline est fermée pour le périmètre Lots 21–30, sans permission de décision ou d'exécution.
- Forecast, alpha, paper, sandbox et capital réel : `NO_GO`.

L'état courant est porté par `data/audit/roadmap_lifecycle_overlay_lot30.json`. Le registre
`data/audit/product_scope_roadmap_lot21.jsonl` reste une preuve historique immuable.

## Documents normatifs transverses

- [Master System Specification](MASTER_SYSTEM_SPECIFICATION.md)
- [System Execution Architecture](SYSTEM_EXECUTION_ARCHITECTURE.md)
- [Domain Boundaries and Ownership](DOMAIN_BOUNDARIES_AND_OWNERSHIP.md)
- [Canonical Data and Event Contracts](CANONICAL_DATA_AND_EVENT_CONTRACTS.md)
- [Runtime Modes and State Machines](RUNTIME_MODES_AND_STATE_MACHINES.md)
- [Strategy Lifecycle and Promotion Gates](STRATEGY_LIFECYCLE_AND_PROMOTION_GATES.md)
- [Veto Consequence Matrix](VETO_CONSEQUENCE_MATRIX.md)
- [Configuration / CI / Release Governance](CONFIGURATION_RELEASE_AND_ENVIRONMENT_GOVERNANCE.md)
- [Failure and Recovery Policy](FAILURE_DEGRADED_AND_RECOVERY_POLICY.md)
- [Lot Specification Standard](LOT_SPECIFICATION_STANDARD.md)
- [Test Strategy, Coverage and Quality Gates](TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md)
- [Mathematical Modeling and Numerical Validation](MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md)
- [Development Engineering Standard](DEVELOPMENT_ENGINEERING_STANDARD.md)
- [Decision Auditability and Traceability](DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md)
- [Lot Final Audit and GO / NO-GO Gate](LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md)
- [Capability and Contract Ownership Registry](CAPABILITY_AND_CONTRACT_OWNERSHIP_REGISTRY.md)
- [Model Retraining and Promotion Policy](MODEL_RETRAINING_AND_PROMOTION_POLICY.md)
- [Economic Objective and Risk Utility Policy](ECONOMIC_OBJECTIVE_AND_RISK_UTILITY_POLICY.md)
- [Canonical Portfolio Risk, Sizing, Reservation and Exit Standard](CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md)

## Architecture quantitative multi-échelle

- [Temporal Multi-Scale and Decision Clock Architecture](TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md)
- [Stochastic Continuous State and Multi-Horizon Forecasting Standard](STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md)
- [Participant Behavior and Liquidity Exit-Zone Inference Standard](PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md)
- [Protective Orders and Exit Lifecycle Standard](PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md)
- [V7/V9 portfolio-risk normative addendum](roadmap/V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md)
- [Cross-version roadmap addendum](roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md)
- [V3 continuous market-data addendum](roadmap/V03_CONTINUOUS_MARKET_DATA_NORMATIVE_ADDENDUM.md)
- [V4 participant/Game Theory addendum](roadmap/V04_PARTICIPANT_GAME_THEORY_NORMATIVE_ADDENDUM.md)
- [V5 multi-horizon forecasting addendum](roadmap/V05_MULTI_HORIZON_FORECASTING_NORMATIVE_ADDENDUM.md)
- [V15 protective-order addendum](roadmap/V15_PROTECTIVE_ORDER_LIFECYCLE_NORMATIVE_ADDENDUM.md)

Ces documents sont normatifs pour les lots futurs. Ils ne signifient pas que les capacités
prédictives ou d'exécution sont déjà implémentées.

## Lot 26

- [Specification](LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [Acceptance criteria](ACCEPTANCE_CRITERIA_LOT_26.md)
- [Implementation status](LOT_26_IMPLEMENTATION_WORKLOG.md)
- [Requirement-test matrix](LOT26_REQUIREMENT_TEST_MATRIX.md)
- [Time semantics ADR](adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md)
- [Temporal contracts](contracts/LOT26_TEMPORAL_CONTRACTS.md)
- [Mathematical specification](math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md)
- [V2 normative addendum](roadmap/V02_LOT26_NORMATIVE_ADDENDUM.md)
- Configuration : `config/math/multi_timeframe_alignment_v1.json`
- Temporal scale registry : `config/temporal/temporal_scale_registry_v1.json`
- Decision clock policy : `config/temporal/decision_clock_policy_v1.json`
- Runner : `scripts/run_lot26_multi_timeframe_alignment_engine.py`
- Validator : `scripts/validate_lot26.py`

## Lot 28

- [Specification](LOT_28_EXPLANATION_CORE_AND_WHY_NOT_TRADE_LAYER.md)
- [Acceptance criteria](ACCEPTANCE_CRITERIA_LOT_28.md)
- [Implementation status](LOT_28_IMPLEMENTATION_WORKLOG.md)
- Configuration : `config/explanations/explanation_core_why_not_trade_v1.json`
- Schema : `contracts/schemas/explanation_core_why_not_trade_layer_state_v1.schema.json`
- Runner : `scripts/run_lot28_explanation_core_and_why_not_trade_layer.py`
- Validator : `scripts/validate_lot28.py`
- Lifecycle overlay : `data/audit/roadmap_lifecycle_overlay_lot28.json`

## Lot 29

- [Specification](LOT_29_V2_DETERMINISTIC_REPLAY_AND_AUDIT.md)
- [Acceptance criteria](ACCEPTANCE_CRITERIA_LOT_29.md)
- [Implementation status](LOT_29_IMPLEMENTATION_WORKLOG.md)
- [Post-merge audit](LOT_29_POST_MERGE_AUDIT.md)
- Configuration : `config/replay/v2_deterministic_replay_audit_v1.json`
- Schema : `contracts/schemas/v2_deterministic_replay_audit_state_v1.schema.json`
- State : `data/audit/v2_deterministic_replay_and_audit_lot29.json`
- Audit : `data/audit/v2_deterministic_replay_and_audit_audit_lot29.json`
- Closure manifest : `data/audit/v2_replay_closure_manifest_lot29.json`
- Report : `reports/lot_29_v2_deterministic_replay_and_audit_report.md`
- Runner : `scripts/run_lot29_v2_deterministic_replay_and_audit.py`
- Validator : `scripts/validate_lot29.py`
- Lifecycle overlay : `data/audit/roadmap_lifecycle_overlay_lot29.json`

## Lot 30

- [Specification](LOT_30_V2_MARKET_ANALYSIS_CLOSURE.md)
- [Acceptance criteria](ACCEPTANCE_CRITERIA_LOT_30.md)
- [Implementation status](LOT_30_IMPLEMENTATION_WORKLOG.md)
- [Post-merge audit](LOT_30_POST_MERGE_AUDIT.md)
- Configuration : `config/closure/v2_market_analysis_closure_v1.json`
- Schema : `contracts/schemas/v2_market_analysis_closure_state_v1.schema.json`
- State : `data/audit/v2_market_analysis_closure_lot30.json`
- Audit : `data/audit/v2_market_analysis_closure_audit_lot30.json`
- Final V2 manifest : `data/audit/closure_manifest_lot30.json`
- Report : `reports/lot_30_v2_market_analysis_closure_report.md`
- Coverage evidence : `reports/lot30/coverage_summary.json`
- Mutation evidence : `reports/lot30/mutation/score.json`
- Runner : `scripts/run_lot30_v2_market_analysis_closure.py`
- Validator : `scripts/validate_lot30.py`
- Lifecycle overlay : `data/audit/roadmap_lifecycle_overlay_lot30.json`

## Séparations obligatoires

```text
data resolution ≠ feature lookback ≠ forecast horizon
decision clock ≠ signal TTL ≠ holding horizon
alignment ≠ forecast ≠ scenario ≠ signal
signal ≠ trade intent ≠ portfolio snapshot ≠ risk approval ≠ risk reservation ≠ order intent
order intent ≠ ordre soumis ≠ fill ≠ position réconciliée
CI verte ≠ validation mathématique ≠ preuve statistique ≠ alpha économique
agreement score ≠ probability ≠ expected return
```

## Profil temporel Lot 26

```text
timebar-5m → timebar-15m
join = ASOF_BACKWARD
trigger = CLOSED_LOCAL_BAR
```

Cette relation est une arête de configuration. Elle ne constitue pas un vote naïf entre
timeframes et n'autorise aucune inférence de rendement futur.

## Versions

| Version | Phase | Lots | Responsabilité principale | Mode maximal |
|---:|---|---:|---|---|
| V1 | Defensive Audit / No Trading | 0–20 | barrières, audit, immutabilité | `EDUCATIONAL_AUDIT_ONLY` |
| V2 | Market Analysis Offline | 21–30 | contextes et alignement descriptif | `LOCAL_OFFLINE_ANALYSIS_ONLY` |
| V3 | Market Data Governance | 31–36 | flux canonique, temps et qualité | `DATA_GOVERNANCE_ONLY` |
| V4 | Microstructure / Liquidity / Game Theory | 37–52 | carnet, order flow, participants | `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY` |
| V5 | Alpha / Strategy Research | 53–59 | prévisions et stratégies | `OFFLINE_STRATEGY_RESEARCH_ONLY` |
| V6 | Backtesting / Expected Value / TCA | 60–71 | OOS, coûts, capacité | `BACKTEST_ONLY` |
| V7 | Model Risk / Sizing / Risk | 72–80 | risque et sizing | `RISK_SIMULATION_ONLY` |
| V8 | Paper Trading | 81–87 | simulation décisions/ordres | `PAPER` |
| V9 | Portfolio / PnL Core | 88–95 | positions, cash et PnL | `PORTFOLIO_ACCOUNTING` |
| V10 | Research OS | 96–102 | gouvernance de recherche | `RESEARCH_GOVERNANCE_ONLY` |
| V11 | News / AI / Event Context | 103–110 | contexte événementiel | `READ_ONLY_CONTEXT_ONLY` |
| V12 | UI / Operator Console | 111–118 | explication opérateur | `OPERATOR_UI` |
| V13 | API / Account Read-Only | 119–125 | état exchange/account | `READ_ONLY` |
| V14 | Exchange Risk / API Health | 126–132 | santé venue/API | `EXCHANGE_HEALTH_ONLY` |
| V15 | OMS / EMS Core | 133–141 | lifecycle ordre | `ORDER_MANAGEMENT_CORE` |
| V16 | Sandbox / Demo Execution | 142–149 | exécution sandbox | `SANDBOX` |
| V17 | Live Governance | 150–157 | approbation humaine | `LIVE_DISABLED_BY_DEFAULT` |
| V18 | Observability / Incident Response | 158–165 | incidents et recovery | `OPERATIONS_GOVERNANCE` |
| V19 | HFT Research | 166–171 | tick/L2/L3 research-only | `HFT_RESEARCH_ONLY` |
| V20 | Options Context | 172–174 | contexte options | `OPTIONS_CONTEXT_ONLY` |
| V21 | On-chain / Flow Intelligence | 175–177 | contexte on-chain | `ONCHAIN_CONTEXT_ONLY` |

## Règles de progression

1. Ne jamais renuméroter ou réécrire un lot implémenté.
2. Aucun lot suivant sans rapport final `GO`, CI verte sur le commit exact et revue humaine.
3. Chaque lot atteint les seuils tests, couverture et mutation applicables.
4. Toute formule suit le standard mathématique et possède des oracles indépendants.
5. Toute probabilité requiert une calibration versionnée ; les Lots 26–30 n'en produisent aucune.
6. Toute décision ou absence de décision est rejouable et auditable.
7. Zéro BLOCKER et zéro MAJOR avant promotion.
8. HFT, options et on-chain ne contournent jamais le core.
9. Lot 26 reste descriptif ; V4 possède la Game Theory ; V5 possède la prévision.
10. Les horizons ne sont jamais agrégés par vote naïf.
11. Les données ajoutées démontrent leur valeur par ablation et hors échantillon.
12. Un statut `PLANNED_LOCKED` ou `AWAITING_EXACT_COMMIT_CI` ne peut être promu sans preuve exacte.
13. V7, V8, V9, V15 et V17 consomment le snapshot, le sizing et les réservations canoniques ; aucune implémentation locale incompatible n'est autorisée.
14. Tout ordre augmentant le risque exige une réservation atomique active ; toute moyenne à la baisse implicite est interdite.
15. Lot 31 reste verrouillé après l'audit post-merge du Lot 30 jusqu'à un gate d'entrée V3 distinct et une décision humaine explicite.
