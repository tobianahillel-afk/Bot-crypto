# Roadmap canonique V1 → V21 — Lots 0 à 177

Projet : **Crypto Quant Bot V3.1-Ops**

## État actuel

- Dernier lot implémenté et validé : **Lot 25**.
- Baseline P0 institutionnelle : fusionnée.
- Préparation Lot 26 : contrats et gate de readiness en cours de revue.
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

## Pré-Lot26 normatif

- [PRE_LOT26_ENTRY_GATE](PRE_LOT26_ENTRY_GATE.md)
- [Lot 26 specification](LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [Lot 26 acceptance criteria](ACCEPTANCE_CRITERIA_LOT_26.md)
- [Time semantics ADR](adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md)
- [Lot 26 temporal contracts](contracts/LOT26_TEMPORAL_CONTRACTS.md)
- [Lot 26 mathematical specification](math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md)
- [V2 Lot 26 normative addendum](roadmap/V02_LOT26_NORMATIVE_ADDENDUM.md)

## Principe de séparation

```text
Analyse ≠ scénario ≠ signal ≠ trade intent ≠ order intent
Order intent ≠ ordre soumis ≠ fill ≠ position
Stratégie validée ≠ autorisation live
CI verte ≠ validation mathématique ≠ GO de promotion
Coverage élevé ≠ correction prouvée
agreement score ≠ probability ≠ alpha
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

## Spécifications détaillées par version

Les 21 documents sont dans [`docs/roadmap/`](roadmap/). L’addendum Lot 26 prévaut sur toute
formulation moins précise du document V2.

## Règles de modification

1. Ne jamais renuméroter un lot implémenté.
2. Aucun lot suivant sans rapport final `GO`, CI verte sur le commit exact et revue humaine.
3. Chaque lot atteint les seuils de tests/coverage/mutation applicables.
4. Toute formule suit le standard mathématique.
5. Toute décision/veto est rejouable et auditable.
6. Zéro BLOCKER et zéro MAJOR avant promotion.
7. HFT/options/on-chain ne contournent jamais le core.
8. Game Theory reste propriétaire de la microstructure V4, pas du Lot 26.
