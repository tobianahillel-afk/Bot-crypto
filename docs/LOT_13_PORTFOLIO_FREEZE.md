# Lot 13 Portfolio Freeze & Allocation Firewall V0

Le Lot 13 ajoute une couche défensive de gel de portefeuille.

## Principes

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `used_for_decision = false`
- `portfolio_state = FROZEN`
- `allocation_state = DISABLED`
- `rebalance_state = DISABLED`
- `portfolio_change_allowed = false`
- `allocation_change_allowed = false`
- `allocation_allowed = false`
- `rebalance_allowed = false`
- `new_exposure_allowed = false`
- `exposure_allowed = false`
- `current_exposure_units = 0`
- `max_exposure_units = 0`
- `capital_at_risk = 0`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Blocage par défaut

Portfolio Freeze formalise les raisons minimales suivantes :

- `PORTFOLIO_FROZEN`
- `ALLOCATION_DISABLED`
- `REBALANCE_DISABLED`
- `NO_CAPITAL_ALLOCATION`
- `NO_ACTIVE_EXPOSURE`
- `NO_ORDER_ROUTER`
- `NO_EXCHANGE_CONNECTOR`
- `RISK_ENGINE_BLOCKS_BY_DEFAULT`
- `EXPOSURE_GUARD_BLOCKS_BY_DEFAULT`
- `EDUCATIONAL_MODE_ONLY`
- `LIVE_EXECUTION_DISABLED`
- `LEVERAGE_FORBIDDEN`

## Portée

Le Lot 13 n’autorise aucune modification de portefeuille, aucune allocation, aucune réallocation, aucune variation d’exposition et aucun capital à risque.

Les artefacts Lot 10, Lot 11 et Lot 12 sont lus uniquement comme contexte documentaire.

Le projet reste éducatif, non connecté à un exchange, avec `live_execution = DISABLED` et `leverage = FORBIDDEN`.

Dans le Lot 14, les artefacts Lot 13 restent eux aussi du contexte documentaire uniquement pour formaliser une décision finale non exécutable.
