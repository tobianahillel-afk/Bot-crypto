# Lot 9-quinquies — Terminaison propre pytest / CI finale

## Résumé

Le Lot 9-quinquies ne modifie pas le Backtest Replay Engine V0. Il corrige uniquement la terminaison CI finale après le rejet du Lot 9-quater.

Le Lot 9-quater affichait bien `LOT 9-quater REQUIRED CHAIN: PASS` et le pytest complet pouvait afficher son résumé, mais certains processus ne rendaient pas toujours la main au shell dans l'environnement d'audit.

## Cause corrigée

La cause principale était une logique de terminaison forcée dans `tests/conftest.py` et l'utilisation de la variable `ancienne variable de force-exit pytest` dans les scripts CI. Cette logique pouvait masquer ou perturber la terminaison naturelle de pytest.

## Corrections appliquées

```text
- suppression de os._exit dans tests/conftest.py ;
- suppression de signal.alarm dans tests/conftest.py ;
- suppression des hooks pytest_sessionfinish / pytest_terminal_summary / pytest_unconfigure ;
- suppression de ancienne variable de force-exit pytest dans les scripts CI et les tests ;
- run_required_chain_until_lot9.sh lance uniquement un pytest smoke subset borné ;
- diagnose_pytest_after_chain.py vérifie les tests fichier par fichier sans variable de force-exit ;
- ajout de tests statiques anti-hack CI ;
- ajout des marqueurs de retour shell PYTEST_DONE, REQUIRED_CHAIN_DONE et EXACT_CHAIN_DONE dans les commandes de validation.
```

## Preuves de retour shell

```text
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
→ 120 passed
→ PYTEST_DONE
→ rc=0

timeout 120s bash -lc 'bash scripts/run_required_chain_until_lot9.sh; echo REQUIRED_CHAIN_DONE'
→ LOT 9-quinquies REQUIRED CHAIN: PASS
→ REQUIRED_CHAIN_DONE
→ rc=0

timeout 300s bash -lc '<chaîne complète obligatoire> && echo EXACT_CHAIN_DONE'
→ 120 passed
→ EXACT_CHAIN_DONE
→ rc=0
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

## Limites

Le Lot 9-quinquies ne commence pas le Lot 10. Il ne crée aucune stratégie, aucun PnL exploitable, aucun paper trading, aucune exécution live, aucun signal LONG/SHORT, aucun target, aucun label, aucun future_*, aucun appel API et aucun WebSocket.
