# Lot 23-ter Lot 10 Writer Robustness Report

Le Lot 23-ter existe parce que la preparation obligatoire du Lot 24 a expose un `FileNotFoundError` intermittent pendant `scripts/run_lot10_transaction_costs.py`.

Cause probable :

- `src/crypto_quant_bot/costs/writer.py` utilisait un nom temporaire fixe partage de la forme `.<target>.tmp` ;
- sur un workspace partage comme `/mnt/hgfs`, deux ecritures rapprochees peuvent viser le meme tmp ;
- une ecriture peut alors remplacer ou nettoyer ce tmp pendant qu'une autre pense encore en etre proprietaire ;
- le symptome devient un `FileNotFoundError` au moment du `replace`.

Correction appliquee :

- remplacement des tmp fixes par des tmp uniques `.<stem>.<pid>.<uuid><suffix>.tmp` ;
- creation du parent avant ecriture ;
- ecriture complete, `flush`, `fsync`, puis `os.replace` atomique dans le meme dossier ;
- nettoyage best-effort uniquement du tmp de l'ecriture courante ;
- ajout d'un diagnostic cible Lot 10 pour verifier les reruns, les counts et l'absence de tmp fixe residuel.

Garantie de perimetre :

- l'archive V1 gelee reste intacte ;
- aucun artefact Lot 24 n'est cree ;
- le Lot 24 n'est pas commence dans ce correctif.
