# Temporal Multi-Scale and Decision Clock Architecture

Statut : `PRE_LOT26_NORMATIVE`  
Projet : **Crypto Quant Bot V3.1-Ops**

## 1. Intention

Le système consomme un flux canonique unique et continu, puis construit plusieurs représentations temporelles du même marché. Il ne crée pas un robot indépendant par timeframe et n'utilise jamais un vote majoritaire naïf entre horizons.

La configuration initiale du Lot 26 utilise une relation ordonnée :

```text
timebar-5m (contexte local) → timebar-15m (contexte supérieur)
```

Cette paire est un profil d'amorçage, pas une limitation architecturale. Toute nouvelle résolution ou relation doit être ajoutée par configuration versionnée, tests, justification économique et gate de promotion.

## 2. Six notions temporelles distinctes

Chaque capability quantitative doit déclarer explicitement :

| Notion | Définition |
|---|---|
| `data_resolution` | granularité de l'observation ou de l'agrégation |
| `feature_lookback` | fenêtre historique consommée par une feature |
| `forecast_horizon` | durée future couverte par une prévision |
| `decision_clock` | événement ou cadence déclenchant une réévaluation |
| `signal_ttl` | durée pendant laquelle un signal demeure consommable |
| `holding_horizon` | durée attendue ou maximale d'une position |

Aucune de ces notions ne peut être déduite implicitement d'une autre. Une feature calculée sur des barres 5m peut alimenter une prévision à 30 secondes, 15 minutes ou une heure si la recherche l'autorise et si la validation hors échantillon le démontre.

## 3. Flux canonique continu

```text
sources marché
→ MarketDataEnvelopeV1
→ ordre canonique event_time / sequence_id
→ qualité, normalisation et disponibilité
→ ContinuousMarketStateV1
→ projections multi-échelles
→ états confirmés par résolution
```

Le flux continu conserve, selon la source :

- transactions ;
- changements de carnet ;
- séquences, révisions et checksums ;
- prix, volume et liquidité ;
- données dérivées autorisées ;
- `event_time`, `receive_time`, `process_time`, `available_at`.

Le Lot 26 ne construit pas encore ce pipeline événementiel. V3 en possède la gouvernance temporelle et V4 en possède les états microstructure.

## 4. État continu et état dérivé de barres

### 4.1 `ContinuousMarketStateV1`

État provisoire et événementiel, actualisé sans attendre une clôture de barre. Il pourra contenir, après les lots dédiés :

- dernier prix et spread ;
- profondeur et imbalance ;
- intensité des trades ;
- order flow et CVD ;
- liquidité, résilience et absorption ;
- qualité et fraîcheur ;
- incertitude et lineage.

Il n'est consommable que par les lots qui déclarent explicitement cette dépendance.

### 4.2 `TimeframeMarketContextStateV1`

État confirmé dérivé d'une agrégation temporelle fermée. Une barre ouverte peut être observée comme `PROVISIONAL_OPEN_BAR`, mais ne peut jamais être présentée comme un état confirmé ni être utilisée par le Lot 26.

```text
bar_close_time <= available_at <= decision_time
```

## 5. Registre des échelles

`config/temporal/temporal_scale_registry_v1.json` est la source de vérité des résolutions autorisées.

Une entrée déclare au minimum :

```text
scale_id
resolution_type
duration_seconds ou règle événementielle
aggregation_method
publication_policy
state_kind
status par version/lot
```

Les futures barres volume, dollar, tick ou imbalance sont possibles mais restent `PLANNED_LOCKED` tant que leurs contrats et tests ne sont pas approuvés.

## 6. Relations entre échelles

Les comparaisons sont modélisées comme un graphe orienté de relations entre échelles :

```text
G = (S, E)
```

- `S` : échelles enregistrées ;
- `E` : relations ordonnées local→contexte supérieur.

Le Lot 26 v1 active exactement une arête :

```text
E_v1 = {(timebar-5m, timebar-15m)}
```

Une version ultérieure peut ajouter d'autres arêtes sans modifier rétroactivement le résultat v1. L'agrégation de plusieurs arêtes devra conserver les résultats par arête et interdire le vote naïf.

## 7. Horloges de décision

`config/temporal/decision_clock_policy_v1.json` sépare les déclencheurs de la résolution des données et des horizons de prévision.

Déclencheurs prévus :

```text
CLOSED_LOCAL_BAR
MARKET_EVENT
BOOK_IMBALANCE_CHANGE
LIQUIDITY_SWEEP
VOLATILITY_BREAK
REGIME_CHANGE
FORECAST_UPDATE
RISK_EVENT
SCHEDULED_REEVALUATION
```

Seul `CLOSED_LOCAL_BAR` est activé pour le Lot 26. Les autres déclencheurs appartiennent aux versions ultérieures et ne doivent pas être simulés artificiellement dans le Lot 26.

Tout déclencheur porte :

- `trigger_id` ;
- `causal_event_id` ;
- `decision_time` ;
- `available_state_ids` ;
- politique d'idempotence ;
- raison de réévaluation.

## 8. Corrélation inter-horizons

Les futurs résultats à plusieurs horizons ne sont pas fusionnés par majorité.

Exemple :

```text
30s : pression acheteuse
5m  : rebond probable
15m : contexte baissier
1h  : régime baissier persistant
```

L'interprétation correcte peut être un rebond court dans une structure supérieure baissière. Le système doit conserver :

- chaque prévision et son horizon ;
- les dépendances entre erreurs ;
- les contradictions directionnelles ;
- les scénarios d'emboîtement ;
- l'horizon dominant selon le mandat de la stratégie ;
- l'incertitude jointe.

## 9. Anti-lookahead

Chaque état ou prévision est consommable seulement si :

```text
available_at <= decision_time
```

Règles supplémentaires :

- `ASOF_BACKWARD` uniquement pour sélectionner un état historique disponible ;
- aucune valeur finale d'une barre ouverte ;
- toute révision possède son propre `available_at` ;
- aucune interpolation utilisant un point futur ;
- tout ordre d'événements ambigu produit `BLOCKED_TIME_ORDER` ;
- replay sur l'ordre canonique obligatoire.

## 10. Auditabilité

Chaque décision temporelle doit permettre de reconstruire :

```text
scale_registry_version
decision_clock_policy_version
source_event_ids
bar_ids
bar_open_time
bar_close_time
available_at
decision_time
selected_scale_edges
tie_break_evidence
config_checksum
code_commit
replay_id
```

## 11. Propriété par version

| Périmètre | Owner |
|---|---|
| Lot 26 | comparaison descriptive 5m→15m, interface extensible |
| V3 | flux canonique, timestamps, qualité, reconciliation données |
| V4 | état continu microstructure, carnet, trades et scénarios |
| V5 | prévisions et stratégies par horizon |
| V6 | validation temporelle, coûts et robustesse |
| V7 | risque et sizing par horizon |
| V15 | exécution gouvernée et lifecycle des ordres |
| V19 | recherche haute résolution tick/L2/L3 |

## 12. Interdictions

- pas de vote majoritaire entre timeframes ;
- pas de probabilité sans calibration ;
- pas de conversion automatique d'un alignement en signal ;
- pas d'utilisation d'une barre ouverte comme donnée confirmée ;
- pas d'ajout de résolution sans registre et justification ;
- pas de mélange entre `forecast_horizon`, `signal_ttl` et `holding_horizon` ;
- pas de chemin live activé par cette architecture.
