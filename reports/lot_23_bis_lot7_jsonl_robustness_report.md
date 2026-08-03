# Lot 23-bis Lot 7 JSONL Robustness Report

Le Lot 23-bis existe parce que la preparation obligatoire du Lot 24 a echoue sur un `JSONDecodeError` intermittent pendant `scripts/build_lot7_market_state.py`.

Cause retenue :

- `build_lot7_market_state.py` ecrivait le JSONL Lot 7 en place ;
- `upsert_catalog` relisait ensuite ce meme fichier de sortie pour extraire `start_timestamp` et `end_timestamp` ;
- sur un workspace partage, une reconstruction concurrente pouvait tronquer puis reecrire le meme JSONL pendant cette relecture ;
- le symptome observé etait donc un `json.decoder.JSONDecodeError` dans `src/crypto_quant_bot/market_state/loader.py`.

Correction appliquee :

- lecture JSONL robuste avec message localise chemin + ligne ;
- ecriture JSONL atomique `tmp -> replace` ;
- suppression de la relecture de sortie Lot 7 pour l'upsert du catalogue ;
- ajout d'un diagnostic cible `scripts/diagnose_lot7_market_state_jsonl.py`.

Garantie de perimetre :

- l'archive V1 gelee reste intacte ;
- aucun artefact Lot 24 n'est cree ;
- le Lot 24 n'est pas commence dans ce correctif.
