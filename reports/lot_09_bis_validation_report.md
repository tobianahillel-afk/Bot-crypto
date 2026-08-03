# Lot 9-bis Validation Report — Robustesse orchestrateur / CI finale

## Contexte

Le Lot 9 était fonctionnel côté replay : `run_lot9_backtest_replay.py`, `validate_lot9.py` et `python -m pytest -q` passaient isolément. Le rejet d'audit venait de la robustesse CI : l'orchestrateur `validate_all_until_lot9.py` ne terminait pas de manière fiable dans l'environnement d'audit.

## Cause corrigée

Les wrappers Python `validate_all_until_lot5.py` à `validate_all_until_lot9.py` utilisaient `os.execv(...)` pour remplacer le processus courant par le shell. Ce comportement était fragile en CI/audit parce qu'il rendait la terminaison et le statut de sortie moins explicites dans certains environnements supervisés.

Les orchestrateurs shell Lots 6 à 9 lançaient aussi un pytest imbriqué en mode fast. Le pytest est désormais exécuté séparément par la chaîne CI obligatoire, ce qui évite les récursions et blocages liés aux tests d'orchestrateurs.

## Corrections appliquées

- Suppression de `os.execv` dans `scripts/validate_all_until_lot5.py` à `scripts/validate_all_until_lot9.py`.
- Remplacement par un wrapper minimal `subprocess.run([...], timeout=300, check=False)` sans capture stdout/stderr.
- Ajout ou confirmation de `exit 0` explicite dans les orchestrateurs shell Lots 5 à 9.
- Orchestrateurs shell Lots 6 à 9 : les validations directes restent exécutées, mais pytest est explicitement laissé à la commande CI séparée `python -m pytest -q`.
- Tests d'orchestrateurs conservés en mode `smoke` uniquement avec `CQB_ORCHESTRATOR_MODE=smoke` et `CQB_SKIP_NESTED_PYTEST=1`.
- Ajout du test `tests/test_validation_wrappers_no_execv.py`.
- Extension de `tests/test_validation_no_nested_subprocess.py` à `validate_lot9.py`.

## Validation attendue

Les commandes critiques doivent terminer avec `rc=0` sans timeout :

```bash
timeout 300s python scripts/validate_all_until_lot9.py
```

et :

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
python scripts/build_lot5_volatility.py &&
python scripts/validate_lot5.py &&
python scripts/build_lot6_regime.py &&
python scripts/validate_lot6.py &&
python scripts/build_lot7_market_state.py &&
python scripts/validate_lot7.py &&
python scripts/audit_lot8_feature_registry.py &&
python scripts/audit_lot8_no_lookahead.py &&
python scripts/validate_lot8.py &&
python scripts/run_lot9_backtest_replay.py &&
python scripts/validate_lot9.py &&
python -m pytest -q
'
```

## Invariants maintenus

Le Lot 9-bis ne modifie pas la logique Backtest Replay V0 et ne commence pas le Lot 10.

Les invariants restent :

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

Aucune stratégie, aucun signal LONG/SHORT, aucun target, aucun label, aucun `future_*`, aucun paper trading, aucun appel API et aucun WebSocket n'ont été ajoutés.

## Résultats exécutés Lot 9-bis

```text
timeout 60s python scripts/run_lot9_backtest_replay.py -> LOT 9 BACKTEST REPLAY: PASS, rc=0
timeout 60s python scripts/validate_lot9.py -> LOT 9 VALIDATION: PASS, rc=0
timeout 300s python scripts/validate_all_until_lot9.py -> LOT 9 ORCHESTRATED VALIDATION: PASS, rc=0
CQB_ORCHESTRATOR_MODE=smoke CQB_SKIP_NESTED_PYTEST=1 timeout 30s python scripts/validate_all_until_lot9.py -> LOT 9 ORCHESTRATOR SMOKE: PASS, rc=0
python -m pytest -q -> 114 passed, rc=0
chaîne complète obligatoire -> rc=0
```

La chaîne complète obligatoire confirme que les validations Lots 0 à 9, les audits Lot 8, le replay Lot 9 et pytest passent sans timeout dans le processus CI final.
