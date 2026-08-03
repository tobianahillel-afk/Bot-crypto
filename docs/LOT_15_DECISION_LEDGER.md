# Lot 15 Decision Ledger & Immutable Audit Trail V0

Le Lot 15-bis corrige d’abord la reproductibilité de la base Lot 14, puis finalise un `Decision Ledger` strictement local.

## Cause du Lot 15-bis

Le faux échec `ERROR: replay file missing` venait d’un replay de validation Lot 0 écrit sur un chemin stable puis supprimé juste après contrôle. Cette suppression rendait le contrôle fragile si plusieurs validations partageaient le même artefact temporaire.

La correction appliquée :

- conserve le replay de validation local après contrôle ;
- écrit ce replay de manière atomique ;
- rétablit une base Lot 14 reproductible avant l’implémentation du ledger.

## Rôle du Decision Ledger

Le `Decision Ledger` est un journal d’audit local et éducatif.

Il enregistre uniquement des décisions déjà bloquées par le Lot 14 et ne produit aucune décision exécutable.

Les artefacts Lot 7, Lot 10, Lot 11, Lot 12, Lot 13 et Lot 14 sont consommés comme contexte documentaire uniquement.

## Invariants conservés

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `final_decision = WAIT`
- `final_system_decision = BLOCK_TRADING`
- `execution_allowed = false`
- `trade_allowed = false`
- `risk_allowed = false`
- `exposure_allowed = false`
- `portfolio_change_allowed = false`
- `allocation_change_allowed = false`
- `rebalance_allowed = false`
- `external_connectivity_allowed = false`
- `human_review_required = true`
- `ledger_state = RECORDED`
- `audit_trail_state = ACTIVE`
- `immutability_mode = APPEND_ONLY_SIMULATED`

## Portée

`APPEND_ONLY_SIMULATED` signifie uniquement qu’un journal local est écrit en séquence pour l’audit éducatif.

Le projet reste éducatif, non connecté à un exchange, avec `live_execution = DISABLED`, `leverage = FORBIDDEN` et `trade_allowed = false`.

## Suite documentaire

Le Lot 16 réutilise le `Decision Ledger` comme contexte documentaire local pour construire un manifeste de reproductibilité.

Cette couche supplémentaire ne change pas les décisions du Lot 15 : le ledger reste strictement audit-only, local et non exécutable.
