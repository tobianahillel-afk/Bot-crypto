# Lot 9 Report — Backtest Replay Engine V0

Le Lot 9 ajoute une infrastructure de replay/backtest V0 sans stratégie.

## Résumé

Le moteur charge les `MarketState` 5m et 15m du Lot 7, les parcourt dans l'ordre temporel et applique une policy neutre `noop_wait_policy`.

## Sécurité

La décision reste `WAIT`, `trade_allowed=false`, aucun ordre n'est créé, aucun fill n'est créé et le PnL reste nul.

## Anti-lookahead

Le replay vérifie que les objets observés ne sont pas disponibles après le step courant. Il vérifie aussi l'absence de champs `future_*`, `target`, `label` et de directions LONG/SHORT.

## Limites V0

Ce lot ne contient aucune stratégie, aucun backtest de performance, aucune logique buy/sell, aucun paper trading et aucune exécution live.

## Addendum Lot 9-bis — Robustesse orchestrateur / CI finale

Le Lot 9-bis ne change pas le Backtest Replay Engine V0. Il corrige uniquement la robustesse de validation CI après rejet d'audit du Lot 9.

Corrections :

```text
- suppression de os.execv dans les wrappers validate_all_until_lot5.py à validate_all_until_lot9.py ;
- remplacement par subprocess.run vers le script shell, sans capture stdout/stderr ;
- ajout ou confirmation de exit 0 explicite dans les scripts shell Lots 5 à 9 ;
- suppression du pytest imbriqué dans les orchestrateurs Lots 6 à 9 ;
- pytest reste exécuté séparément par la chaîne CI obligatoire ;
- tests d'orchestrateurs maintenus en mode smoke uniquement.
```

Le replay Lot 9 reste neutre : `WAIT`, aucun ordre, aucun fill, `pnl_total=0`.

## Lot 9-ter — Robustesse CI complète

Le Lot 9-ter corrige le rejet résiduel lié à la chaîne complète obligatoire. Il ajoute `scripts/run_required_chain_until_lot9.sh` avec un timeout par étape, stabilise les écritures JSON/Markdown, rend `DatasetCatalog.upsert()` idempotent par `dataset_id`, et ajoute des tests de mini-chaîne Lot 8 vers Lot 9 ainsi qu'un test de stabilité du catalogue.

La logique Backtest Replay V0 reste inchangée : policy `noop_wait_policy`, décisions `WAIT`, aucun ordre, aucun fill, aucun PnL exploitable et aucune fuite temporelle.


## Addendum Lot 9-ter — Robustesse CI complète

Le Lot 9-ter corrige le dernier rejet d'audit lié à la chaîne complète obligatoire. Le replay Lot 9 et la robustesse orchestrateur Lot 9-bis étaient fonctionnels, mais la commande complète pouvait encore rester bloquée en environnement CI.

Corrections appliquées : chaîne bornée `scripts/run_required_chain_until_lot9.sh`, scripts Lot 8 terminables, sorties explicites, écriture atomique des rapports, upsert idempotent de `dataset_catalog.json`, test de mini-chaîne Lot 8 vers Lot 9, et vérification de stabilité du catalogue après deux exécutions du replay.

Résultat final : chaîne complète obligatoire `rc=0`, `LOT 9-ter REQUIRED CHAIN: PASS`, `LOT 9 ORCHESTRATED VALIDATION: PASS`, `LOT 9 ORCHESTRATOR SMOKE: PASS`, `117 passed`.

## Addendum Lot 9-quater — Chaîne CI finale sans pytest bloquant

Le Lot 9-quater corrige le rejet résiduel du Lot 9-ter : `scripts/run_required_chain_until_lot9.sh` ne lance plus un pytest complet à la fin de la chaîne longue. Le script exécute désormais la chaîne fonctionnelle complète avec timeouts par étape, puis un sous-ensemble smoke pytest borné. Le pytest complet reste obligatoire, mais il est lancé séparément par la commande CI `python -m pytest -q`.

Un diagnostic manuel/CI a été ajouté : `scripts/diagnose_pytest_after_chain.py`. Il exécute chaque fichier `tests/test_*.py` séparément avec timeout de 30 secondes pour identifier immédiatement un fichier de test sensible à l'état post-chaîne.

Résultat attendu : `LOT 9-quater REQUIRED CHAIN: PASS`, `DIAGNOSE PYTEST AFTER CHAIN: PASS`, chaîne obligatoire exacte `rc=0`, pytest complet passé séparément, aucun skipped, aucun deselected, catalogue stable.

## Addendum Lot 9-quinquies — Terminaison propre pytest / CI finale

Le Lot 9-quinquies corrige le rejet résiduel du Lot 9-quater. Le script `run_required_chain_until_lot9.sh` affichait `PASS`, et le pytest complet pouvait afficher son résumé, mais le processus ne rendait pas toujours la main au shell dans l'environnement d'audit.

La correction supprime la logique de force-exit pytest dans `tests/conftest.py`, supprime toute utilisation réelle de la variable de contournement de force-exit, et laisse pytest terminer naturellement. La chaîne requise garde uniquement un pytest smoke subset borné. Le pytest complet reste exécuté séparément par la commande CI obligatoire.

Les preuves de retour shell sont explicites : `PYTEST_DONE`, `REQUIRED_CHAIN_DONE` et `EXACT_CHAIN_DONE` sont affichés après les commandes concernées. La chaîne complète obligatoire retourne `rc=0` sous timeout, sans démarrer le Lot 10 et sans modifier la logique Backtest Replay V0.

## Addendum Lot 9-sexies — Terminaison réelle du process tree CI

Le Lot 9-sexies corrige le rejet résiduel du Lot 9-quinquies. Le problème n'était plus un échec pytest mais un processus ou descripteur enfant pouvant rester vivant après la chaîne requise.

La chaîne `scripts/run_required_chain_until_lot9.sh` utilise désormais un smoke subset strictement passif : il lit les artefacts et vérifie des invariants sans relancer de subprocess métier, sans relancer `run_lot9_backtest_replay.py`, sans orchestrateur imbriqué et sans pytest imbriqué. Le test actif de stabilité du catalogue a été retiré du smoke subset et remplacé par `tests/test_lot9_dataset_catalog_static.py`.

Un diagnostic de process tree a été ajouté avec `scripts/diagnose_lingering_processes.py`. Le script requis n'affiche `LOT 9-sexies REQUIRED CHAIN: PASS` qu'après vérification qu'aucun enfant direct ne reste vivant.

Les preuves de retour shell sont `PYTEST_DONE`, `REQUIRED_CHAIN_DONE` et `EXACT_CHAIN_DONE`. Le Backtest Replay V0 reste inchangé : décisions `WAIT`, aucun ordre, aucun fill, `pnl_total=0` et aucune fuite temporelle.

## Transition vers Lot 10

Le Lot 10 démarre uniquement après validation du Lot 9-sexies. Le Backtest Replay V0 reste inchangé : il fournit des steps `WAIT` neutres que le Lot 10 utilise uniquement pour estimer des coûts hypothétiques non décisionnels.
