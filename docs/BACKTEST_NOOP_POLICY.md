# Backtest NOOP Policy — Lot 9

La policy par défaut du Lot 9 est `noop_wait_policy`.

Elle produit toujours :

```text
decision = WAIT
trade_allowed = false
orders_created = []
fills_created = []
pnl_impact = 0
used_for_decision = false
```

Cette policy est volontairement neutre. Elle ne contient aucune règle buy/sell, aucune entrée, aucune sortie et aucun signal exploitable.

## Pourquoi WAIT

Le projet impose un comportement défensif par défaut. Tant que les lots de stratégie, backtest supervisé et paper trading ne sont pas explicitement autorisés, la seule décision acceptable est `WAIT`.

## Garantie Lot 9

Le Lot 9 vérifie que 48 steps sont rejoués et que les 48 décisions restent `WAIT`. Aucun ordre n'est créé et aucun fill n'est créé.
