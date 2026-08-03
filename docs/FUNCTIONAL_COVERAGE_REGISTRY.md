# Functional Coverage Registry — V1 à V21

Ce registre remplace le registre fonctionnel V2+ limité à V11 comme vue canonique des capabilities futures.

## Statuts

- `DONE_VALIDATED` : implémenté et validé.
- `ACTIVE_PARTIAL` : version ouverte et partiellement implémentée.
- `PLANNED_LOCKED` : planifié mais non activé.
- `OPTIONAL_RESEARCH` : extension optionnelle de recherche.

## Couverture par version

| Version | Capabilities principales | Lots | Statut |
|---:|---|---:|---|
| V1 | bootstrap, data foundation, pivots, volume/VWAP, volatility, regime, market state, anti-lookahead, replay, cost V0, risk firewalls, lineage, health, compliance, closure | 0–20 | DONE_VALIDATED |
| V2 | market analysis, indicators, trend/range/momentum, volatility/regime/confluence, MTF alignment, aggregation, explanation, replay | 21–30 | ACTIVE_PARTIAL |
| V3 | source registry, instrument normalization, clock policy, data quality, reconciliation, freshness/outages | 31–36 | PLANNED_LOCKED |
| V4 | L2/L3 offline, book reconstruction, order flow/CVD, liquidity, absorption, stops, fakeouts, derivatives, game theory/scenarios | 37–52 | PLANNED_LOCKED |
| V5 | alpha registry, strategy candidates, signal schema, trade/order intents, horizon, invalidation, retirement, promotion | 53–59 | PLANNED_LOCKED |
| V6 | labels, replay, fees/funding/spread, slippage/impact, fills/capacity, EV, walk-forward, OOS, purged CV, placebo, Monte Carlo | 60–71 | PLANNED_LOCKED |
| V7 | model cards, drift, limits, sizing, drawdown, tail risk, portfolio pre-checks, risk approval, kill switch | 72–80 | PLANNED_LOCKED |
| V8 | paper runtime, simulated orders/fills, paper ledger, reconciliation, incident handling, promotion | 81–87 | PLANNED_LOCKED |
| V9 | portfolio state, cash/collateral, positions, unified PnL, attribution, exposure, statements | 88–95 | PLANNED_LOCKED |
| V10 | experiment registry, versioning, hypothesis lifecycle, ablations, knowledge base, governance | 96–102 | PLANNED_LOCKED |
| V11 | news/events read-only, calendar, sentiment, event risk, source audit, LLM explanation | 103–110 | PLANNED_LOCKED |
| V12 | market/microstructure/scenario dashboards, risk command center, operator console, UI security | 111–118 | PLANNED_LOCKED |
| V13 | read-only connector, account snapshots, histories, reconciliation, permission scanner | 119–125 | PLANNED_LOCKED |
| V14 | API/WS health, availability, staleness, rate limits, maintenance, counterparty risk | 126–132 | PLANNED_LOCKED |
| V15 | OMS/EMS contracts, order state machine, idempotency, validation, rejects, partial fills, cancel/replace, recovery | 133–141 | PLANNED_LOCKED |
| V16 | sandbox adapter, routing, fill/latency simulation, risk, failure injection, reconciliation | 142–149 | PLANNED_LOCKED |
| V17 | runtime modes, secrets, human approval, small capital, live risk, override, compliance | 150–157 | PLANNED_LOCKED |
| V18 | logs/metrics/traces, heartbeats, monitoring, alerting, incidents, DR, readiness | 158–165 | PLANNED_LOCKED |
| V19 | tick/L2/L3, matching engine, queue model, latency, market making, adverse selection | 166–171 | OPTIONAL_RESEARCH |
| V20 | options contracts, IV, skew, term structure, expiry, Greeks | 172–174 | OPTIONAL_RESEARCH |
| V21 | on-chain sources, exchange/stablecoin/miner/whale flows, market fusion | 175–177 | OPTIONAL_RESEARCH |

## Gates transverses

- `data_quality_gate` avant toute analyse avancée.
- `research_promotion_gate` avant backtest.
- `backtest_promotion_gate` avant paper.
- `risk_approval_gate` avant tout order intent.
- `paper_promotion_gate` avant sandbox.
- `sandbox_promotion_gate` avant live eligibility.
- `human_approval_gate` avant toute soumission live.
- `emergency_stop_gate` prioritaire sur tous les autres états.

## Interdictions

- Aucun LLM ne crée ou approuve un signal, un sizing ou un ordre.
- Aucune donnée inconnue ou non réconciliée n’autorise une action.
- Aucune permission withdrawal.
- Aucun HFT live dans la roadmap V1–V21.
