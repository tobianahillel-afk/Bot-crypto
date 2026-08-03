# Transaction Cost Model Policy — Lot 10

Le Lot 10 ajoute un modèle neutre de coûts de transaction pour préparer une future simulation plus réaliste. Il estime des frais, un spread et un slippage théoriques sur les steps `WAIT` du Lot 9.

Une estimation de coût n'est pas un ordre. Elle ne contient aucune logique de stratégie, aucune décision LONG/SHORT, aucune logique buy/sell, aucun target, aucun label et aucun `future_*`.

Les estimations Lot 10 sont marquées `trade_allowed=false` et `used_for_decision=false`. Elles ne peuvent pas déclencher un trade et ne changent pas le PnL.

## Limites V0

Le modèle utilise un notional théorique fixe et des paramètres statiques. Il sert à auditer la structure future de friction de marché, pas à mesurer une performance exploitable.
