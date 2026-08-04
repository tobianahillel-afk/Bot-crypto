# System Execution Architecture

## 1. Responsabilités de bout en bout

| Étape | Owner | Entrée | Sortie | Interdiction |
|---|---|---|---|---|
| Data governance | MarketDataGovernanceDomain | raw/source metadata/events | canonical validated stream | ne produit pas de signal |
| Temporal projection | MarketDataGovernanceDomain | canonical stream | closed bars / registered scales | ne prédit pas |
| Market analysis | MarketAnalysisDomain | validated OHLCVT/features | descriptive market contexts | ne produit pas de direction exécutable |
| Multi-scale alignment | MarketAnalysisDomain | confirmed scale states | alignment/divergence by scale edge | ne produit pas de forecast |
| Continuous state | MicrostructureDomain avec gouvernance V3 | trades/book/derivatives events | `ContinuousMarketStateV1` | ne prétend pas connaître les intentions réelles |
| Microstructure / Game Theory | MicrostructureDomain | continuous state + scale contexts | scenarios, participant/zone inferences | ne produit pas de signal exécutable |
| Forecasting / strategy research | StrategyResearchDomain | scenarios/features/states | multi-horizon forecasts, hypotheses, candidates, signals | ne choisit ni venue ni taille finale |
| Backtest/TCA | BacktestDomain | candidate + historical event stream | evidence, calibration, EV, capacity | ne donne pas d'autorisation live |
| Risk | RiskDomain | intent + state + limits | sizing/risk decision | seul owner d'APPROVE/WAIT/BLOCK/PAUSE/KILL |
| OMS | OrderExecutionDomain | approved OrderIntent | durable order/protective-plan state | ne modifie pas la stratégie |
| EMS/adapter | OrderExecutionDomain | validated OMS order | submit/ack/fill events | ne bypass pas OMS/risk |
| Portfolio/PnL | PortfolioDomain | fills/cashflows/marks | positions/PnL/exposure | ne crée pas d'ordres |
| Operations | OperationsDomain | telemetry/all states | alerts/incidents/recovery | ne réactive pas une stratégie sans gate |

## 2. Chaîne quantitative canonique

```text
Canonical continuous event stream
→ data quality / time / source governance
→ ContinuousMarketStateV1 (V3/V4, planned)
→ registered temporal projections
→ confirmed scale states
→ scale-edge alignment (Lot26: 5m→15m)
→ microstructure and participant scenarios
→ MultiHorizonForecastV1
→ AlphaHypothesis / StrategyCandidate
→ calibrated Signal
→ TradeIntent
→ RiskDecision
→ OrderIntent
→ OMS / ProtectiveOrderPlan
→ EMS / venue events
→ ledger / portfolio / PnL
→ reconciliation / monitoring
```

À chaque étape, `available_at <= decision_time` et lineage complet sont obligatoires.

## 3. Dimensions temporelles

La chaîne ne confond jamais :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Une stratégie choisit explicitement son mandat/horizon. Les prévisions de plusieurs horizons ne sont pas agrégées par vote majoritaire.

## 4. Decision clocks

Le système cible plusieurs triggers versionnés : clôture de barre, événement marché, changement de carnet, sweep de liquidité, changement de régime, mise à jour de forecast ou événement risque.

Le Lot 26 active uniquement `CLOSED_LOCAL_BAR`. Les autres triggers restent désactivés jusqu'aux lots propriétaires.

## 5. Séquence paper future

1. Scheduler/event loop fixe `simulated_now` et charge configuration/version.
2. Data quality valide les événements disponibles.
3. Continuous state et projections temporelles sont mis à jour sans accès futur.
4. Analysis/microstructure calculent contextes et scénarios.
5. Forecasting produit des distributions par horizon si modèles calibrés.
6. Strategy produit Signal puis TradeIntent pour un horizon explicite.
7. Risk retourne WAIT/BLOCK ou APPROVE avec taille bornée.
8. OrderIntent et ProtectiveOrderPlan paper sont créés pour le hash approuvé.
9. Simulateur produit ack/partial/no-fill/fees/slippage/expiry.
10. Ledger, portfolio et PnL consomment les events.
11. Reconciliation vérifie les identités comptables et quantités protégées.
12. Monitoring produit métriques et incident si divergence.

## 6. Séquence sandbox/live gouverné

```text
Signal
→ TradeIntent
→ RiskDecision(APPROVE)
→ HumanApproval (live seulement)
→ OrderIntent + ProtectiveOrderPlan
→ OMS durable/idempotent
→ validation instrument/exchange/runtime
→ EMS adapter
→ venue ack/reject/partial fill/fill/cancel
→ OMS transitions et OCO/bracket lifecycle
→ ledger/portfolio/PnL
→ reconciliation
```

Tout timeout de soumission produit `UNKNOWN_SUBMIT_OUTCOME` puis reconciliation ; jamais un retry aveugle.

## 7. Priorité des décisions système

```text
KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE
```

Aucun score, forecast ou vote entre horizons ne neutralise un veto critique.

## 8. État actuel

Lots 0–25 implémentent uniquement une fondation offline descriptive. Lot 26, continuous state, order book, forecasting, participant inference, risk approval, protective orders et execution restent non implémentés jusqu'à leurs gates respectifs.
