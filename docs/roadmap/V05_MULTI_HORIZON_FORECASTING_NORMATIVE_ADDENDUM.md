# V5 Normative Addendum — Stochastic Multi-Horizon Forecasting

Ce document complète V5 Lots 53–59.

## Objective

Transformer des états disponibles et scénarios V4 en hypothèses prédictives falsifiables, distributions multi-horizons et stratégies candidates, sans choisir venue ou taille finale.

## Temporal contract

Chaque recherche déclare séparément :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Le registre initial propose 30s, 5m, 15m et 1h. Chaque horizon est calibré et validé indépendamment.

## Lot mapping

### Lot 53

Le registre d'hypothèses inclut mécanisme, population, régime, horizon, cible, null hypothesis, baselines et falsification.

### Lot 54

`StrategyCandidateV1` inclut forecast horizons autorisés, entrée, sortie, `ExitPolicyV1`, invalidation, signal TTL et holding horizon.

### Lot 55

`SignalV1` référence un `MultiHorizonForecastV1`, une calibration et une expiration. Aucun champ `probability` sans calibration.

### Lot 56

La frontière Signal→TradeIntent conserve l'horizon, le risque maximal et les preuves sans créer d'OrderIntent.

### Lot 57

Éligibilité par régime, horizon, staleness, contradiction inter-horizons et invalidation.

### Lot 58

Decay, drift, calibration decay et retrait par horizon.

### Lot 59

Promotion vers V6 seulement si hypothèses, modèles, configs, datasets et essais négatifs sont gelés.

## Forecast output

Pour chaque horizon :

```text
expected_return
return_quantiles
volatility_forecast
direction_probability if calibrated
target_hit_probability if calibrated
stop_hit_probability if calibrated
time_to_event
MAE/MFE distributions
regime_transition probability if calibrated
uncertainty
```

## Model selection

Les modèles stochastiques ou ML sont des candidats. Chaque modèle est comparé aux baselines naïves et simples. La sélection tient compte de calibration, stabilité, coûts et capacité, pas seulement d'une métrique in-sample.

## Cross-horizon logic

- erreurs conjointes mesurées ;
- contradictions transformées en scénarios ;
- aucune majorité naïve ;
- horizon du mandat de stratégie explicite ;
- prévention du double comptage des mêmes features ;
- modèle d'agrégation séparé et versionné si nécessaire.

## Validation gate

V6 doit démontrer hors échantillon la correction statistique et économique. V5 ne peut promouvoir une simple sophistication ou un score heuristique comme alpha.
