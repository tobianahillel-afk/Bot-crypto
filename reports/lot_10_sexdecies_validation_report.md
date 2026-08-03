# Lot 10-sexdecies — Diagnostics naturels sans Popen/process group

## Résumé

Le Lot 10-sexdecies ne modifie pas la logique métier Transaction Costs V0. Il corrige uniquement les diagnostics de chaîne qui pouvaient imprimer `PASS` mais ne pas rendre réellement la main à cause d'une gestion manuelle de process tree.

## Cause corrigée

Le Lot 10-quindecies corrigeait `scripts/validate_lot4.py`. L'audit chef de projet a ensuite montré que `scripts/diagnose_lot5_validate_after_chain.py` pouvait afficher :

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
```

mais rester vivant jusqu'au timeout externe.

La cause était structurelle dans les diagnostics : usage de `subprocess.Popen`, `start_new_session=True`, gestion manuelle de process group, signaux de terminaison et `process.wait()`. Ces mécanismes ont été remplacés par une exécution naturelle basée sur `subprocess.run(..., timeout=..., check=False)`.

## Corrections appliquées

Diagnostics corrigés :

```text
scripts/diagnose_lot4_validate_after_chain.py
scripts/diagnose_lot5_validate_after_chain.py
scripts/diagnose_lot7_build_after_chain.py
scripts/diagnose_lot8_no_lookahead_after_chain.py
scripts/diagnose_exact_chain_until_lot10.py
scripts/diagnose_after_pytest_lingering.py
scripts/diagnose_exact_chain_return_shell.py
scripts/diagnose_lingering_processes.py
```

Chaque diagnostic utilise maintenant :

```python
result = subprocess.run(
    command,
    cwd=ROOT,
    timeout=timeout_seconds,
    check=False,
)
```

Les diagnostics affichent un marqueur `BEFORE:<step>`, puis un marqueur `AFTER:<step>:rc=<code>:duration_seconds=<duration>`, retournent `124` sur timeout et n'impriment `PASS` qu'après retour réel de toutes les étapes.

## Garde statique ajoutée

```text
tests/test_diagnostics_use_subprocess_run_only.py
```

Ce test vérifie que les diagnostics actifs n'utilisent plus de gestion manuelle instable : pas de `subprocess.Popen`, pas de `start_new_session=True`, pas de `os.killpg`, pas de `SIGTERM/SIGKILL`, pas de `process.wait()`, pas de capture PIPE, pas de DEVNULL, pas de `os._exit`, pas de `signal.alarm`, pas de `close_standard_streams`, pas de `os.dup2`.

## Commandes exécutées

```bash
timeout 60s python scripts/diagnose_pytest_resolution.py
timeout 300s python scripts/diagnose_lot4_validate_after_chain.py
timeout 300s python scripts/diagnose_lot5_validate_after_chain.py
timeout 300s python scripts/diagnose_lot7_build_after_chain.py
timeout 300s python scripts/diagnose_lot8_no_lookahead_after_chain.py
timeout 300s python scripts/diagnose_exact_chain_until_lot10.py
timeout 300s python scripts/diagnose_after_pytest_lingering.py
timeout 300s python scripts/diagnose_exact_chain_return_shell.py
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
```

Commande exacte Lot 0 → Lot 10 exécutée :

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
python scripts/run_lot10_transaction_costs.py &&
python scripts/validate_lot10.py &&
python -m pytest -q &&
echo EXACT_CHAIN_DONE
'
```

## Résultats

```text
DIAGNOSE PYTEST RESOLUTION: PASS
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
166 passed
rc=0
```

## Invariants conservés

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

Aucune stratégie, aucun ordre réel, aucun ordre simulé exploitable, aucun PnL exploitable, aucun paper trading, aucun signal LONG/SHORT, aucun target/label/future_*, aucun appel API et aucun WebSocket n'a été ajouté.
