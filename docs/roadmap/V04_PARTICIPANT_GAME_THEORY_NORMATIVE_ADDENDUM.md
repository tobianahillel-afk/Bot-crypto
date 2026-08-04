# V4 Normative Addendum — Participant Inference, Game Theory and Exit Zones

Ce document complète V4 Lots 37–52 et prévaut sur toute formulation moins précise.

## Objective

Transformer des événements L2/L3/trades/dérivés en faits microstructure, puis en scénarios concurrents sur les réactions probables de catégories de participants. Toute intention reste inférée et explicitement étiquetée.

## Lot mapping

- Lots 37–40 : contrats, snapshot, deltas, synchronisation et santé du carnet ;
- Lots 41–43 : spread, profondeur, imbalance, zones, murs, vides, résilience et replenishment ;
- Lots 44–46 : trades, aggressor, order flow, delta/CVD et confiance de classification ;
- Lots 47–48 : absorption, défense, hidden-liquidity proxy, volume clusters et time-at-level ;
- Lot 49 : toutes les `LiquidityExitZoneV1`, pas uniquement les stops ;
- Lot 50 : sweeps, fakeouts, traps, failed auctions et transitions de scénarios ;
- Lot 51 : OI, funding, basis, crowding, squeeze et liquidations ;
- Lot 52 : modèle participant/action/constraint/payoff/belief/best-response et agrégation de scénarios.

## Lot 49 required zone types

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

Chaque zone porte horizon, méthode, preuves, contre-preuves, disponibilité, incertitude et invalidation.

## Lot 52 game-theory contract

Le lot doit produire des `ParticipantBehaviorScenarioV1` contenant :

```text
participant_class
information_set
constraints
action_set
payoff_proxy
loss_or_pain_proxy
belief_state
best_response_candidates
bounded_rationality_assumptions
forecast_horizon
invalidation_conditions
```

Un modèle d'équilibre n'est utilisé que si ses hypothèses sont documentées et testées. Des scénarios simples et baselines comportementales restent obligatoires.

## Multi-horizon behavior

Les market makers, traders momentum, détenteurs intraday et liquidateurs forcés peuvent agir sur des horizons différents. V4 conserve les scénarios par horizon au lieu de les fusionner par majorité.

## Outputs

```text
ContinuousMarketStateV1
BookFeatureStateV1
OrderFlowStateV1
LiquidityExitZoneV1
ParticipantBehaviorScenarioV1
ScenarioSetV1
```

Tous restent non exécutables.

## Validation

- anti-lookahead événementiel ;
- book reconstruction ;
- aggressor confidence ;
- calibration des scénarios si probability ;
- ablation des preuves ;
- contradictions conservées ;
- zones non présentées comme ordres privés observés ;
- replay déterministe ;
- aucun Signal/TradeIntent/OrderIntent.

## Gate

V5 reste verrouillée jusqu'à ce que les scénarios soient falsifiables, audités et accompagnés de limites connues.
