# Acceptance Criteria — Lot 4

Le Lot 4 est validé si :

- les validations des Lots 0, 1, 2 et 3 passent ;
- `build_lot4_volume_vwap.py` passe ;
- `validate_lot4.py` passe ;
- les contracts `volume_profile.py` et `vwap.py` existent ;
- le module `src/crypto_quant_bot/volume/` existe ;
- les datasets Volume Profile, VWAP, Anchors et Anchored VWAP sont générés ;
- le POC existe pour 5m et 15m ;
- les `volume_share` somment environ à 1.0 ;
- chaque anchor contient `selected_at` et `usable_from` ;
- les anchors pivot respectent `usable_from >= selected_at >= anchor_time` ;
- aucun point Anchored VWAP n'est émis avant `usable_from` ;
- `used_for_decision = false` pour tous les objets Lot 4 ;
- aucun dataset ne contient LONG/SHORT, target, label ou `future_*` ;
- les invariants défensifs restent inchangés.

## Critères Lot 4-bis — Robustesse validation

Le Lot 4-bis est validé si :

- `validate_lot3.py` termine en moins de 60 secondes avec returncode 0 ;
- `validate_lot4.py` termine en moins de 60 secondes avec returncode 0 ;
- `validate_lot4.py` ne lance pas de validation imbriquée longue ;
- les appels subprocess conservés dans l'orchestrateur ont des timeouts explicites ;
- `validate_all_until_lot4.py` termine en moins de 300 secondes ;
- les sorties d'erreur des subprocess sont affichées en cas d'échec ;
- les `TimeoutExpired` sont gérés proprement ;
- les validations ne génèrent pas de nombreux `reports/replay_*.json` aléatoires ;
- le replay de validation est stable ou stocké dans `data/audit/replay_validation/` ;
- tous les invariants défensifs restent inchangés ;
- aucun signal LONG/SHORT, target, label ou `future_*` n'est introduit.

## Critères Lot 4-quinquies — Robustesse orchestrateur validation

Le Lot 4-quinquies est validé si :

- `validate_lot3.py` termine en moins de 60 secondes avec returncode 0 ;
- `validate_lot4.py` termine en moins de 60 secondes avec returncode 0 ;
- `validate_all_until_lot4.py` termine en moins de 300 secondes avec returncode 0 ;
- l'orchestrateur n'utilise pas `capture_output=True` ;
- l'orchestrateur streame stdout/stderr directement ;
- les scripts projet sont exécutés avec timeout de 60 secondes ;
- `python -m pytest -q` est exécuté avec timeout de 180 secondes ;
- `CQB_SKIP_NESTED_PYTEST=1` permet de sauter pytest pendant un test de l'orchestrateur ;
- un test exécute réellement `validate_all_until_lot4.py` avec `CQB_SKIP_NESTED_PYTEST=1` ;
- le message final `LOT 4-quinquies VALIDATION: PASS` apparaît ;
- tous les invariants défensifs restent inchangés ;
- aucun signal LONG/SHORT, target, label ou `future_*` n'est introduit.

## Lot 4-quinquies acceptance criteria

Lot 4-quinquies is accepted only if:

- `scripts/validate_all_until_lot4.sh` exists and uses explicit `timeout` commands.
- `scripts/validate_all_until_lot4.py` only delegates to the shell orchestrator.
- `scripts/validate_lot3.py` and `scripts/validate_lot4.py` remain direct validations and do not orchestrate previous lots.
- `timeout 60s python scripts/validate_lot3.py` passes.
- `timeout 60s python scripts/validate_lot4.py` passes.
- `timeout 300s python scripts/validate_all_until_lot4.py` passes.
- `python -m pytest -q` passes without skipped orchestrator proof.

## Lot 4-quinquies — validation orchestrée définitive

- `CQB_ORCHESTRATOR_MODE=fast` est le mode par défaut de `scripts/validate_all_until_lot4.sh`.
- Le mode fast vérifie les artefacts clés et lance les validations Lot 0 à Lot 4 sans rebuild lourd.
- `CQB_ORCHESTRATOR_MODE=full` conserve le rebuild complet explicite.
- `scripts/validate_all_until_lot4.py` reste un wrapper Python minimal vers le script Bash.
- Le test orchestrateur lance réellement le wrapper avec `CQB_SKIP_NESTED_PYTEST=1` et ne skippe plus.
- La sortie attendue est `LOT 4-quinquies VALIDATION: PASS`.


## Lot 4-sexies acceptance criteria

- `pyproject.toml` must not contain `-k not test_validate_all_until_lot4_executes_without_nested_pytest`.
- `python -m pytest -q` must execute `tests/test_aaa_lot4_validate_all_terminates.py::test_validate_all_until_lot4_executes_without_nested_pytest`.
- The orchestrator must run in fast mode with `CQB_SKIP_NESTED_PYTEST=1`.
- The orchestrator must return code 0 and print `LOT 4-sexies VALIDATION: PASS`.
- The final pytest run must have no skipped or deselected orchestrator test.

Lot 4-sexies final behavior: fast orchestrator validation does not run nested pytest; the default `python -m pytest -q` run executes the orchestrator test directly, with 0 skipped and 0 deselected tests.

Lot 4-sexies CI detail: `pyproject.toml` has no `-k` deselection filter. It keeps `-s` to avoid capture-related hangs while still executing the orchestrator test by default.

Lot 4-sexies pytest exit stabilization: pytest records the real exit status and forces process termination after unconfigure to avoid post-summary hangs in the audit environment.


## Lot 4-septies — Suppression des validations imbriquées

Lot 4-septies corrige le dernier blocage CI : les validations individuelles ne doivent plus s'appeler entre elles. `scripts/validate_lot2.py` ne relance plus `validate_lot0.py` ni `validate_lot1.py`, et aucun `validate_lot1.py` / `validate_lot2.py` / `validate_lot3.py` / `validate_lot4.py` ne contient `capture_output=True` ni d'appel à un autre script de validation de lot.

L'orchestrateur `validate_all_until_lot4.py` / `.sh` est désormais le seul responsable de l'enchaînement complet multi-lots. Le message final attendu est `LOT 4-septies VALIDATION: PASS`.
