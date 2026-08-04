# ADR-0001 — Time semantics, continuous state, closed bars and ASOF_BACKWARD

Status: **ACCEPTED FOR LOT 26 READINESS**  
Date: 2026-08-04  
Scope: V2 foundation, reusable by V3–V19

## Context

Le flux source peut être continu et les futurs moteurs pourront réagir à chaque événement matériel. Une analyse confirmée ne doit toutefois jamais utiliser une barre ouverte, une donnée future ou une révision qui n'était pas disponible au moment évalué.

Les 5m et 15m constituent la première relation activée du Lot 26. L'architecture doit rester extensible à d'autres résolutions et horloges de décision.

## Decision

### Canonical clocks

- `event_time` : temps économique de l'observation source ;
- `bar_open_time` : début inclusif de la barre ;
- `bar_close_time` : fin exclusive de la barre ;
- `source_time` : timestamp fourni par la source ;
- `receive_time` : arrivée locale ;
- `process_time` : traitement local ;
- `available_at` : premier instant où l'état pouvait légalement être consommé ;
- `decision_time` : instant logique de l'évaluation ;
- `monotonic_time` : durée locale lorsque nécessaire, jamais substitut du temps économique.

Toutes les valeurs persistées sont UTC et ISO-8601 avec suffixe `Z`.

### Temporal dimensions

Le système sépare obligatoirement :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Aucune dimension n'est déduite implicitement d'une autre.

### Continuous and confirmed states

- `ContinuousMarketStateV1` : état provisoire mis à jour par événements, prévu pour V3/V4 ;
- `TimeframeMarketContextStateV1` : état confirmé dérivé d'une agrégation fermée ;
- `open_bars` : observables uniquement comme états provisoires, jamais consommables comme états confirmés du Lot 26.

### Interval convention

```text
[bar_open_time, bar_close_time)
```

Une barre 5m ouverte à `10:00:00Z` agrège les événements `>=10:00:00Z` et `<10:05:00Z`. Elle ne peut être utilisée comme barre confirmée avant sa clôture et sa disponibilité.

### Lot 26 initial profile

```text
local_scale  = timebar-5m
higher_scale = timebar-15m
evaluation_trigger = CLOSED_LOCAL_BAR
```

- ingestion : potentiellement continue ;
- état 5m confirmé : à chaque nouvelle barre 5m fermée ;
- état 15m confirmé : à chaque nouvelle barre 15m fermée ;
- évaluation Lot 26 : à chaque nouvel état 5m admissible.

Le même état 15m peut être associé à trois états 5m successifs. Il représente un contexte supérieur plus lent.

### Eligibility

```text
bar_close_time <= available_at <= decision_time
```

`available_at` intègre calcul, validation et publication. `process_time` ne le remplace jamais.

### ASOF_BACKWARD

Pour une relation ordonnée `(local_scale, higher_scale)` à `decision_time=t`, sélectionner l'état supérieur admissible maximal selon :

```text
bar_close_time DESC
available_at DESC
revision_id DESC
sequence_id DESC
```

Le Lot 26 active uniquement `(timebar-5m, timebar-15m)`. Aucun forward fill depuis un état futur et aucune tolérance future ne sont autorisés.

### Future scale graph

Les relations temporelles futures sont un graphe orienté `G=(S,E)`. Chaque arête conserve son résultat propre. Une extension à 1m, 1h, volume bars ou event stream nécessite configuration, tests et gate dédiés ; elle ne modifie pas rétroactivement le profil Lot 26 v1.

### Decision clocks

Le Lot 26 active seulement `CLOSED_LOCAL_BAR`. Les déclencheurs `MARKET_EVENT`, `BOOK_IMBALANCE_CHANGE`, `LIQUIDITY_SWEEP`, `FORECAST_UPDATE` ou `RISK_EVENT` restent planifiés pour les versions propriétaires correspondantes.

### Revisions

Une révision conserve le même `source_bar_id`, augmente `revision_id` et possède un nouvel `available_at`. Un replay à l'instant `t` ne voit que les révisions disponibles à `t`.

### Staleness

La configuration fixe les limites par échelle. Dépassement → `UNKNOWN/BLOCKED`, jamais fallback permissif.

### Timezones and ordering

Un timestamp naïf, une timezone non convertible, une incohérence de durée, une séquence ambiguë ou un événement hors ordre non résolu produit un état bloqué et auditable.

## Consequences

- pas de lookahead ;
- flux continu compatible avec des états confirmés ;
- divergence 5m/15m observable sans veto automatique ;
- replay déterministe ;
- interface extensible ;
- aucune confusion entre résolution, prévision, horloge et détention ;
- aucun vote naïf entre timeframes.

## Rejected alternatives

- comparer les barres par simple index ;
- utiliser la barre 15m en construction ;
- aligner par timestamp le plus proche dans les deux directions ;
- donner au 15m un veto automatique ;
- figer toute l'architecture à deux timeframes ;
- utiliser un vote majoritaire entre horizons ;
- mélanger prédiction, microstructure ou Game Theory dans le Lot 26.
