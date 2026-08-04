# Crypto Quant Bot V3.1-Ops

Plateforme quantitative crypto défensive, déterministe, extensible et auditable.

## État courant

| Élément | État |
|---|---|
| Dernier lot implémenté et validé | **Lot 25 — Volatility / Regime / Confluence** |
| Baseline qualité | **P0 institutionnel fusionné** |
| Prochaine implémentation autorisée | **Lot 26 — Multi-Timeframe Alignment**, encore verrouillé |
| Runtime maximal | `LOCAL_OFFLINE_ANALYSIS_ONLY` |
| Trading | **désactivé** |
| Connectivité exchange | **désactivée** |

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
execution_allowed = false
approved_size = 0
live_execution = DISABLED
leverage = FORBIDDEN
withdrawals = FORBIDDEN
```

## Vision temporelle

Le système cible un flux de marché canonique unique et continu, plusieurs représentations temporelles et plusieurs horizons prédictifs. Il ne crée pas un robot indépendant par timeframe.

Six notions restent séparées :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Le profil initial du Lot 26 est :

```text
flux continu amont
→ états confirmés de barres fermées
→ timebar-5m comme contexte local
→ timebar-15m comme contexte supérieur
→ ASOF_BACKWARD avec available_at <= decision_time
→ alignement descriptif et auditable
```

Le 5m/15m est une première configuration, pas une limitation du futur système. Le registre temporel prévoit une interface extensible, tandis que les échelles supplémentaires restent désactivées dans le Lot 26.

Le 15m n'oppose aucun veto automatique au 5m. Une divergence peut représenter un rebond local dans une structure supérieure différente. Le vote majoritaire naïf entre timeframes est interdit.

## Flux continu et données confirmées

Une barre ouverte peut être observée comme état provisoire, mais elle ne peut pas être consommée comme état confirmé. Les futurs états événementiels de carnet, trades, liquidations et order flow appartiennent à V3/V4 ; ils ne sont pas simulés dans le Lot 26.

## Prévision et modèles stochastiques

La roadmap prévoit des prévisions par horizons distincts — initialement 30s, 5m, 15m et 1h — avec distributions, quantiles, volatilité, target/stop hit, MAE/MFE, temps avant événement et incertitude.

Ces contrats sont `PLANNED_LOCKED_NOT_IMPLEMENTED`. Le Lot 26 ne produit aucune prediction, probability, expected return ou direction BUY/SELL.

Les futurs modèles stochastiques devront être sélectionnés par preuve, comparés à des baselines et validés hors échantillon. La sophistication d'un modèle n'est pas une preuve d'alpha.

## Carnet, participants et Game Theory

V4 — Lots 37–52 possède :

- carnet L2/L3, deltas, santé et séquences ;
- spread, profondeur, imbalance, murs et vides ;
- résilience, replenishment, absorption et liquidité cachée proxy ;
- aggressor classification, order flow, delta et CVD ;
- volume clusters, time-at-level, sweeps, fakeouts et traps ;
- OI, funding, basis et liquidations ;
- Game Theory et scénarios concurrents.

Les zones futures sont explicitement typées :

```text
STOP_LOSS_CLUSTER
TAKE_PROFIT_CLUSTER
BREAK_EVEN_CLUSTER
LIQUIDATION_CLUSTER
ENTRY_CONGESTION_ZONE
TRAPPED_POSITION_ZONE
FORCED_EXIT_ZONE
PASSIVE_DEFENSE_ZONE
```

Elles restent des inférences probabilistes, jamais des ordres privés prétendument observés.

## Décision, risque et exécution future

```text
forecast
→ scenario
→ signal
→ TradeIntent
→ RiskDecision
→ OrderIntent
→ OMS/EMS
→ fill/reconciliation
```

Les futurs ordres protecteurs — stop-loss, take-profit, break-even, trailing, partial exits, bracket et OCO — sont spécifiés mais non implémentés. Ils appartiennent à V5/V7/V8/V15 selon leurs responsabilités.

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

## Validation

```bash
python scripts/validate_pre_lot26_readiness.py --write-report
python scripts/validate_roadmap_documentation.py
python scripts/validate_architecture_boundaries.py
python scripts/check_no_silent_numeric_coercion.py
pytest -q
```

La CI ajoute Ruff, mypy, coverage lignes/branches, diff coverage, Bandit, `pip-audit`, complexité et mutation testing.

## Sources de vérité

### Lot 26

- [Gate pré-Lot26](docs/PRE_LOT26_ENTRY_GATE.md)
- [Spécification Lot 26](docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [Critères d'acceptation](docs/ACCEPTANCE_CRITERIA_LOT_26.md)
- [Mathématiques](docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md)
- [ADR temporel](docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md)
- [Contrats temporels](docs/contracts/LOT26_TEMPORAL_CONTRACTS.md)

### Architecture future verrouillée

- [Architecture multi-échelle et horloges](docs/TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md)
- [Standard stochastique et multi-horizon](docs/STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md)
- [Participants et zones de sortie](docs/PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md)
- [Ordres protecteurs](docs/PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md)
- [Addendum de roadmap](docs/roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md)
- [Roadmap V1 → V21](docs/ROADMAP_V1_TO_V21.md)

## Contribution

Toute modification suit [CONTRIBUTING.md](CONTRIBUTING.md). Aucun lot ne commence sans rapport `GO` sur le commit exact. Un contrat futur documenté ne devient pas une capability implémentée.
