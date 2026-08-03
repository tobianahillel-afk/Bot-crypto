# Lot 22-bis — Lot16 Source Catalog Checksum Stability

## Why This Lot Exists

Le Lot 22-bis existe parce que la preparation obligatoire du Lot 23 a echoue dans `scripts/diagnose_exact_chain_return_shell.py` avec `source_catalog_checksum mismatch` pendant `scripts/validate_lot16.py`.

## Root Cause

- `run_lot16_reproducibility_manifest.py` calcule le `source_catalog_checksum` avant les upserts Lot 16 dans `data/audit/dataset_catalog.json`.
- `validate_lot16.py` recalcule le checksum sur le catalogue courant, donc apres upserts et apres enrichissements V2 du catalogue.
- la normalisation initiale etait trop fragile si des entrees futures ou des entrees Lot 16 auto-referencees restaient visibles dans le perimetre checksum.

## Applied Fix

- la normalisation du `DatasetCatalog` a ete centralisee autour d'un perimetre historique explicite ;
- le checksum Lot 16 ne conserve que les enregistrements dont les hints de lot restent `<= 15` ;
- les hints de lot sont detectes de maniere deterministe dans plusieurs champs (`dataset_id`, `dataset_name`, `data_version`, `source`, `validation_status`, `lineage_id`, `path`, `lot`, `lot_id`, `source_lot`) ;
- les scripts de run et de validation Lot 16 utilisent exactement la meme fonction de checksum ;
- la logique Lot 17 de `dataset_catalog_checksum` a ete alignee sur la meme normalisation, avec borne historique `<= 16`.

## Safety Result

- `scripts/diagnose_exact_chain_return_shell.py` repasse ;
- `scripts/diagnose_exact_chain_until_lot22.py` repasse ;
- l'archive V1 gelee reste strictement inchangee ;
- aucun artefact Lot 23 n'a ete cree ;
- le projet reste local, offline, no-trading et non executable.
