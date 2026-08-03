# Lot 16 Dataset Lineage & Reproducibility Manifest V0

Le Lot 16 ajoute un manifeste local de traçabilité et de reproductibilité.

## Rôle

Le manifeste recense uniquement des artefacts locaux explicites.

Il indique :

- quels artefacts officiels sont suivis ;
- par quel lot ils sont produits ;
- quels fichiers sont consommés comme contexte documentaire ;
- quels checksums locaux sont associés ;
- quels comptages critiques doivent être rejoués ;
- quelles validations doivent être relancées pour reproduire l’état.

## Portée

Le Lot 16 ne produit aucune décision exécutable.

Il ne fait aucun appel réseau, ne crée aucune stratégie et ne référence aucun exchange.

Les artefacts Lot 0 à Lot 15, `data/audit/dataset_catalog.json`, les rapports canoniques `reports/lot_*` et les artefacts audit officiels des lots 7 à 15 sont utilisés comme contexte documentaire local uniquement.

Depuis le Lot 17, le calcul `source_catalog_checksum` continue d'ignorer les entrées auto-référentes du Lot 16 et ignore aussi les entrées audit-only du Health Monitor Lot 17. Cela conserve un manifeste Lot 16 cohérent même quand le catalogue dataset reçoit de nouveaux enregistrements locaux non exécutables.
Le checksum est en plus calculé sur un ordre canonique des enregistrements afin qu'un `upsert` atomique local ne provoque plus de faux mismatch de reproductibilité.

## Invariants

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `final_decision = WAIT`
- `final_system_decision = BLOCK_TRADING`
- `trade_allowed = false`
- `execution_allowed = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`
- `exposure_allowed = false`
- `allocation_allowed = false`
- `rebalance_allowed = false`
- `portfolio_state = FROZEN`
- `capital_at_risk = 0`
- `external_connectivity_allowed = false`
- `human_review_required = true`
- `immutability_mode = APPEND_ONLY_SIMULATED`

Le projet reste éducatif et non connecté à un exchange.
