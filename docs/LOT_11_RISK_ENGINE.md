# Lot 11 Risk Engine & Decision Firewall V0

Le Lot 11 ajoute une couche de Risk Engine défensive, déterministe et non exécutable.

## Principes

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `used_for_decision = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Blocage par défaut

Le Risk Engine bloque par défaut et formalise les raisons minimales suivantes :

- `LIVE_EXECUTION_DISABLED`
- `LEVERAGE_FORBIDDEN`
- `NO_ORDER_ROUTER`
- `NO_EXCHANGE_CONNECTOR`
- `EDUCATIONAL_MODE_ONLY`
- `RISK_ENGINE_BLOCKS_BY_DEFAULT`

## Portée

Le Lot 11 ne crée aucune stratégie, aucun ordre, aucun fill, aucun PnL exploitable, aucun paper trading, aucun appel API et aucun WebSocket.

Les estimations de coûts du Lot 10 peuvent être lues comme contexte documentaire, mais elles ne sont jamais utilisées pour ouvrir une position.

## Consommation par le Lot 12

Le Lot 12 Exposure Guard peut relire les snapshots du Risk Engine Lot 11 comme contexte documentaire pour confirmer qu’aucune exposition active n’est autorisée. Cette consommation ne change pas les invariants du Lot 11 : `trade_allowed=false`, `used_for_decision=false`, `live_execution=DISABLED` et `leverage=FORBIDDEN`.

Dans ce contexte, le Lot 12 maintient aussi `allocation_allowed=false`, `rebalance_allowed=false` et `capital_at_risk=0`.
