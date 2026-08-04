# Roadmap canonique V1 → V21 — Lots 0 à 177

Projet : **Crypto Quant Bot V3.1-Ops**

## État actuel

- Dernier lot implémenté et validé : **Lot 25**.
- Baseline P0 institutionnelle : fusionnée.
- Préparation Lot 26 : architecture fusionnée ; le gate transversal P0.6 est actif avant démarrage.
- Lot 26 : `PLANNED_LOCKED`, aucune implémentation métier.
- Lots 26–177 : planifiés et verrouillés.
- Recherche offline : `CONDITIONAL_GO`.
- Alpha, paper, sandbox et capital réel : `NO_GO`.

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
- [Capability and Contract Ownership Registry](CAPABILITY_AND_CONTRACT_OWNERSHIP_REGISTRY.md)
- [Model Retraining and Promotion Policy](MODEL_RETRAINING_AND_PROMOTION_POLICY.md)
- [Economic Objective and Risk Utility Policy](ECONOMIC_OBJECTIVE_AND_RISK_UTILITY_POLICY.md)

## Architecture quantitative multi-échelle

- [Temporal Multi-Scale and Decision Clock Architecture](TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md)
- [Stochastic Continuous State and Multi-Horizon Forecasting Standard](STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md)
- [Participant Behavior and Liquidity Exit-Zone Inference Standard](PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md)
- [Protective Orders and Exit Lifecycle Standard](PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md)
- [Cross-version roadmap addendum](roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md)
- [V3 continuous market-data addendum](roadmap/V03_CONTINUOUS_MARKET_DATA_NORMATIVE_ADDENDUM.md)
- [V4 participant/Game Theory addendum](roadmap/V04_PARTICIPANT_GAME_THEORY_NORMATIVE_ADDENDUM.md)
- [V5 multi-horizon forecasting addendum](roadmap/V05_MULTI_HORIZON_FORECASTING_NORMATIVE_ADDENDUM.md)
- [V15 protective-order addendum](roadmap/V15_PROTECTIVE_ORDER_LIFECYCLE_NORMATIVE_ADDENDUM.md)

Ces documents sont normatifs pour les lots futurs. Ils n'indiquent pas que les capabilities sont déjà implémentées.

## Pré-Lot26 normatif

- [PRE_LOT26_ENTRY_GATE](PRE_LOT26_ENTRY_GATE.md)
- [Lot 26 specification](LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [Lot 26 acceptance criteria](ACCEPTANCE_CRITERIA_LOT_26.md)
- [Lot 26 requirement-test matrix](LOT26_REQUIREMENT_TEST_MATRIX.md)
- [Time semantics ADR](adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md)
- [Lot 26 temporal contracts](contracts/LOT26_TEMPORAL_CONTRACTS.md)
- [Lot 26 mathematical specification](math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md)
- [V2 Lot 26 normative addendum](roadmap/V02_LOT26_NORMATIVE_ADDENDUM.md)
- Temporal scale registry: `config/temporal/temporal_scale_registry_v1.json`
- Decision clock policy: `config/temporal/decision_clock_policy_v1.json`
- Forecast horizon registry: `config/research/forecast_horizon_registry_v1.json`
- Domain ownership registry: `config/governance/domain_ownership_registry_v1.json`
- Decision evidence schema: `contracts/schemas/decision_evidence_envelope_v1.schema.json`
- Domain ownership registry: `config/governance/domain_ownership_registry_v1.json`
- Decision evidence schema: `contracts/schemas/decision_evidence_envelope_v1.schema.json`

## Principe de séparation

```text
data resolution ≠ feature lookback ≠ forecast horizon
decision clock ≠ signal TTL ≠ holding horizon
alignment ≠ forecast ≠ scenario ≠ signal
signal ≠ trade intent ≠ risk approval ≠ order intent
order intent ≠ ordre soumis ≠ fill ≠ position réconciliée
CI verte ≠ validation mathématique ≠ preuve statistique ≠ alpha économique
agreement score ≠ probability ≠ expected return
```

## Vision temporelle

Le système cible un flux canonique continu. Les 5m et 15m constituent le profil initial du Lot 26 :

```text
timebar-5m → timebar-15m
```

Cette relation est une arête de configuration, pas une architecture figée. Les futures résolutions et horloges sont ajoutées par registre et gate, sans vote majoritaire naïf.

## Versions

| Version | Phase | Lots | Responsabilité temporelle/quantitative | Mode maximal |
|---:|---|---:|---|---|
| V1 | Defensive Audit / No Trading | 0–20 | barrières, audit, immutabilité | `EDUCATIONAL_AUDIT_ONLY` |
| V2 | Market Analysis Offline | 21–30 | contextes de barres, alignement 5m→15m extensible | `LOCAL_OFFLINE_ANALYSIS_ONLY` |
| V3 | Market Data Governance | 31–36 | flux canonique, temps, qualité, réconciliation data | `DATA_GOVERNANCE_ONLY` |
| V4 | Microstructure / Liquidity / Game Theory | 37–52 | état continu, carnet, order flow, participants et zones | `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY` |
| V5 | Alpha / Strategy Research | 53–59 | prévisions stochastiques multi-horizons et stratégies | `OFFLINE_STRATEGY_RESEARCH_ONLY` |
| V6 | Backtesting / Expected Value / TCA | 60–71 | calibration, OOS, coûts, capacité et robustesse | `BACKTEST_ONLY` |
| V7 | Model Risk / Sizing / Risk | 72–80 | risque et sizing par distribution/horizon | `RISK_SIMULATION_ONLY` |
| V8 | Paper Trading | 81–87 | simulation des décisions et ordres protecteurs | `PAPER` |
| V9 | Portfolio / PnL Core | 88–95 | positions, cash, PnL et attribution | `PORTFOLIO_ACCOUNTING` |
| V10 | Research OS | 96–102 | gouvernance des recherches et expériences | `RESEARCH_GOVERNANCE_ONLY` |
| V11 | News / AI / Event Context | 103–110 | contexte événementiel read-only | `READ_ONLY_CONTEXT_ONLY` |
| V12 | UI / Operator Console | 111–118 | explication et contrôle opérateur | `OPERATOR_UI` |
| V13 | API Read-Only / Account Read-Only | 119–125 | état exchange/account read-only | `READ_ONLY` |
| V14 | Exchange Risk / API Health | 126–132 | santé venue/API et permissions | `EXCHANGE_HEALTH_ONLY` |
| V15 | OMS / EMS Core | 133–141 | lifecycle ordre et protections réconciliables | `ORDER_MANAGEMENT_CORE` |
| V16 | Sandbox / Demo Execution | 142–149 | exécution sandbox | `SANDBOX` |
| V17 | Live Governance / Human Approval | 150–157 | approbation et live désactivé par défaut | `LIVE_DISABLED_BY_DEFAULT` |
| V18 | Observability / Incident Response | 158–165 | monitoring, incidents et recovery | `OPERATIONS_GOVERNANCE` |
| V19 | HFT Research | 166–171 | tick/L2/L3, queue, latence research-only | `HFT_RESEARCH_ONLY` |
| V20 | Options Context | 172–174 | contexte options | `OPTIONS_CONTEXT_ONLY` |
| V21 | On-chain / Flow Intelligence | 175–177 | contexte on-chain | `ONCHAIN_CONTEXT_ONLY` |

## Règles de modification

1. Ne jamais renuméroter ou réécrire un lot implémenté.
2. Aucun lot suivant sans rapport final `GO`, CI verte sur le commit exact et revue humaine.
3. Chaque lot atteint les seuils tests/coverage/mutation applicables.
4. Toute formule suit le standard mathématique.
5. Toute probabilité suit une calibration versionnée.
6. Toute décision/veto est rejouable et auditable.
7. Zéro BLOCKER et zéro MAJOR avant promotion.
8. HFT/options/on-chain ne contournent jamais le core.
9. Lot 26 reste descriptif ; V4 possède la Game Theory ; V5 possède la prévision.
10. Les horizons ne sont jamais agrégés par vote naïf.
11. Les données ajoutées doivent démontrer leur valeur par ablation et hors échantillon.
12. Un contrat `PLANNED_LOCKED` ne devient implémenté qu'après preuves CI et rapport de lot.
