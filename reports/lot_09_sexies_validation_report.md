# Lot 9-sexies — Terminaison réelle du process tree CI

## Contexte

Le Lot 9-quinquies supprimait les hacks de terminaison pytest et prouvait que pytest pouvait afficher `PYTEST_DONE`. L'audit a toutefois montré qu'un processus ou un descripteur pouvait rester vivant après la chaîne requise, même après l'affichage de `LOT 9-quinquies REQUIRED CHAIN: PASS` et `REQUIRED_CHAIN_DONE`.

## Correction appliquée

Le Lot 9-sexies ne modifie pas la logique métier Backtest Replay V0. Il corrige uniquement la terminaison réelle du process tree CI.

Corrections principales :

```text
- ajout de scripts/diagnose_lingering_processes.py ;
- remplacement du smoke subset actif par un smoke subset strictement passif ;
- retrait de test_lot9_dataset_catalog_stability.py du smoke subset de run_required_chain_until_lot9.sh ;
- ajout de tests/test_lot9_dataset_catalog_static.py ;
- ajout de tests/test_lot9_required_chain_smoke_subset_is_passive.py ;
- conversion du test dataset_catalog_stability en contrôle sans subprocess ;
- remplacement des captures subprocess par des fichiers temporaires dans les tests smoke orchestrateurs ;
- ajout d'une vérification finale d'absence d'enfant direct dans run_required_chain_until_lot9.sh ;
- affichage de LOT 9-sexies REQUIRED CHAIN: PASS uniquement après le contrôle d'absence d'enfant direct.
```

## Preuves de terminaison

```text
PYTEST_DONE : affiché
REQUIRED_CHAIN_DONE : affiché
EXACT_CHAIN_DONE : affiché
DIAGNOSE LINGERING PROCESSES: PASS : affiché
```

## Résultats

```text
LOT 9-sexies REQUIRED CHAIN: PASS
DIAGNOSE PYTEST AFTER CHAIN: PASS
DIAGNOSE LINGERING PROCESSES: PASS
LOT 9 ORCHESTRATED VALIDATION: PASS
LOT 9 ORCHESTRATOR SMOKE: PASS
pytest complet : PASS
```

## Invariants

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

Aucune stratégie, aucun PnL exploitable, aucun paper trading, aucun signal LONG/SHORT, aucun target, aucun label, aucun `future_*`, aucun appel API et aucun WebSocket n'ont été ajoutés.
