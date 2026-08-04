# Domain Boundaries and Ownership

## Ownership canonique

| Version | Owner | Package | Responsabilité |
|---:|---|---|---|
| V1 | `SafetyKernel` | `src/crypto_quant_bot/core` | Defensive Audit / No Trading |
| V2 | `MarketAnalysisDomain` | `src/crypto_quant_bot/market_analysis` | Market Analysis Offline |
| V3 | `MarketDataGovernanceDomain` | `src/crypto_quant_bot/data_governance` | Market Data Governance |
| V4 | `MicrostructureDomain` | `src/crypto_quant_bot/microstructure` | Microstructure / Liquidity / Game Theory |
| V5 | `StrategyResearchDomain` | `src/crypto_quant_bot/strategy_research` | Alpha / Strategy Research |
| V6 | `BacktestDomain` | `src/crypto_quant_bot/backtesting` | Backtesting / Expected Value / TCA |
| V7 | `RiskDomain` | `src/crypto_quant_bot/risk` | Model Risk / Sizing / Risk |
| V8 | `PaperTradingDomain` | `src/crypto_quant_bot/paper_trading` | Paper Trading |
| V9 | `PortfolioDomain` | `src/crypto_quant_bot/portfolio` | Portfolio / PnL Core |
| V10 | `ResearchOSDomain` | `src/crypto_quant_bot/research_os` | Research OS |
| V11 | `IntelligenceDomain` | `src/crypto_quant_bot/intelligence` | News / AI / Event Context |
| V12 | `OperatorConsoleDomain` | `src/crypto_quant_bot/ui` | UI / Operator Console |
| V13 | `ReadOnlyConnectorDomain` | `src/crypto_quant_bot/connectors` | API Read-Only / Account Read-Only |
| V14 | `ExchangeRiskDomain` | `src/crypto_quant_bot/exchange_risk` | Exchange Risk / API Health |
| V15 | `OrderExecutionDomain` | `src/crypto_quant_bot/execution` | OMS / EMS Core |
| V16 | `SandboxExecutionDomain` | `src/crypto_quant_bot/sandbox` | Sandbox / Demo Execution |
| V17 | `LiveGovernanceDomain` | `src/crypto_quant_bot/live_governance` | Live Governance / Human Approval |
| V18 | `OperationsDomain` | `src/crypto_quant_bot/monitoring` | Observability / Incident Response |
| V19 | `HFTResearchDomain` | `src/crypto_quant_bot/hft_research` | HFT Research |
| V20 | `OptionsContextDomain` | `src/crypto_quant_bot/options` | Options Context |
| V21 | `OnChainContextDomain` | `src/crypto_quant_bot/onchain` | On-chain / Flow Intelligence |

## Règles de dépendance

- `contracts` ne dépend d’aucun domaine métier.
- `data_governance` peut être consommé par tous, mais ne consomme ni strategy, ni risk, ni execution.
- `market_analysis` et `microstructure` ne dépendent jamais de `execution`.
- `strategy_research` peut consommer analysis/scenarios, pas portfolio live ni secrets.
- `risk` peut consommer tous les états read-only nécessaires ; aucun domaine ne peut contourner son résultat.
- `execution` ne reçoit que des `OrderIntentV1` approuvés.
- `portfolio` consomme execution events ; il ne fait aucun submit.
- `ui` ne contient aucune logique d’autorisation.
- `intelligence`, `options`, `onchain`, `hft_research` restent contextuels/research selon leur mode.

## API publique d’un domaine

Chaque domaine expose uniquement : modèles de contrats, fonctions/services publics, reason codes, health state et validators. Les imports vers `_internal`, repositories privés ou tables internes d’un autre domaine sont interdits par test d’architecture.
