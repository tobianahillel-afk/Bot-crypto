# Lot 17 Local Health Monitor & Integrity Checks V0

Le Lot 17 ajoute un contrôle local de santé, d'intégrité et de cohérence opérationnelle.

## Cause du Lot 17-bis

Le chef de projet a demandé un Lot 17-bis car la chaîne existante cassait d'abord sur `scripts/audit_lot8_feature_registry.py`.

La cause était un nom temporaire fixe `.feature_registry_audit_lot8.json.tmp`, fragile sur le workspace partagé et exposé quand plusieurs chaînes réécrivaient le même artefact.

Le correctif remplace ce tmp fixe par un tmp unique dans le même dossier, avec `flush`, `fsync`, `replace` atomique et nettoyage best-effort.
Le lot 17-bis corrige aussi un faux écart complémentaire: les checksums de `dataset_catalog.json` sont désormais calculés sur un ordre canonique, ce qui évite qu'une réécriture idempotente du catalogue casse Lot 16 ou Lot 17.
Depuis le Lot 18, ce calcul exclut aussi les nouvelles entrées audit-only de conformité finale, afin que le Health Monitor reste valide après ajout des artefacts documentaire du Lot 18.

Le diagnostic `scripts/diagnose_exact_chain_return_shell.py` a aussi été réaligné avec l'état actuel du projet : il rafraîchit le manifeste Lot 16 avant `pytest` pour éviter un faux échec sur des checksums Lot 16 devenus obsolètes après une réécriture Lots 7 à 10.

## Rôle

Le Health Monitor :

- vérifie uniquement des artefacts locaux explicites ;
- lit `data/audit/dataset_catalog.json` ;
- lit `data/audit/reproducibility_manifest_lot16.json` ;
- lit `data/audit/reproducibility_artifacts_lot16.jsonl` ;
- vérifie les artefacts critiques des Lots 12 à 16 ;
- vérifie les rapports critiques des Lots 12 à 16 ;
- vérifie les scripts run / validate / diagnose des Lots 12 à 16 ;
- vérifie les comptages critiques `36 / 12 / 48` pour les Lots 12 à 15 ;
- vérifie les références de checksum du manifeste Lot 16 ;
- met à jour le catalogue dataset de manière idempotente.

Le Lot 18 relit ensuite ces artefacts pour produire la certification finale no-trading, sans modifier le caractère local et non exécutable du Lot 17.

## Portée

Le Lot 17 :

- ne crée aucune stratégie ;
- ne produit aucune décision exécutable ;
- ne fait aucun appel réseau ;
- ne crée aucun connecteur exchange ;
- ne produit aucun ordre, aucun fill et aucun PnL exploitable ;
- ne fait ni paper trading ni live trading.

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

Le projet reste éducatif, local et non connecté à un exchange.
