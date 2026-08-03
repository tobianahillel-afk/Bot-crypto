# Lot 12 Exposure Guard & Capital Safety Snapshot V0

Le Lot 12 ajoute une couche défensive d’exposition et de sécurité capital.

## Principes

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `used_for_decision = false`
- `exposure_allowed = false`
- `allocation_allowed = false`
- `rebalance_allowed = false`
- `current_exposure_units = 0`
- `max_exposure_units = 0`
- `capital_at_risk = 0`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Blocage par défaut

L’Exposure Guard bloque par défaut et formalise les raisons minimales suivantes :

- `NO_CAPITAL_ALLOCATION`
- `NO_ACTIVE_EXPOSURE`
- `NO_ORDER_ROUTER`
- `NO_EXCHANGE_CONNECTOR`
- `RISK_ENGINE_BLOCKS_BY_DEFAULT`
- `EDUCATIONAL_MODE_ONLY`
- `LIVE_EXECUTION_DISABLED`
- `LEVERAGE_FORBIDDEN`

## Portée

Le Lot 12 ne crée aucune stratégie, aucun ordre, aucun fill, aucun PnL exploitable, aucun paper trading, aucun appel API, aucun WebSocket et aucune exposition active.

Les artefacts Lot 7, Lot 10 et Lot 11 sont lus uniquement comme contexte documentaire.

Dans le Lot 13, les artefacts Lot 12 restent eux aussi du contexte documentaire uniquement pour formaliser un portefeuille figé.
