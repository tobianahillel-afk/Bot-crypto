# Backtest Replay Engine Policy — Lot 9

Le Backtest Replay Engine V0 est une infrastructure de replay déterministe. Il relit les objets `MarketState` déjà validés du Lot 7 dans un ordre temporel contrôlé.

Ce lot ne définit aucune stratégie. Il ne cherche pas de performance financière, ne simule pas d'ordre exploitable et ne prépare aucun passage en production.

## Objectif

L'objectif est de prouver que le projet peut parcourir une séquence de marché déjà construite sans voir le futur. Chaque step est une observation neutre. La décision associée reste `WAIT`.

## Replay, backtest, stratégie et paper trading

Un replay est une lecture ordonnée de données historiques. Un backtest complet contient généralement une stratégie, des règles d'entrée/sortie, des ordres simulés et une mesure de performance. Le Lot 9 ne fait que le replay V0.

Le paper trading implique une boucle proche du réel et une exécution simulée. Le Lot 9 n'implémente pas ce comportement.

## Règles de sécurité

`trade_allowed=false` partout. Les listes `orders_created` et `fills_created` restent vides. `pnl_impact` et `pnl_total` restent à zéro.

## Limites V0

Le moteur ne calcule aucune performance trading avancée. Il ne génère aucun signal LONG/SHORT et ne crée aucun champ target, label ou future_*.
