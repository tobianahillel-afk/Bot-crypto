# Backtest Anti-Lookahead Policy — Lot 9

Le replay Lot 9 applique un garde-fou anti-lookahead sur chaque `MarketState` et chaque `BacktestStep`.

## Règles vérifiées

```text
market_state.available_at <= step.available_at
component_available_at <= market_state.available_at
aucun champ future_*
aucun champ target
aucun champ label
aucun signal LONG/SHORT
```

## Rôle de available_at

`available_at` représente le moment où l'information devient disponible. Le replay ne doit pas utiliser une donnée dont la disponibilité est postérieure au step courant.

## Rôle de component_available_at

Un `MarketState` agrège plusieurs composants. Le champ `component_available_at` garantit que l'objet agrégé n'est pas disponible avant ses composants.

## Limites

Cette politique V0 vérifie la cohérence temporelle et l'absence de champs interdits. Elle ne prouve pas formellement chaque formule mathématique utilisée dans les lots précédents.
