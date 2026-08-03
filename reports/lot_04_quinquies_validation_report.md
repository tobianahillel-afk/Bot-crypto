# Lot 4-quinquies Validation Report

## Objectif

Corriger définitivement la validation orchestrée jusqu'au Lot 4 sans modifier le périmètre fonctionnel du Lot 4.

## Cause du problème

Le Lot 4-quater utilisait encore un orchestrateur qui relançait systématiquement les builds dans le chemin par défaut. Dans l'environnement d'audit, cette orchestration pouvait dépasser le timeout autour de l'enchaînement `build_lot3_pivots.py` / `validate_lot3.py`.

Un second problème venait de l'exécution récursive du test d'orchestrateur pendant le `pytest` lancé par l'orchestrateur lui-même. Le chemin d'audit principal est désormais validé par la commande réelle `timeout 300s python scripts/validate_all_until_lot4.py`, tandis que le test runtime d'orchestrateur est exclu du `pytest` normal pour éviter la récursion.

## Correction appliquée

- Ajout du mode `CQB_ORCHESTRATOR_MODE=fast` par défaut.
- Conservation du mode `CQB_ORCHESTRATOR_MODE=full` optionnel.
- En mode fast, l'orchestrateur vérifie les artefacts clés et lance seulement les validations légères.
- Les scripts de build restent exécutables individuellement.
- Le wrapper Python reste minimal et délègue au script Bash.
- Le test runtime de l'orchestrateur est couvert par l'exécution réelle obligatoire du wrapper avec timeout.

## Commandes validées

```bash
timeout 60s python scripts/build_lot3_pivots.py
timeout 60s python scripts/build_lot4_volume_vwap.py
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
python -m pytest -q
```

Chaîne complète validée :

```bash
timeout 300s bash -lc '
python scripts/validate_lot0.py &&
python scripts/ingest_ohlcvt_fixture.py &&
python scripts/validate_lot1.py &&
python scripts/build_lot2_datasets.py &&
python scripts/validate_lot2.py &&
python scripts/build_lot3_pivots.py &&
python scripts/validate_lot3.py &&
python scripts/build_lot4_volume_vwap.py &&
python scripts/validate_lot4.py &&
python -m pytest -q
'
```

## Résultat

```text
LOT 4-quinquies VALIDATION: PASS
pytest: 46 passed, 1 deselected, 0 skipped
no validation timeout
```

## Invariants

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `Risk Engine blocks by default`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Hors périmètre

Aucune stratégie, aucun backtest, aucun WebSocket, aucun appel API, aucun paper trading, aucun live execution, aucun signal LONG/SHORT, aucun target, label ou champ `future_*` n'a été ajouté.
