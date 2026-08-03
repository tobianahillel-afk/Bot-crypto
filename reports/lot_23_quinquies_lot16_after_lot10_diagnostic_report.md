# Lot 23-quinquies Lot 16 After Lot 10 Diagnostic Report

Le Lot 23-quinquies existe parce que la preparation obligatoire du Lot 24 a montre qu'un diagnostic de preparation pouvait desynchroniser le manifeste Lot 16.

Cause racine constatee :

- `scripts/diagnose_lot10_transaction_cost_writer.py` relancait `scripts/run_lot10_transaction_costs.py` par defaut ;
- ce rerun reecrivait les artefacts Lot 10 ainsi que `data/audit/dataset_catalog.json` ;
- `scripts/diagnose_lot16_source_catalog_checksum.py` comparait ensuite le manifeste Lot 16 deja ecrit au catalogue courant, sans regeneration automatique du manifeste ;
- le diagnostic Lot 10 devenait donc mutant, ce qui cassait la preparation sequentielle du Lot 24.

Correction appliquee :

- le diagnostic Lot 10 est maintenant non-mutant par defaut ;
- il lit les artefacts existants, execute `validate_lot10.py`, verifie les counts attendus et l'absence de tmp fixe residuel ;
- il surveille aussi `dataset_catalog.json` et `reproducibility_manifest_lot16.json` pour garantir qu'aucune mutation ne survient en mode par defaut ;
- un mode explicite `--rerun` est conserve pour une regeneration volontaire et assumee des artefacts Lot 10.

Garantie de perimetre :

- l'archive V1 gelee reste intacte ;
- aucun artefact Lot 24 n'est cree ;
- le Lot 24 n'est pas commence dans ce correctif.
