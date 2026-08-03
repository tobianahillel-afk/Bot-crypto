# Roadmap canonique V1 → V21 — Lots 0 à 177

Projet : **Crypto Quant Bot V3.1-Ops**

Ce document remplace la roadmap prévisionnelle limitée à V11 / Lot 147 comme source de vérité pour les travaux futurs.
Les documents historiques restent conservés pour audit, mais toute nouvelle implémentation doit suivre cette roadmap canonique.

## État actuel

- Dernier lot implémenté et validé : **Lot 25 — Volatility / Regime / Confluence Engine**.
- Prochain lot : **Lot 26 — Multi-Timeframe Alignment Engine**.
- Lots `0–25` : implémentés/validés selon les rapports existants.
- Lots `26–177` : planifiés et verrouillés jusqu’à activation explicite.
- Les correctifs historiques `bis/ter/quater/...` restent des correctifs d’audit et ne sont pas comptés comme lots principaux.

## Principes non négociables

```text
Analyse ≠ signal
Signal ≠ trade intent
Trade intent ≠ order intent
Order intent ≠ ordre soumis
Ordre ≠ position
Position ≠ stratégie validée
Stratégie validée ≠ autorisation live
```

- Tout module est fail-closed.
- Aucun score descriptif ne devient implicitement un signal.
- Aucun signal ne devient ordre sans risk approval.
- Aucun live sans promotion paper → sandbox → live et revue humaine.
- HFT reste research/simulation dans cette roadmap.
- Options et on-chain sont des extensions contextuelles, non bloquantes pour le cœur du produit.

## Versions et plages de lots

| Version | Phase | Lots | Statut global |
|---:|---|---:|---|
| V1 | Defensive Audit / No Trading | 0–20 | CLOSED |
| V2 | Market Analysis Offline | 21–30 | ACTIVE / PARTIAL |
| V3 | Market Data Governance | 31–36 | PLANNED_LOCKED |
| V4 | Microstructure / Liquidity / Game Theory | 37–52 | PLANNED_LOCKED |
| V5 | Alpha / Strategy Research | 53–59 | PLANNED_LOCKED |
| V6 | Backtesting / Expected Value / TCA | 60–71 | PLANNED_LOCKED |
| V7 | Model Risk / Sizing / Risk | 72–80 | PLANNED_LOCKED |
| V8 | Paper Trading | 81–87 | PLANNED_LOCKED |
| V9 | Portfolio / PnL Core | 88–95 | PLANNED_LOCKED |
| V10 | Research OS | 96–102 | PLANNED_LOCKED |
| V11 | News / AI / Event Context | 103–110 | PLANNED_LOCKED |
| V12 | UI / Operator Console | 111–118 | PLANNED_LOCKED |
| V13 | API Read-Only / Account Read-Only | 119–125 | PLANNED_LOCKED |
| V14 | Exchange Risk / API Health | 126–132 | PLANNED_LOCKED |
| V15 | OMS / EMS Core | 133–141 | PLANNED_LOCKED |
| V16 | Sandbox / Demo Execution | 142–149 | PLANNED_LOCKED |
| V17 | Live Governance / Human Approval | 150–157 | PLANNED_LOCKED |
| V18 | Observability / Incident Response | 158–165 | PLANNED_LOCKED |
| V19 | HFT Research | 166–171 | PLANNED_LOCKED |
| V20 | Options Context | 172–174 | PLANNED_LOCKED |
| V21 | On-chain / Flow Intelligence | 175–177 | PLANNED_LOCKED |

## Documents détaillés par version

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

## Registres associés

- `data/audit/product_scope_roadmap_lot21.jsonl` : registre machine-readable détaillé des Lots 0 à 177.
- `docs/FUNCTIONAL_COVERAGE_REGISTRY.md` : couverture des capabilities et gates par version.
- `docs/ROADMAP_MIGRATION_AND_GOVERNANCE.md` : règles de migration depuis l’ancienne roadmap.
- `docs/LOT_SPECIFICATION_STANDARD.md` : structure obligatoire des futurs lots.

## Règles de modification

1. Ne jamais renuméroter un lot déjà implémenté.
2. Toute modification de scope doit mettre à jour simultanément le document de version, le registre JSONL et le registre fonctionnel.
3. Tout lot activé doit obtenir un document d’acceptation dédié et un rapport PASS.
4. Les versions optionnelles V19–V21 ne peuvent pas contourner les gates des versions V6–V18.
