# Crypto Quant Bot V4.1-Ops

Plateforme quantitative crypto défensive, déterministe, extensible et auditable.

Le projet n’est pas conçu comme un simple bot « signal → ordre ». Son principe central est de prouver, avant toute action, que les données, la causalité temporelle, la stratégie, le risque, l’exécution et l’état du compte autorisent cette action. En cas d’incertitude ou d’incohérence, le comportement attendu est fail-closed.

## État courant

| Élément | État |
|---|---|
| Dernier lot fusionné et audité | **Lot 44 — Trades & Aggressor Classification Schema** |
| Version de développement | **0.45.0.dev0** |
| Version V4 | **active** |
| Lot actuellement ouvert | **Lot 45 — Order Flow, Delta & CVD Engine** |
| État Lot 45 | **candidat en certification exacte sur PR #66** |
| Lots suivants | **46–52 verrouillés** jusqu’au `GO_LOT45_POST_MERGE` |
| Runtime maximal courant | `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY` |
| Trading | **désactivé** |
| Connectivité/exécution exchange | **désactivée** |
| Levier | **FORBIDDEN** |
| Withdrawals | **FORBIDDEN** |

```text
trade_allowed = false
execution_allowed = false
approved_size = 0
live_execution = DISABLED
```

La branche `main` est actuellement le gate certifié du Lot 45, issu du `GO_LOT44_POST_MERGE`. Le candidat Lot 45 reste non exécutable et ne peut produire ni `Signal`, ni `RiskDecision`, ni `OrderIntent`.

## Ce qui est déjà construit

### V1 — Lots 0–20

Fondation défensive, contrats, audit, invariants no-trading, reproductibilité et garde-fous institutionnels.

### V2 — Lots 21–30

Analyse de marché offline et explicable : multi-timeframe 5m/15m, contexte global, couche why-not-trade, replay déterministe et clôture V2.

### V3 — Lots 31–36

Market Data Governance : registre des sources, normalisation instruments/symboles, gouvernance timestamps/timezones, data quality, réconciliation candle/trade/book, freshness/gaps/outages et clôture V3.

### V4 — Lots 37–52

Les Lots 37–44 sont fusionnés et audités :

1. Lot 37 — scope et contrats microstructure offline ;
2. Lot 38 — snapshots carnet L2 ;
3. Lot 39 — reconstruction des deltas et séquences du carnet ;
4. Lot 40 — intégrité et désynchronisation du book ;
5. Lot 41 — spread, profondeur et imbalance ;
6. Lot 42 — liquidity zones, walls et voids ;
7. Lot 43 — résilience et replenishment ;
8. Lot 44 — trades et classification de l’agresseur.

Le **Lot 45** construit l’Order Flow / Delta / CVD de manière déterministe en event-time, avec conservation BUY/SELL/UNKNOWN, `Decimal`, politique de sessions versionnée, lineage/checksums et replay. Il est encore en certification et ne constitue pas encore un lot fusionné.

Les Lots 46–52 — confidence engine, absorption/defense/hidden-liquidity proxy, volume clusters, liquidity pools, sweeps/fakeouts/traps, dérivés puis Game Theory — restent verrouillés.

## Produit cible

La chaîne canonique est :

```text
Source Registry
→ Raw Immutable / Ingestion gouvernée
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
→ OMS / EMS
→ Ack / Fill / Reconciliation
→ Portfolio / PnL
→ Monitoring / Incident / Reporting
```

Chaque transition est un contrat. Aucun domaine ne peut contourner le domaine propriétaire de la décision suivante.

## Roadmap V1 → V21

| Version | Lots | Objectif |
|---:|---:|---|
| V1 | 0–20 | Defensive Audit / No Trading |
| V2 | 21–30 | Market Analysis Offline |
| V3 | 31–36 | Market Data Governance |
| V4 | 37–52 | Microstructure / Liquidity / Game Theory |
| V5 | 53–59 | Alpha / Strategy Research |
| V6 | 60–71 | Backtesting / Expected Value / TCA |
| V7 | 72–80 | Model Risk / Sizing / Risk |
| V8 | 81–87 | Paper Trading |
| V9 | 88–95 | Portfolio / PnL Core |
| V10 | 96–102 | Research OS |
| V11 | 103–110 | News / AI / Event Context |
| V12 | 111–118 | UI / Operator Console |
| V13 | 119–125 | API / Account Read-Only |
| V14 | 126–132 | Exchange Risk / API Health |
| V15 | 133–141 | OMS / EMS Core |
| V16 | 142–149 | Sandbox / Demo Execution |
| V17 | 150–157 | Live Governance / Human Approval |
| V18 | 158–165 | Observability / Incident Response |
| V19 | 166–171 | HFT Research — research-only |
| V20 | 172–174 | Options Context |
| V21 | 175–177 | On-chain / Flow Intelligence |

Aucun HFT live n’est prévu dans V1→V21. Aucun scale-up autonome n’est autorisé.

## Invariants non négociables

- pas de donnée sans lineage et disponibilité temporelle explicite ;
- pas de lookahead ;
- pas de probabilité sans calibration ;
- pas de stratégie sans hypothèse falsifiable ;
- pas d’EV finale sans coûts/slippage/fills/capacité ;
- pas de `Signal` transformé implicitement en ordre ;
- pas d’`OrderIntent` sans `RiskDecision APPROVE` valide pour le hash exact ;
- aucun nouvel ordre si data, exchange, ledger ou reconciliation est `UNKNOWN` ;
- pas de secret réel dans Git ;
- pas de withdrawal ;
- pas de levier dans le périmètre initial ;
- aucun lot suivant avant le gate explicite du lot courant.

## Environnement canonique

```text
Python 3.11.9
timezone UTC
locale indépendante
seed/config/horloge injectées
```

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
```

## Validation courante

Pour le candidat Lot 45 :

```bash
PYTHONPATH=src python scripts/validate_lot45.py --code-commit <SOURCE_HEAD_SHA>
pytest -q
python scripts/validate_roadmap_documentation.py
python scripts/validate_architecture_boundaries.py
python scripts/validate_domain_architecture.py
python scripts/audit_roadmap_semantics.py
python scripts/validate_traceability_contract.py
python scripts/check_no_silent_numeric_coercion.py
```

La CI ajoute Ruff, mypy, couverture lignes/branches, Bandit, `pip-audit`, mutation testing et répétitions anti-flake. Les workflows Lot 45 doivent certifier explicitement le `SOURCE_HEAD_SHA` courant ; un workflow vert épinglé sur un ancien SHA ne constitue pas une preuve du nouveau candidat.

## Sources de vérité

- [Master System Specification](docs/MASTER_SYSTEM_SPECIFICATION.md)
- [Roadmap canonique V1 → V21](docs/ROADMAP_V1_TO_V21.md)
- [System Execution Architecture](docs/SYSTEM_EXECUTION_ARCHITECTURE.md)
- [Functional Coverage Registry](docs/FUNCTIONAL_COVERAGE_REGISTRY.md)
- [V4 Microstructure / Liquidity / Game Theory](docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md)
- [Lot 45 — Order Flow, Delta & CVD Engine](docs/LOT_45_ORDER_FLOW_DELTA_AND_CVD_ENGINE.md)
- [Lot 45 — Acceptance Criteria](docs/ACCEPTANCE_CRITERIA_LOT_45.md)

Pour les lots historiques, les critères d’acceptation, rapports PASS, artefacts et commits certifiés restent normatifs. Une documentation future ne réécrit jamais rétroactivement une preuve auditée.

## Contribution

Toute modification suit [CONTRIBUTING.md](CONTRIBUTING.md). Un contrat documenté ne devient pas une capability implémentée. Aucun lot ne commence sans gate explicite et preuves sur le commit exact.
