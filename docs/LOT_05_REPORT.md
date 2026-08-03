# Lot 5 Report

Lot 5 adds Volatility, ATR, Range and Compression/Expansion analysis. It produces analysis datasets only and does not create trading signals, strategies, backtests, WebSocket ingestion, API calls, ML, AI/news, paper trading or live execution.

Outputs are generated under `data/gold/` and reports under `reports/`.

## Lot 5-bis — Robustesse CI finale

Lot 5-bis corrige la chaîne de validation complète. Le Lot 5 était fonctionnellement correct, mais la CI complète pouvait rester bloquée car `validate_lot1.py` relançait encore la matérialisation Lot 1 via subprocess.

Corrections appliquées :

- `validate_lot1.py` est désormais une validation directe.
- Les scripts `validate_lot1.py` à `validate_lot5.py` ne doivent plus appeler de build script, ingest script ou autre validate script.
- L’orchestrateur `validate_all_until_lot5.sh` reste le seul responsable de l’enchaînement multi-lots.
- Le test orchestrateur Lot 5 exécute réellement le wrapper Python en mode fast avec `CQB_SKIP_NESTED_PYTEST=1`.
- La chaîne complète demandée termine sans timeout.

Résultat : `LOT 5-ter ORCHESTRATED VALIDATION: PASS`.

## Lot 5-ter

Lot 5-ter stabilizes CI by adding `CQB_ORCHESTRATOR_MODE=smoke` for pytest. The full validation remains available outside pytest through `scripts/validate_all_until_lot5.py` in fast/full mode. Pytest now checks the orchestrator through a quick smoke path and does not rerun heavy validations.

Expected outputs:

```text
LOT 5-ter ORCHESTRATED VALIDATION: PASS
LOT 5-ter ORCHESTRATOR SMOKE: PASS
```
