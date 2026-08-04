# V2 Lot 26 — Normative readiness addendum

Ce document complète et, en cas d'ambiguïté, prévaut sur la section Lot 26 de `V02_MARKET_ANALYSIS_OFFLINE.md`.

## 1. Clarification centrale

Le flux peut être continu, mais le Lot 26 consomme uniquement des snapshots confirmés issus de barres fermées. Le timeframe n'est pas une limitation de l'ingestion : il est une vue agrégée avec cadence et disponibilité propres.

Le profil v1 est :

```text
timebar-5m = contexte local, mise à jour fréquente
timebar-15m = contexte supérieur, mise à jour plus lente
relation = timebar-5m → timebar-15m
join = ASOF_BACKWARD
```

Le même 15m peut contextualiser plusieurs 5m. Une divergence est informative et ne crée aucun veto automatique.

## 2. Extensibilité obligatoire

Le Lot 26 doit implémenter une interface de relation entre échelles, et non une fonction métier dupliquée et codée en dur pour chaque paire.

Les autres échelles — event stream, 1m, 1h, volume/tick/imbalance bars — sont enregistrées mais désactivées. Leur activation nécessite une nouvelle version, une justification et un gate.

Aucun vote majoritaire entre timeframes n'est autorisé.

## 3. Séparation des temps

```text
data_resolution ≠ feature_lookback
forecast_horizon ≠ decision_clock
signal_ttl ≠ holding_horizon
```

Le Lot 26 ne déduit aucun horizon de prévision ou de détention du timeframe 5m/15m.

## 4. Documents normatifs

### Lot 26

- `docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_26.md`
- `docs/LOT26_REQUIREMENT_TEST_MATRIX.md`
- `docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md`
- `docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md`
- `docs/contracts/LOT26_TEMPORAL_CONTRACTS.md`
- `config/math/multi_timeframe_alignment_v1.json`
- `config/temporal/temporal_scale_registry_v1.json`
- `config/temporal/decision_clock_policy_v1.json`

### Architecture future verrouillée

- `docs/TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md`
- `docs/STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md`
- `docs/PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md`
- `docs/PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md`
- `docs/roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md`
- `config/research/forecast_horizon_registry_v1.json`

## 5. Frontières

### Lot 26

- alignement descriptif ;
- relation v1 5m→15m ;
- barres fermées ;
- `CLOSED_LOCAL_BAR` comme seul trigger ;
- aucune prévision, probability, participant, zone ou ordre.

### V3

Flux continu canonique, temps, qualité, révisions et réconciliation.

### V4

Carnet, trades, order flow, état continu, participants, Game Theory, stop/take-profit/break-even/liquidation zones.

### V5/V6

Prévisions stochastiques multi-horizons, calibration, OOS, coûts et capacité.

### V7/V15

Risque, sizing, ExitPolicy et ProtectiveOrderPlan/OMS.

## 6. Gate

Le Lot 26 reste `PLANNED_LOCKED` jusqu'au rapport pré-Lot26 `GO`, à une CI verte sur le commit exact et à une activation humaine explicite.
