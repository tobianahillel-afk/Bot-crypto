# Lot 8 — Anti-Lookahead Audit Policy

Une fuite temporelle apparaît quand un objet d'analyse utilise une information qui n'était pas encore disponible au moment où l'objet est censé être connu.

Dans ce projet, la règle centrale est :

```text
timestamp <= available_at
component_available_at <= available_at
usable_from <= available_at
```

## Rôle de `available_at`

`available_at` indique le premier instant à partir duquel la ligne est exploitable sans regarder le futur. Une candle agrégée 5m datée de `00:00` n'est disponible qu'après sa clôture, par exemple à `00:05`.

## Rôle de `component_available_at`

Pour `MarketStatePoint`, l'objet agrège plusieurs composants : candle, features, VWAP, volatilité, range, régime, pivots ou zones. `component_available_at` garde la disponibilité de chaque composant. Le `available_at` global doit être supérieur ou égal au maximum de ces valeurs.

## Rôle de `usable_from`

Les pivots, zones et anchors ne doivent pas être utilisés avant leur confirmation. `usable_from` empêche l'utilisation d'un objet détecté avec des candles futures.

## Limites V1

L'audit V1 est un vérificateur générique de cohérence temporelle. Il ne remplace pas une preuve formelle complète des algorithmes, mais il bloque les erreurs structurelles les plus dangereuses.
