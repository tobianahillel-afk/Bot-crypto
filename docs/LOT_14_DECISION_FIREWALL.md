# Lot 14 Final Decision Firewall & Audit Trail V0

Le Lot 14 ajoute une couche finale d’audit décisionnel défensif.

## Principes

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `final_decision = WAIT`
- `final_system_decision = BLOCK_TRADING`
- `decision_firewall_state = ACTIVE`
- `execution_allowed = false`
- `trade_allowed = false`
- `used_for_decision = false`
- `risk_allowed = false`
- `exposure_allowed = false`
- `portfolio_state = FROZEN`
- `portfolio_change_allowed = false`
- `allocation_change_allowed = false`
- `rebalance_allowed = false`
- `order_routing_allowed = false`
- `external_connectivity_allowed = false`
- `human_review_required = true`
- `capital_at_risk = 0`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Blocage par défaut

Decision Firewall formalise les raisons minimales suivantes :

- `FINAL_DECISION_FIREWALL_ACTIVE`
- `TRADING_DECISION_WAIT`
- `SYSTEM_DECISION_BLOCK_TRADING`
- `RISK_ENGINE_BLOCKS_BY_DEFAULT`
- `EXPOSURE_GUARD_BLOCKS_BY_DEFAULT`
- `PORTFOLIO_FROZEN`
- `NO_ORDER_ROUTER`
- `NO_EXCHANGE_CONNECTOR`
- `LIVE_EXECUTION_DISABLED`
- `LEVERAGE_FORBIDDEN`
- `EDUCATIONAL_MODE_ONLY`
- `HUMAN_REVIEW_REQUIRED`

## Portée

Le Lot 14 n’autorise aucune décision exécutable, aucune connectivité externe active, aucune variation de portefeuille et aucun capital à risque.

Les artefacts Lot 7, Lot 10, Lot 11, Lot 12 et Lot 13 sont lus uniquement comme contexte documentaire.

Le projet reste éducatif, non connecté à un exchange, avec `live_execution = DISABLED`, `leverage = FORBIDDEN` et `trade_allowed = false`.

## Note Lot 15-bis

Le faux échec observé avant le Lot 15 ne venait pas du moteur Lot 14 lui-même.

La fragilité provenait du replay de validation Lot 0 : un fichier de contrôle local était créé puis supprimé immédiatement, ce qui pouvait casser une autre validation partageant le même artefact.

Le correctif Lot 15-bis rend cette étape stable :

- le replay de validation reste disponible après contrôle ;
- l’écriture est atomique ;
- la chaîne exacte Lot 14 redevient reproductible avant le passage au Decision Ledger.
