# Stochastic Continuous State and Multi-Horizon Forecasting Standard

Statut : `PLANNED_LOCKED_STANDARD`  
Applicabilité : V3–V7, avec validation V6 obligatoire avant toute promotion.

## 1. Finalité

Le marché est traité comme un système partiellement observé, bruité, non stationnaire et soumis à des changements de régime. Une valeur ponctuelle ou un score heuristique ne constitue pas une prévision probabiliste.

Le standard définit les contrats et preuves requis pour les futurs modèles continus et multi-horizons. Il n'implémente aucun modèle et n'autorise aucune prédiction dans le Lot 26.

## 2. Séparation des couches

```text
observations continues
→ état latent estimé
→ features par résolution
→ prévisions par horizon
→ scénarios concurrents
→ validation statistique et économique
→ signal éventuel dans V5
```

Les sorties descriptives du Lot 26 restent en amont de cette chaîne.

## 3. `ContinuousMarketStateV1`

Le futur état continu doit au minimum référencer :

```text
state_id
instrument_id
as_of_event_time
available_at
source_event_range
market_quality_state
price_state
volatility_state
liquidity_state
order_flow_state
derivatives_state
latent_regime_state
state_uncertainty
model_ids
config_versions
lineage_id
```

Les champs non disponibles restent `UNKNOWN`; ils ne sont jamais remplacés par zéro.

## 4. Familles de modèles éligibles à la recherche

Les modèles suivants sont des candidats à évaluer, pas des choix imposés :

- modèles espace-état et filtres de Kalman lorsque les hypothèses sont défendables ;
- filtres particulaires pour états non linéaires/non gaussiens ;
- Hidden Markov Models ou modèles semi-markoviens pour régimes ;
- modèles de volatilité conditionnelle ;
- processus ponctuels et Hawkes pour intensités d'événements ;
- modèles de survie/hazard pour temps avant target, stop ou liquidation ;
- régression quantile et distributional forecasting ;
- modèles probabilistes monotones ou régularisés ;
- ensembles calibrés et modèles de changement de régime.

Tout modèle doit être comparé à des baselines simples. La sophistication n'est jamais une preuve d'amélioration.

## 5. `MultiHorizonForecastV1`

Une prévision porte sur un instrument, un `decision_time` et un ensemble d'horizons enregistrés. Pour chaque horizon :

```text
forecast_horizon
expected_return
median_return
return_quantiles
volatility_forecast
direction_probability (uniquement calibrée)
target_hit_probability (uniquement calibrée)
stop_hit_probability (uniquement calibrée)
time_to_target_distribution
maximum_adverse_excursion_distribution
maximum_favorable_excursion_distribution
regime_transition_probability (uniquement calibrée)
liquidity_risk
model_uncertainty
data_uncertainty
calibration_id
```

Une sortie peut être partiellement `UNKNOWN`. Une distribution absente ne devient pas une estimation ponctuelle arbitraire.

## 6. Horizon registry

`config/research/forecast_horizon_registry_v1.json` enregistre les horizons autorisés. La première proposition contient 30s, 5m, 15m et 1h, tous `PLANNED_LOCKED`.

Chaque horizon nécessite :

- définition exacte de la cible ;
- convention de rendement ;
- univers et régime ;
- calendrier d'observation ;
- label availability ;
- modèle et hyperparamètres gelés ;
- calibration indépendante ;
- coûts et capacité applicables ;
- tests hors échantillon.

## 7. Dépendance entre horizons

Le système doit mesurer les erreurs conjointes et ne peut supposer l'indépendance.

Obligations :

- matrice de corrélation des erreurs ;
- cohérence des quantiles emboîtés ;
- tests de contradictions entre horizons ;
- détection des prévisions dominées ou redondantes ;
- scénario expliquant les divergences ;
- absence de vote majoritaire naïf ;
- attribution de la décision à un mandat/horizon de stratégie explicite.

## 8. Calibration

Aucun champ nommé `probability` ne peut être publié sans :

- jeu de calibration temporellement séparé ;
- calibration versionnée ;
- reliability diagram ;
- Brier score ou log loss adapté ;
- calibration par régime et horizon ;
- intervalle d'incertitude ;
- test de dérive ;
- règles d'expiration.

Une confiance heuristique doit être nommée `score` ou `confidence_proxy`, jamais probabilité.

## 9. Validation statistique

Pour chaque horizon :

- baseline naïve et aléatoire ;
- walk-forward ;
- purged cross-validation et embargo ;
- tests placebo ;
- correction des tests multiples ;
- bootstrap et Monte Carlo ;
- sensibilité aux paramètres ;
- stabilité par sous-période, régime et venue ;
- comparaison de distributions, pas uniquement de moyennes ;
- suivi des essais négatifs.

## 10. Validation économique

Une prévision n'est promotionnable que si son utilisation produit une valeur nette après :

```text
fees
spread
slippage
market impact
funding
adverse selection
missed fills
latency
capacity constraints
```

L'amélioration statistique sans valeur économique nette est insuffisante.

## 11. Anti-lookahead et disponibilité

Toute feature et tout état portent `available_at`. La cible future porte `label_available_at` et n'est jamais disponible à `decision_time`.

Tests obligatoires :

- permutation temporelle ;
- accès futur monkeypatché ;
- révision tardive ;
- fuseau naïf ;
- horizon chevauchant les folds ;
- dépendance indirecte à un label ;
- leakage par normalisation globale.

## 12. Décision et exécution

```text
forecast != scenario
scenario != signal
signal != trade intent
trade intent != order intent
```

Le modèle de prévision ne choisit ni venue, ni taille finale, ni type d'ordre. V7 possède l'approbation risque et V15 possède le lifecycle d'ordre.

## 13. Auditabilité

Chaque prévision référence :

```text
forecast_id
model_id + version
calibration_id
dataset_id
feature_set_id
state_ids
horizon_registry_version
decision_time
available_at
code_commit
config_checksum
seed
replay_id
```

## 14. Tests minimaux

- cas analytiques connus ;
- property-based ;
- mutation testing ;
- calibration ;
- invariance et monotonie attendues ;
- comportement sous données manquantes ;
- stress de changement de régime ;
- stabilité numérique ;
- déterminisme conditionnel à seed/config ;
- replay ;
- non-régression.

## 15. Restrictions pré-Lot26

```text
Lot26 forecast generation = FORBIDDEN
Lot26 prediction claims = FORBIDDEN
Lot26 probability claims = FORBIDDEN
Lot26 signal generation = FORBIDDEN
```

Le Lot 26 fournit seulement un état descriptif multi-échelle destiné à être consommable ultérieurement par la recherche prédictive.
