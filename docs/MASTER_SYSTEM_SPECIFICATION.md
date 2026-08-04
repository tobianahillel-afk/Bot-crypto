# Master System Specification — Crypto Quant Bot V3.1-Ops

Ce document réintègre les contrats fondateurs historiques dans la roadmap canonique V1→V21. Il est normatif avec `ROADMAP_V1_TO_V21.md`, les contrats canoniques et les documents de version.

## 1. Philosophie centrale

Le système ne cherche pas d’abord à trader. Il cherche d’abord à prouver que les données, la stratégie, le risque, l’exécution et l’état du compte autorisent une action.

```text
trade_allowed = false par défaut
approved_size = 0 par défaut
runtime_mode = LIVE_DISABLED par défaut
```

```text
NO_DATA              → WAIT / BLOCK_ANALYSIS
BAD_DATA             → BLOCK_TRADING
UNCERTAIN_SCENARIO   → WAIT
UNPROMOTED_STRATEGY  → WAIT
UNCALIBRATED_MODEL   → WAIT
NEGATIVE_NET_EV      → WAIT
BAD_BOOK_HEALTH      → WAIT / BLOCK_TRADING
RISK_VETO            → WAIT / BLOCK_TRADING
SECURITY_ALERT       → PAUSE / KILL_SWITCH
RECONCILIATION_ERROR → PAUSE / KILL_SWITCH
INCIDENT_UNRESOLVED  → BLOCK_TRADING
```

## 2. Périmètre initial préservé

```text
Marché initial         : crypto spot
Paire initiale         : BTC/EUR
Venue de référence     : Kraken
Données initiales      : OHLCVT ; L2/trades seulement après lots dédiés
Capital réel initial   : aucun
Mode initial           : offline puis paper
Levier                 : FORBIDDEN
Withdrawals            : FORBIDDEN
Futures/perpetuals     : contexte/research avant toute éligibilité d’exécution
Live                   : DISABLED jusqu’aux gates V16–V18 et approbation humaine
```

Les extensions perp/futures/options/on-chain ne changent jamais rétroactivement ce périmètre initial. Elles ont leurs propres contrats et permissions.

## 3. Chaîne fonctionnelle canonique

```text
Source Registry
→ Ingestion / Raw Immutable
→ Normalisation instrument + temps
→ Data Quality Gate
→ Dataset / Feature Registry
→ Market Analysis
→ Microstructure / Scenario
→ Alpha Hypothesis
→ Strategy Candidate
→ Backtest + TCA + OOS
→ Model Risk / Sizing
→ Signal
→ Trade Intent
→ Risk Approval
→ Order Intent
→ OMS
→ EMS / Adapter autorisé
→ Ack / Fill / Reconciliation
→ Portfolio / PnL
→ Monitoring / Incident / Reporting
```

Chaque flèche est un contrat. Aucun composant ne lit directement les structures internes du composant précédent.

## 4. Identifiants obligatoires de toute décision

Toute décision ou action dérivée doit contenir :

```text
data_snapshot_id
feature_set_id
market_context_id
scenario_set_id
strategy_id + strategy_version
signal_id (si applicable)
trade_intent_id (si applicable)
risk_state_id + risk_decision_id
order_intent_id (si applicable)
config_version
model_versions
code_commit
replay_id
run_id / correlation_id
```

Une décision sans ces références n’est ni rejouable ni consommable.

## 5. Core obligatoire et extensions

### Core avant toute éligibilité live

Data governance, contracts, anti-lookahead, market context, strategy lifecycle, backtest/TCA, model risk, sizing, risk approval, paper, portfolio/PnL, read-only account, exchange risk, OMS/EMS, sandbox, live governance, reconciliation, observability, incident response, CI/release/rollback.

### Extensions optionnelles

HFT research, options context et on-chain context. Elles ne peuvent contourner les gates du core et ne sont pas requises pour le premier produit spot BTC/EUR.

## 6. Règles non négociables

- Pas de donnée sans lineage ni `available_at`.
- Pas de feature sans registry et disponibilité temporelle.
- Pas de probabilité sans calibration.
- Pas de stratégie sans hypothèse falsifiable et baselines.
- Pas d’EV finale sans coûts, slippage, fills et capacité.
- Pas de Signal transformé implicitement en OrderIntent.
- Pas d’OrderIntent sans RiskDecision APPROVE valide pour le hash exact.
- Pas de nouvel ordre si data, exchange, ledger ou reconciliation est UNKNOWN.
- Pas de secret dans Git, pas de permission withdrawal, pas de levier dans le périmètre initial.
- Pas de HFT live dans V1→V21.
- Pas de scale-up autonome.
