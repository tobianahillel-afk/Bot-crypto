# Anchored VWAP Policy — Lot 4

Lot 4 ajoute un Anchored VWAP V1 avec ancres déterministes.

## Ancres autorisées

```text
session_start
pivot_high
pivot_low
```

Ancres minimales :

```text
session_start_5m
session_start_15m
first_confirmed_pivot_high_5m
first_confirmed_pivot_low_5m
```

## Règles anti-look-ahead

Pour une ancre `session_start` :

```text
selected_at = anchor_time
usable_from = anchor_time
```

Pour une ancre pivot :

```text
anchor_time = pivot_time
selected_at = pivot.usable_from
usable_from = pivot.usable_from
```

Un point Anchored VWAP ne peut jamais être émis avant `usable_from`.

```text
AnchoredVWAPPoint.available_at >= AnchorPoint.usable_from
```

## Interdiction de sélection après coup

Une ancre doit être sélectionnée par une règle écrite avant le calcul. Il est interdit de choisir une ancre parce qu'elle donne un résultat visuellement intéressant.

## Interdictions

- Aucun signal LONG/SHORT.
- Aucun target.
- Aucun label.
- Aucun champ `future_*`.
- Aucun trading.
- Aucun backtest.
