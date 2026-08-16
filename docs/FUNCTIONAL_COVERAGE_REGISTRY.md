# Functional Coverage Registry — V1 à V21

## Périmètre initial

- BTC/EUR spot, venue de référence Kraken, offline/paper d’abord.
- Leverage et withdrawals interdits ; live désactivé par défaut.
- Futures/perpetuals/options/on-chain restent contextuels/research jusqu’aux gates dédiés.

## État d’implémentation courant

- V1 (Lots 0–20) : fermée et validée.
- V2 (Lots 21–30) : fermée et validée offline.
- V3 (Lots 31–36) : fermée, auditée et validée ; aucune connectivité/ingestion live n’est ouverte.
- V4 : Lots 37–44 fusionnés et audités. Le Lot 45 — Order Flow / Delta / CVD est le seul lot d’implémentation actuellement ouvert et reste en certification sur la PR #66. Les Lots 46–52 restent verrouillés jusqu’au GO post-merge du Lot 45.
- V5–V18 : planifiés et verrouillés.
- V19–V21 : extensions optionnelles de recherche/contexte, non requises pour le premier produit spot et non exécutables.

## Couverture par version

| Version | Lots | Owner | Package | Mode maximal | Statut |
|---:|---:|---|---|---|---|
| V1 | 0–20 | `SafetyKernel` | `core` | `EDUCATIONAL_AUDIT_ONLY` | DONE_VALIDATED |
| V2 | 21–30 | `MarketAnalysisDomain` | `market_analysis` | `LOCAL_OFFLINE_ANALYSIS_ONLY` | DONE_VALIDATED |
| V3 | 31–36 | `MarketDataGovernanceDomain` | `data_governance` | `DATA_GOVERNANCE_ONLY` | DONE_VALIDATED |
| V4 | 37–52 | `MicrostructureDomain` | `microstructure` | `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY` | ACTIVE_PARTIAL — 37–44 DONE, 45 CERTIFICATION, 46–52 LOCKED |
| V5 | 53–59 | `StrategyResearchDomain` | `strategy_research` | `OFFLINE_STRATEGY_RESEARCH_ONLY` | PLANNED_LOCKED |
| V6 | 60–71 | `BacktestDomain` | `backtesting` | `BACKTEST_ONLY` | PLANNED_LOCKED |
| V7 | 72–80 | `RiskDomain` | `risk` | `RISK_SIMULATION_ONLY` | PLANNED_LOCKED |
| V8 | 81–87 | `PaperTradingDomain` | `paper_trading` | `PAPER` | PLANNED_LOCKED |
| V9 | 88–95 | `PortfolioDomain` | `portfolio` | `PORTFOLIO_ACCOUNTING` | PLANNED_LOCKED |
| V10 | 96–102 | `ResearchOSDomain` | `research_os` | `RESEARCH_GOVERNANCE_ONLY` | PLANNED_LOCKED |
| V11 | 103–110 | `IntelligenceDomain` | `intelligence` | `READ_ONLY_CONTEXT_ONLY` | PLANNED_LOCKED |
| V12 | 111–118 | `OperatorConsoleDomain` | `ui` | `OPERATOR_UI` | PLANNED_LOCKED |
| V13 | 119–125 | `ReadOnlyConnectorDomain` | `connectors` | `READ_ONLY` | PLANNED_LOCKED |
| V14 | 126–132 | `ExchangeRiskDomain` | `exchange_risk` | `EXCHANGE_HEALTH_ONLY` | PLANNED_LOCKED |
| V15 | 133–141 | `OrderExecutionDomain` | `execution` | `ORDER_MANAGEMENT_CORE` | PLANNED_LOCKED |
| V16 | 142–149 | `SandboxExecutionDomain` | `sandbox` | `SANDBOX` | PLANNED_LOCKED |
| V17 | 150–157 | `LiveGovernanceDomain` | `live_governance` | `LIVE_DISABLED_BY_DEFAULT` | PLANNED_LOCKED |
| V18 | 158–165 | `OperationsDomain` | `monitoring` | `OPERATIONS_GOVERNANCE` | PLANNED_LOCKED |
| V19 | 166–171 | `HFTResearchDomain` | `hft_research` | `HFT_RESEARCH_ONLY` | OPTIONAL_RESEARCH_LOCKED |
| V20 | 172–174 | `OptionsContextDomain` | `options` | `OPTIONS_CONTEXT_ONLY` | OPTIONAL_RESEARCH_LOCKED |
| V21 | 175–177 | `OnChainContextDomain` | `onchain` | `ONCHAIN_CONTEXT_ONLY` | OPTIONAL_RESEARCH_LOCKED |

## Capabilities transverses

- Canonical contracts, lineage, available_at/usable_from, replay et checksums.
- Veto consequence matrix et priorité KILL_SWITCH > PAUSE > BLOCK > WAIT > APPROVE.
- Strategy lifecycle et promotion gates.
- Configuration/environment governance, CI/CD, artifact registry, release et rollback.
- Ledger, portfolio/PnL, reconciliation, observability, incident response et DR.
- Domain ownership et architecture dependency tests.

## Interdictions

- Aucun LLM ne crée/approuve signal, sizing ou ordre.
- Aucune donnée inconnue/non réconciliée n’autorise une action.
- Aucune permission withdrawal.
- Aucun HFT live dans V1–V21.
- Aucun scale-up autonome.
- Lot 45 reste descriptif/offline et ne peut produire ni `Signal`, ni `RiskDecision`, ni `OrderIntent`.
- Lot 46 ne peut commencer qu’après merge du Lot 45, audit post-merge indépendant et décision explicite `GO_LOT45_POST_MERGE`.
