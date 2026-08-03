# Lot 10-quater — Suppression des hacks pytest/os._exit et CI propre finale

Le Lot 10 était conforme côté métier Transaction Costs V0, mais le Lot 10-ter avait introduit un fichier local `pytest.py` à la racine. Ce fichier shadowait le vrai package pytest lors de `python -m pytest -q` et utilisait des mécanismes de terminaison forcée.

## Corrections

- Suppression complète du fichier local `pytest.py`.
- Ajout du diagnostic `scripts/diagnose_pytest_resolution.py` pour vérifier que `pytest` résout vers le package installé.
- Suppression de `os._exit(...)` des scripts actifs Lot 8 / Lot 9 / Lot 10.
- Absence de `signal.alarm` et de `CQB_DISABLE_PYTEST_FORCE_EXIT` dans le code actif.
- Renforcement des tests statiques anti-hack CI.
- Renforcement de `scripts/run_required_chain_until_lot10.sh` avec un message `LOT 10-quater REQUIRED CHAIN: PASS` uniquement après les vérifications finales.

## Preuves attendues

- `DIAGNOSE PYTEST RESOLUTION: PASS`
- `PYTEST_DONE`
- `LOT10_WRAPPER_DONE`
- `REQUIRED_CHAIN_LOT10_DONE`
- `EXACT_CHAIN_DONE`

## Invariants

Le Lot 10-quater ne modifie pas la logique métier Transaction Costs V0 et ne crée aucun ordre, aucun fill, aucun PnL exploitable, aucun signal LONG/SHORT, aucun target, label ou future_*.
