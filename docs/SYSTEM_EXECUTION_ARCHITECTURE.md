# System Execution Architecture

## 1. Responsabilités de bout en bout

| Étape | Owner | Entrée | Sortie | Interdiction |
|---|---|---|---|---|
| Data governance | MarketDataGovernanceDomain | raw/source metadata | validated market envelopes | ne produit pas de signal |
| Market analysis | MarketAnalysisDomain | validated OHLCVT/features | market context | ne produit pas de direction exécutable |
| Microstructure | MicrostructureDomain | L2/trades/derivatives context | scenarios/inferences | ne prétend pas connaître les intentions réelles |
| Strategy research | StrategyResearchDomain | scenarios/features | hypothesis/candidate/signal | ne choisit ni venue ni taille finale |
| Backtest/TCA | BacktestDomain | candidate + historical data | evidence/EV/robustness | ne donne pas d’autorisation live |
| Risk | RiskDomain | intent + state + limits | sizing/risk decision | seul owner d’APPROVE/WAIT/BLOCK/PAUSE/KILL |
| OMS | OrderExecutionDomain | approved OrderIntent | durable order state | ne modifie pas la stratégie |
| EMS/adapter | OrderExecutionDomain | validated OMS order | submit/ack/fill events | ne bypass pas OMS/risk |
| Portfolio/PnL | PortfolioDomain | fills/cashflows/marks | positions/PnL/exposure | ne crée pas d’ordres |
| Operations | OperationsDomain | telemetry/all states | alerts/incidents/recovery | ne réactive pas une stratégie sans gate |

## 2. Séquence paper

1. Scheduler fixe `simulated_now` et charge configuration/version.
2. Data quality valide le snapshot.
3. Analysis/scenario calculent des états disponibles à `simulated_now`.
4. Strategy produit Signal puis TradeIntent.
5. Risk retourne WAIT/BLOCK ou APPROVE avec size borné.
6. OrderIntent paper est créé pour le hash approuvé.
7. Simulateur paper produit ack/fill selon modèles TCA.
8. Ledger, portfolio et PnL consomment les events.
9. Reconciliation vérifie l’identité comptable.
10. Monitoring écrit métriques et incident si divergence.

## 3. Séquence sandbox/live gouverné

```text
Signal
→ TradeIntent
→ RiskDecision(APPROVE)
→ HumanApproval (live seulement)
→ OrderIntent
→ OMS durable/idempotent
→ validation instrument/exchange/runtime
→ EMS adapter
→ venue ack/reject/fill
→ OMS transitions
→ ledger/portfolio/PnL
→ reconciliation
```

Tout timeout de soumission produit `UNKNOWN_SUBMIT_OUTCOME` puis reconciliation ; jamais un retry aveugle.

## 4. Priorité des décisions système

```text
KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE
```

Aucun score moyen ne peut neutraliser un veto critique.
