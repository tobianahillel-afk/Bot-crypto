# Acceptance Criteria — Lot 5

- Build script `scripts/build_lot5_volatility.py` exists and outputs `LOT 5 VOLATILITY BUILD: PASS`.
- Validation script `scripts/validate_lot5.py` exists and outputs `LOT 5 VALIDATION: PASS`.
- Orchestrator `scripts/validate_all_until_lot5.py` / `.sh` exists and outputs `LOT 5-ter ORCHESTRATED VALIDATION: PASS`.
- Volatility and range state contracts exist.
- 5m datasets have 36 rows and 15m datasets have 12 rows.
- No `future_*`, `target`, or `label` fields are produced.
- `used_for_decision=false` for all Lot 5 objects.
- Defensive invariants remain unchanged.

## Critères additionnels Lot 5-bis

- `validate_lot1.py` ne doit pas utiliser `subprocess.run`.
- `validate_lot1.py` ne doit pas relancer l’étape d’ingestion.
- `validate_lot1.py` à `validate_lot5.py` doivent être des validateurs directs.
- Aucun `validate_lotX.py` ne doit appeler un build script, ingest script ou autre validate script.
- `tests/test_validation_no_nested_subprocess.py` doit vérifier cette règle.
- `tests/test_lot5_validate_all_terminates.py` doit exécuter l’orchestrateur Lot 5 avec timeout.
- La chaîne complète CI doit terminer sous 300 secondes.
- `python -m pytest -q` doit passer sans skipped ni deselected.

## Lot 5-ter

Lot 5-ter stabilizes CI by adding `CQB_ORCHESTRATOR_MODE=smoke` for pytest. The full validation remains available outside pytest through `scripts/validate_all_until_lot5.py` in fast/full mode. Pytest now checks the orchestrator through a quick smoke path and does not rerun heavy validations.

Expected outputs:

```text
LOT 5-ter ORCHESTRATED VALIDATION: PASS
LOT 5-ter ORCHESTRATOR SMOKE: PASS
```
