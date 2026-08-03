# Lot 9-quater — Chaîne CI finale sans pytest bloquant

## Contexte

Le Lot 9-ter a stabilisé les validations fonctionnelles, les scripts Lot 8/Lot 9 et `dataset_catalog.json`. Le rejet restant venait de `scripts/run_required_chain_until_lot9.sh`, qui lançait encore un `python -m pytest -q` complet à la fin. En audit CI, ce pytest complet pouvait rester bloqué après toutes les étapes fonctionnelles pourtant validées.

## Correction appliquée

Le Lot 9-quater sépare clairement :

```text
1. chaîne fonctionnelle complète avec timeouts par étape ;
2. pytest smoke subset borné dans run_required_chain_until_lot9.sh ;
3. pytest complet lancé séparément par la commande CI obligatoire ;
4. diagnostic pytest fichier par fichier via scripts/diagnose_pytest_after_chain.py.
```

`run_required_chain_until_lot9.sh` ne lance plus le pytest complet. Il lance uniquement un sous-ensemble smoke borné :

```text
tests/test_lot9_run_outputs.py
tests/test_lot9_invariants.py
tests/test_lot9_dataset_catalog_stability.py
tests/test_validation_no_nested_subprocess.py
tests/test_validation_wrappers_no_execv.py
```

## Diagnostic ajouté

`scripts/diagnose_pytest_after_chain.py` exécute chaque fichier `tests/test_*.py` séparément avec un timeout de 30 secondes et affiche le fichier courant avant exécution. Il permet d'isoler un éventuel test bloquant après une chaîne longue sans relancer une validation complète ni orchestrateur.

## Invariants

Le Lot 9-quater ne modifie pas le Backtest Replay V0 et ne crée aucune stratégie, aucun PnL exploitable, aucun paper trading, aucun signal LONG/SHORT, aucun target, aucun label, aucun `future_*`, aucun appel API et aucun WebSocket.

Les invariants restent :

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

## Résultats attendus

```text
LOT 9-quater REQUIRED CHAIN: PASS
DIAGNOSE PYTEST AFTER CHAIN: PASS
LOT 9 ORCHESTRATED VALIDATION: PASS
LOT 9 ORCHESTRATOR SMOKE: PASS
pytest: all tests passed
no validation timeout
no skipped orchestrator test
no deselected orchestrator test
dataset_catalog stable
```
