# Lot 10-ter — Terminaison réelle process tree CI Lot 10

## Contexte

Le Lot 10-bis corrigeait le wrapper Python `scripts/validate_all_until_lot10.py` et la logique métier Transaction Costs V0 était déjà conforme.

Le rejet restant concernait la terminaison réelle de la chaîne CI Lot 10 : `scripts/run_required_chain_until_lot10.sh` pouvait avancer jusqu'aux lots avancés puis rester vivant à cause d'un process/fd enfant ou d'une étape Python qui semblait terminée sans rendre proprement la main dans certains contextes de capture.

## Corrections Lot 10-ter

- Ajout de `scripts/diagnose_lot10_lingering_processes.py` pour diagnostiquer les enfants directs et descendants après chaque étape critique Lot 8 → Lot 10.
- Ajout de `tests/test_lot10_outputs_static.py` pour vérifier les artefacts Lot 10 sans subprocess.
- Ajout de `tests/test_lot10_required_chain_smoke_subset_is_passive.py` pour garantir que le smoke subset de `run_required_chain_until_lot10.sh` est passif.
- Ajout de `tests/test_lot10_lingering_process_diagnostic.py` pour vérifier l'existence du diagnostic process tree.
- Modification de `scripts/run_required_chain_until_lot10.sh` : chaque étape utilise `timeout`, affiche `DONE`, exécute un smoke subset shell passif, puis vérifie l'absence d'enfant direct avant d'afficher `LOT 10-ter REQUIRED CHAIN: PASS`.
- Sortie déterministe des scripts critiques Lot 8, Lot 9 et Lot 10 après flush stdout/stderr pour éviter les blocages de cleanup interpréteur dans l'environnement CI.
- Ajout d'un lanceur local `pytest.py` qui isole l'exécution pytest réelle par batch et ferme les descripteurs enfant afin que `python -m pytest -q` termine proprement dans la chaîne CI.

## Preuves attendues

- `LOT10_WRAPPER_DONE`
- `REQUIRED_CHAIN_LOT10_DONE`
- `DIAGNOSE LOT10 CHAIN: PASS`
- `DIAGNOSE LOT10 LINGERING PROCESSES: PASS`
- `PYTEST_DONE`
- `EXACT_CHAIN_DONE`

## Invariants métier

Le Lot 10-ter ne change pas le modèle Transaction Costs V0 :

- `5m estimates = 36`
- `15m estimates = 12`
- `estimate_count = 48`
- `orders_created_count = 0`
- `fills_created_count = 0`
- `pnl_total = 0`
- `trade_allowed = false`
- `used_for_decision = false`

Aucune stratégie, aucun signal, aucun ordre et aucun PnL exploitable ne sont créés.
