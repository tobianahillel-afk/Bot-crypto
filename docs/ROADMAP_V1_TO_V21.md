# Roadmap canonique V1 → V21 — Lots 0 à 177

Projet : **Crypto Quant Bot V3.1-Ops**

Cette roadmap est la source de vérité pour les travaux futurs. Elle est complétée par les contrats d'architecture ci-dessous et par les 21 documents de version.

## État actuel

- Dernier lot implémenté et validé : **Lot 25**.
- Prochain lot : **Lot 26**.
- Lots 0–25 : historique implémenté/validé selon les preuves existantes.
- Lots 26–177 : `PLANNED_LOCKED` jusqu'à activation explicite.

## Documents normatifs

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

## Principe de séparation

```text
Analyse ≠ scénario ≠ signal ≠ trade intent ≠ order intent
Order intent ≠ ordre soumis ≠ fill ≠ position
Stratégie validée ≠ autorisation live
CI verte ≠ validation mathématique ≠ GO de promotion
Coverage élevé ≠ tests suffisants ≠ correction prouvée
```

## Versions

| Version | Phase | Lots | Mode maximal |
|---:|---|---:|---|
| V1 | Defensive Audit / No Trading | 0–20 | `EDUCATIONAL_AUDIT_ONLY` |
| V2 | Market Analysis Offline | 21–30 | `LOCAL_OFFLINE_ANALYSIS_ONLY` |
| V3 | Market Data Governance | 31–36 | `DATA_GOVERNANCE_ONLY` |
| V4 | Microstructure / Liquidity / Game Theory | 37–52 | `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY` |
| V5 | Alpha / Strategy Research | 53–59 | `OFFLINE_STRATEGY_RESEARCH_ONLY` |
| V6 | Backtesting / Expected Value / TCA | 60–71 | `BACKTEST_ONLY` |
| V7 | Model Risk / Sizing / Risk | 72–80 | `RISK_SIMULATION_ONLY` |
| V8 | Paper Trading | 81–87 | `PAPER` |
| V9 | Portfolio / PnL Core | 88–95 | `PORTFOLIO_ACCOUNTING` |
| V10 | Research OS | 96–102 | `RESEARCH_GOVERNANCE_ONLY` |
| V11 | News / AI / Event Context | 103–110 | `READ_ONLY_CONTEXT_ONLY` |
| V12 | UI / Operator Console | 111–118 | `OPERATOR_UI` |
| V13 | API Read-Only / Account Read-Only | 119–125 | `READ_ONLY` |
| V14 | Exchange Risk / API Health | 126–132 | `EXCHANGE_HEALTH_ONLY` |
| V15 | OMS / EMS Core | 133–141 | `ORDER_MANAGEMENT_CORE` |
| V16 | Sandbox / Demo Execution | 142–149 | `SANDBOX` |
| V17 | Live Governance / Human Approval | 150–157 | `LIVE_DISABLED_BY_DEFAULT` |
| V18 | Observability / Incident Response | 158–165 | `OPERATIONS_GOVERNANCE` |
| V19 | HFT Research | 166–171 | `HFT_RESEARCH_ONLY` |
| V20 | Options Context | 172–174 | `OPTIONS_CONTEXT_ONLY` |
| V21 | On-chain / Flow Intelligence | 175–177 | `ONCHAIN_CONTEXT_ONLY` |

## Spécifications détaillées

- [V1 — Defensive Audit / No Trading](roadmap/V01_DEFENSIVE_AUDIT_NO_TRADING.md) — Lots 0 à 20
- [V2 — Market Analysis Offline](roadmap/V02_MARKET_ANALYSIS_OFFLINE.md) — Lots 21 à 30
- [V3 — Market Data Governance](roadmap/V03_MARKET_DATA_GOVERNANCE.md) — Lots 31 à 36
- [V4 — Microstructure / Liquidity / Game Theory](roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md) — Lots 37 à 52
- [V5 — Alpha / Strategy Research](roadmap/V05_ALPHA_STRATEGY_RESEARCH.md) — Lots 53 à 59
- [V6 — Backtesting / Expected Value / TCA](roadmap/V06_BACKTESTING_EXPECTED_VALUE_TCA.md) — Lots 60 à 71
- [V7 — Model Risk / Sizing / Risk](roadmap/V07_MODEL_RISK_SIZING_RISK.md) — Lots 72 à 80
- [V8 — Paper Trading](roadmap/V08_PAPER_TRADING.md) — Lots 81 à 87
- [V9 — Portfolio / PnL Core](roadmap/V09_PORTFOLIO_PNL_CORE.md) — Lots 88 à 95
- [V10 — Research OS](roadmap/V10_RESEARCH_OS.md) — Lots 96 à 102
- [V11 — News / AI / Event Context](roadmap/V11_NEWS_AI_EVENT_CONTEXT.md) — Lots 103 à 110
- [V12 — UI / Operator Console](roadmap/V12_UI_OPERATOR_CONSOLE.md) — Lots 111 à 118
- [V13 — API Read-Only / Account Read-Only](roadmap/V13_API_READ_ONLY_ACCOUNT_READ_ONLY.md) — Lots 119 à 125
- [V14 — Exchange Risk / API Health](roadmap/V14_EXCHANGE_RISK_API_HEALTH.md) — Lots 126 à 132
- [V15 — OMS / EMS Core](roadmap/V15_OMS_EMS_CORE.md) — Lots 133 à 141
- [V16 — Sandbox / Demo Execution](roadmap/V16_SANDBOX_DEMO_EXECUTION.md) — Lots 142 à 149
- [V17 — Live Governance / Human Approval](roadmap/V17_LIVE_GOVERNANCE_HUMAN_APPROVAL.md) — Lots 150 à 157
- [V18 — Observability / Incident Response](roadmap/V18_OBSERVABILITY_INCIDENT_RESPONSE.md) — Lots 158 à 165
- [V19 — HFT Research](roadmap/V19_HFT_RESEARCH.md) — Lots 166 à 171
- [V20 — Options Context](roadmap/V20_OPTIONS_CONTEXT.md) — Lots 172 à 174
- [V21 — On-chain / Flow Intelligence](roadmap/V21_ON_CHAIN_FLOW_INTELLIGENCE.md) — Lots 175 à 177

## Règles de modification et validation

1. Ne jamais renuméroter un lot implémenté.
2. Toute modification met à jour roadmap, version, registry, contrats et validation report.
3. Aucun lot suivant sans rapport final `GO`, CI verte sur le commit exact et gate humain.
4. HFT/options/on-chain ne contournent jamais le core.
5. Chaque lot atteint au moins 90 % de line coverage sur le code ajouté/modifié et satisfait toutes les suites obligatoires.
6. Toute formule, probabilité, estimation ou décision quantitative suit le standard mathématique et numérique.
7. Toute décision et tout veto sont intégralement rejouables, traçables et auditables.
8. Zéro BLOCKER et zéro MAJOR avant promotion.