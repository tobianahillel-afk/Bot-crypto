# Roadmap canonique V1 → V21 — Lots 0 à 177

Projet : **Crypto Quant Bot V4.1-Ops**

Ce document est l’index canonique de progression. Les spécifications détaillées de chaque version vivent dans `docs/roadmap/V01_*.md` à `V21_*.md`. Pour les lots déjà certifiés, les critères d’acceptation, rapports PASS, artefacts, audits post-merge et commits exacts prévalent sur toute synthèse de roadmap.

## État actuel

- Dernier lot fusionné et audité : **Lot 44 — Trades & Aggressor Classification Schema**.
- Release correspondant au dernier lot fusionné : `0.44.0`.
- V1 (Lots 0–20) : fermée et validée.
- V2 (Lots 21–30) : fermée et validée offline.
- V3 (Lots 31–36) : fermée et auditée ; aucune connectivité/ingestion live n’est ouverte.
- V4 (Lots 37–52) : **active**.
- Lots 37–44 : fusionnés, certifiés et audités dans le runtime `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.
- Lot 45 — **Order Flow, Delta & CVD Engine** : seul lot d’implémentation actuellement ouvert ; candidat en certification exacte sur la PR #66.
- Lots 46–52 : verrouillés jusqu’au merge du Lot 45, audit post-merge indépendant et décision explicite `GO_LOT45_POST_MERGE`.
- V5–V18 : planifiées et verrouillées.
- V19–V21 : extensions optionnelles de recherche/contexte, verrouillées et non exécutables.
- Forecast, alpha, risk approval, paper, portfolio execution, sandbox, live et capital réel : `NO_GO` tant que leurs gates dédiés ne sont pas atteints.
- Trading, exécution exchange, levier et withdrawals restent interdits dans l’état courant.

La branche `main` porte le gate certifié du Lot 45 (`390d0779f2be257fa8134faf8f02193a760a09c3` au moment de l’ouverture de la PR #66), issu du `GO_LOT44_POST_MERGE`. Le registre `data/audit/product_scope_roadmap_lot21.jsonl` reste une preuve historique immuable : il ne doit pas être interprété comme l’état runtime courant des lots ultérieurs.

## Lifecycle synthétique Lots 26–45

| Lot | Capability | État courant |
|---:|---|---|
| 26 | Multi-Timeframe Alignment | IMPLEMENTED / VALIDATED |
| 27 | Global Market Context | IMPLEMENTED / VALIDATED |
| 28 | Explanation Core / Why-Not-Trade | IMPLEMENTED / VALIDATED |
| 29 | Deterministic Replay & Audit | IMPLEMENTED / VALIDATED |
| 30 | V2 Closure | IMPLEMENTED / VALIDATED / V2 CLOSED |
| 31 | Market Data Source Registry | IMPLEMENTED / VALIDATED |
| 32 | Instrument/Symbol Normalization | IMPLEMENTED / VALIDATED |
| 33 | Timestamp/Clock/Timezone Governance | IMPLEMENTED / VALIDATED |
| 34 | Market Data Quality Engine | IMPLEMENTED / VALIDATED |
| 35 | Candle/Trade/Book Reconciliation | IMPLEMENTED / VALIDATED |
| 36 | Freshness/Gap/Outage + V3 Closure | IMPLEMENTED / VALIDATED / V3 CLOSED |
| 37 | Microstructure Scope & Offline Contracts | IMPLEMENTED / AUDITED |
| 38 | Order Book L2 Snapshot Engine | IMPLEMENTED / AUDITED |
| 39 | Order Book Delta & Sequence Reconstruction | IMPLEMENTED / AUDITED |
| 40 | Book Integrity / Desynchronization | IMPLEMENTED / AUDITED |
| 41 | Spread / Depth / Imbalance | IMPLEMENTED / AUDITED |
| 42 | Liquidity Zones / Walls / Voids | IMPLEMENTED / AUDITED |
| 43 | Book Resilience / Replenishment | IMPLEMENTED / AUDITED |
| 44 | Trades & Aggressor Classification | IMPLEMENTED / AUDITED |
| 45 | Order Flow / Delta / CVD | IMPLEMENTATION CANDIDATE — CERTIFICATION IN PROGRESS |

Aucun statut `IMPLEMENTED`, `AUDITED` ou `GO` ne doit être déduit d’un simple workflow vert : la preuve doit porter sur le commit/source exact annoncé par le lot.

## Marqueurs historiques certifiés

Ces marqueurs sont conservés textuellement parce qu’ils font partie des contrats de preuve des releases historiques. Leur présence ne signifie pas que l’état courant du projet s’arrête à ces lots.

- Lot 26 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 27 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 28 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 29 : `IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY`.
- Lot 30 : `IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY`.
- Lot 31 : `IMPLEMENTED_VALIDATED_METADATA_ONLY`.
- Lot 32 : `IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY`.
- Lot 33 : `IMPLEMENTED_VALIDATED_TEMPORAL_ONLY`.
- Lot 34 : `IMPLEMENTED_VALIDATED_DATA_QUALITY_ONLY`.
- Lot 35 : `IMPLEMENTED_VALIDATED_RECONCILIATION_ONLY`.
- Lot 36 : `IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY`.
- Lot 37 : `IMPLEMENTED_VALIDATED_OFFLINE_SCOPE_CONTRACTS_ONLY`.

## Lot 30

La preuve historique de clôture V2 reste liée à `data/audit/closure_manifest_lot30.json`, `docs/LOT_30_POST_MERGE_AUDIT.md` et `data/audit/roadmap_lifecycle_overlay_lot30.json`. Elle n’est pas réécrite par V4.

## Lot 32

La preuve historique de normalisation reste liée à `data/audit/instrument_symbol_and_contract_normalization_lot32.json`, `data/audit/instrument_registry_lot32.json`, `docs/LOT_32_POST_MERGE_AUDIT.md` et `data/audit/roadmap_lifecycle_overlay_lot32.json`.

## Documents normatifs transverses

- [Master System Specification](MASTER_SYSTEM_SPECIFICATION.md)
- [System Execution Architecture](SYSTEM_EXECUTION_ARCHITECTURE.md)
- [Functional Coverage Registry](FUNCTIONAL_COVERAGE_REGISTRY.md)
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
- [Canonical Portfolio Risk, Sizing, Reservation and Exit Standard](CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md)

## Architecture quantitative multi-échelle

- [Temporal Multi-Scale and Decision Clock Architecture](TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md)
- [Stochastic Continuous State and Multi-Horizon Forecasting Standard](STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md)
- [Participant Behavior and Liquidity Exit-Zone Inference Standard](PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md)
- [Protective Orders and Exit Lifecycle Standard](PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md)
- [V3 continuous market-data addendum](roadmap/V03_CONTINUOUS_MARKET_DATA_NORMATIVE_ADDENDUM.md)
- [V4 participant/Game Theory addendum](roadmap/V04_PARTICIPANT_GAME_THEORY_NORMATIVE_ADDENDUM.md)
- [V5 multi-horizon forecasting addendum](roadmap/V05_MULTI_HORIZON_FORECASTING_NORMATIVE_ADDENDUM.md)
- [V7/V9 portfolio-risk normative addendum](roadmap/V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md)
- [V15 protective-order addendum](roadmap/V15_PROTECTIVE_ORDER_LIFECYCLE_NORMATIVE_ADDENDUM.md)
- [Cross-version roadmap addendum](roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md)

Ces documents décrivent l’architecture cible. Ils ne signifient jamais qu’une capability future est activée avant son lot propriétaire et son gate.

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

Les documents détaillés de version sont dans `docs/roadmap/` et doivent contenir les Lots 0–177 exactement une fois.

## Séparations obligatoires

```text
data resolution ≠ feature lookback ≠ forecast horizon
decision clock ≠ signal TTL ≠ holding horizon
alignment ≠ forecast ≠ scenario ≠ signal
signal ≠ trade intent ≠ portfolio snapshot ≠ risk approval ≠ risk reservation ≠ order intent
order intent ≠ ordre soumis ≠ fill ≠ position réconciliée
CI verte ≠ validation mathématique ≠ preuve statistique ≠ alpha économique
agreement score ≠ probability ≠ expected return
source registry ≠ connector ≠ ingestion ≠ validated market event
instrument registry ≠ live metadata fetch ≠ market event ≠ signal
microstructure contract ≠ live book ingestion ≠ signal ≠ execution
```

## Profil temporel initial Lot 26

```text
timebar-5m → timebar-15m
join = ASOF_BACKWARD
trigger = CLOSED_LOCAL_BAR
```

Cette relation est une arête de configuration. Elle ne constitue pas un vote naïf entre timeframes et n’autorise aucune inférence de rendement futur.

## Règles de progression

1. Ne jamais renuméroter ou réécrire rétroactivement un lot certifié.
2. Aucun lot suivant sans rapport final `GO`, validation exacte disponible et revue humaine.
3. Chaque lot atteint les seuils de tests, couverture et mutation applicables.
4. Toute formule suit le standard mathématique et possède des oracles indépendants adaptés.
5. Toute probabilité requiert une calibration versionnée ; les lots V1–V4 n’en produisent pas comme autorisation de trading.
6. Toute décision ou absence de décision est rejouable et auditable.
7. Zéro BLOCKER et zéro MAJOR avant promotion.
8. HFT, options et on-chain ne contournent jamais le core.
9. V4 possède la microstructure/Game Theory ; V5 possède la prévision/alpha.
10. Les horizons ne sont jamais agrégés par vote naïf.
11. Les données ajoutées démontrent leur valeur par ablation et hors échantillon quand elles sont utilisées pour une hypothèse prédictive.
12. Un statut `PLANNED_LOCKED`, `CERTIFICATION_IN_PROGRESS` ou `AWAITING_EXACT_COMMIT_CI` ne peut être promu sans preuve exacte.
13. V7, V8, V9, V15 et V17 consomment les snapshots, décisions, sizing et réservations canoniques ; aucune implémentation locale incompatible n’est autorisée.
14. Tout ordre augmentant le risque exige une réservation atomique active ; toute moyenne à la baisse implicite est interdite.
15. Les Lots 37–44 sont des preuves historiques V4 fusionnées/auditées et ne doivent pas être réécrits pour simuler une nouvelle progression.
16. Le Lot 45 est limité à Order Flow / Delta / CVD offline. Il ne produit aucune permission de trading et ne peut ouvrir implicitement le Lot 46.
17. Le Lot 46 reste `PLANNED_LOCKED` jusqu’au merge du Lot 45, audit post-merge indépendant et décision humaine explicite `GO_LOT45_POST_MERGE`.
18. Un workflow dédié vert n’est recevable que si le SHA qu’il checkout/certifie correspond explicitement au candidat annoncé.

## Point de reprise opérationnel

Pour la PR #66, l’ordre de certification reste :

```text
source candidate exact
→ dedicated validation + coverage sur ce SHA
→ dedicated mutation sur ce SHA
→ evidence canonique régénérée
→ freeze/validator immuables
→ frozen attestation
→ matrice CI exacte
→ review Codex finale du HEAD figé
→ merge
→ audit post-merge indépendant
→ GO_LOT45_POST_MERGE
→ seulement ensuite gate Lot46
```
