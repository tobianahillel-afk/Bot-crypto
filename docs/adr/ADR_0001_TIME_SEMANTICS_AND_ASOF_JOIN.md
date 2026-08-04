# ADR-0001 — Time semantics, closed bars and as-of backward join

Status: **ACCEPTED FOR LOT 26 READINESS**  
Date: 2026-08-04  
Scope: V2 Market Analysis Offline

## Context

Le flux source peut être continu. Une analyse multi-timeframe ne doit cependant jamais utiliser une
barre ouverte, une donnée future ou une révision qui n’était pas disponible au moment évalué.

## Decision

### Canonical clocks

- `event_time` : temps économique de l’observation source ;
- `bar_open_time` : début inclusif de la barre ;
- `bar_close_time` : fin exclusive de la barre ;
- `source_time` : timestamp fourni par la source ;
- `receive_time` : arrivée locale ;
- `process_time` : traitement local ;
- `available_at` : premier instant où l’état pouvait légalement être consommé ;
- `decision_time` : instant logique de l’évaluation descriptive.

Toutes les valeurs sont UTC, ISO-8601 avec suffixe `Z`.

### Interval convention

```text
[bar_open_time, bar_close_time)
```

Une barre 5m ouverte à `10:00:00Z` agrège les événements `>=10:00:00Z` et `<10:05:00Z`.
Elle ne peut être utilisée avant sa clôture et sa disponibilité.

### Publication cadence

- ingestion : continue ;
- état 5m : à chaque nouvelle barre 5m fermée ;
- état 15m : à chaque nouvelle barre 15m fermée ;
- évaluation Lot 26 : à chaque nouvel état 5m admissible.

Le même état 15m peut être associé à trois états 5m successifs. Cela est voulu : le 15m représente
un contexte supérieur plus lent.

### Eligibility

```text
bar_close_time <= available_at <= decision_time
```

`available_at` intègre le délai de calcul/validation. `process_time` ne remplace jamais
`available_at`.

### As-of backward join

Pour un état local 5m à `decision_time=t`, sélectionner l’état 15m admissible maximal selon :

```text
bar_close_time DESC,
available_at DESC,
revision_id DESC,
sequence_id DESC
```

Aucun forward fill depuis un état futur. Aucune tolérance future.

### Revisions

Une révision conserve le même `source_bar_id`, augmente `revision_id` et possède un nouvel
`available_at`. Un replay historique à l’instant `t` ne voit que les révisions disponibles à `t`.

### Staleness

La configuration fixe les limites. Dépassement → état `UNKNOWN/BLOCKED`, jamais fallback permissif.

### Timezones and calendars

UTC est canonique. Un timestamp naïf, une timezone non convertible ou une incohérence de durée
produit `MTF_TIMEZONE_INVALID` ou `BLOCKED_TIME_ALIGNMENT`.

## Consequences

- pas de lookahead ;
- divergence 5m/15m observable sans veto automatique ;
- replay déterministe ;
- extensibilité future à d’autres timeframes par registre, sans modifier la sémantique.

## Rejected alternatives

- comparer les barres par simple index de tableau ;
- utiliser la barre 15m en construction ;
- aligner par timestamp le plus proche dans les deux directions ;
- donner au 15m un veto automatique ;
- mélanger logique microstructure/Game Theory dans le Lot 26.
