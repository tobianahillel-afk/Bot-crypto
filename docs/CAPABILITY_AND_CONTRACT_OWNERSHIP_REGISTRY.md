# Capability and Contract Ownership Registry

Statut : `P0_6_NORMATIVE`  
Registre exécutable : `config/governance/domain_ownership_registry_v1.json`.

## Principe

Chaque capability métier et chaque contrat critique possède un propriétaire canonique unique. Les autres domaines peuvent consommer un contrat public autorisé, mais ne peuvent ni le redéfinir, ni en devenir copropriétaires, ni réimplémenter silencieusement sa logique.

```text
one capability = one canonical owner
one critical contract = one canonical producer domain
cross-domain access = public contracts only
```

## Propriétaires V1–V21

| Version | Owner | Package | Responsabilité exclusive principale |
|---:|---|---|---|
| V1 | SafetyKernel | `core` | sécurité défensive et audit initial |
| V2 | MarketAnalysisDomain | `market_analysis` | contexte de barres et alignement multi-échelle descriptif |
| V3 | MarketDataGovernanceDomain | `data_governance` | sources, instruments, temps canonique, qualité et flux data |
| V4 | MicrostructureDomain | `microstructure` | carnet, order flow, liquidité, participants et Game Theory |
| V5 | StrategyResearchDomain | `strategy_research` | hypothèses alpha, forecasts, scénarios, signaux et TradeIntent |
| V6 | BacktestDomain | `backtesting` | labels offline, backtest, coûts, fills, EV et OOS |
| V7 | RiskDomain | `risk` | model risk, limites, sizing, RiskDecision et politique kill |
| V8 | PaperTradingDomain | `paper_trading` | runtime, ordres, fills et réconciliation paper |
| V9 | PortfolioDomain | `portfolio` | cash, positions, comptabilité, PnL et réconciliation portfolio |
| V10 | ResearchOSDomain | `research_os` | expériences, artefacts et releases de recherche |
| V11 | IntelligenceDomain | `intelligence` | événements, news, sentiment et explication contextuelle |
| V12 | OperatorConsoleDomain | `ui` | read models et actions opérateur auditées |
| V13 | ReadOnlyConnectorDomain | `connectors` | exchange/account read-only et permission scan |
| V14 | ExchangeRiskDomain | `exchange_risk` | santé exchange, rate limits et vetos venue |
| V15 | OrderExecutionDomain | `execution` | validation OrderIntent, OMS/EMS, protections et réconciliation ordre |
| V16 | SandboxExecutionDomain | `sandbox` | adapters sandbox, routing et drills d'incident |
| V17 | LiveGovernanceDomain | `live_governance` | approbation humaine, éligibilité live, pause et emergency stop |
| V18 | OperationsDomain | `monitoring` | télémétrie, alertes, incidents, DR et release readiness |
| V19 | HFTResearchDomain | `hft_research` | simulations queue/matching et faisabilité HFT research-only |
| V20 | OptionsContextDomain | `options` | IV, skew, greeks et contexte options |
| V21 | OnChainContextDomain | `onchain` | sources et contexte de flux on-chain |

## Règles de production et consommation

- V3 produit `InstrumentRegistryV1`, `InstrumentSpecificationV1`, temps et qualité canoniques. Portfolio, exchange risk, options et exécution les consomment sans les normaliser à nouveau.
- V4 produit les états de book, microstructure, dérivés et participants. V6 les consomme pour les coûts et fills sans recalculer la microstructure.
- V5 produit forecast, scenario, signal et `TradeIntentV1`. Aucun domaine contextuel ne crée directement ces contrats.
- V7 est l'unique producteur de `RiskDecisionV1` et de la taille approuvée.
- V15 est l'unique propriétaire de la soumission et du lifecycle d'ordre. Portfolio ne soumet jamais.
- V11, V19, V20 et V21 restent contextuels ou research-only et ne peuvent autoriser un trade seuls.
- V12 n'implémente aucune autorisation côté interface.

## Frontières privées

Les imports vers `_internal`, repositories privés, tables internes ou helpers non publics d'un autre domaine sont interdits. Un nouveau besoin transverse exige un contrat public versionné ou un changement explicite du registre.

## Modification du registre

Toute modification exige :

1. justification architecturale ;
2. absence de collision de capability ;
3. migration des consommateurs ;
4. mise à jour de la roadmap et des contrats ;
5. tests d'architecture ;
6. replay/non-régression ;
7. revue humaine.

Une modification documentaire seule ne change pas le propriétaire effectif.

## Gate

Les scripts suivants sont normatifs :

```text
scripts/validate_domain_architecture.py
scripts/audit_roadmap_semantics.py
```

Toute collision, dépendance interdite, import privé ou production d'un contrat critique par le mauvais domaine donne :

```text
NO_GO_DOMAIN_OWNERSHIP
```
