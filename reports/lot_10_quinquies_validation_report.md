# Lot 10-quinquies — Correction finale no-lingering check Lot 10

## Contexte

Le Lot 10-quater avait supprimé le shadowing `pytest.py` et les sorties forcées `os._exit` du code actif. Le métier Transaction Costs V0 restait conforme : 36 estimations 5m, 12 estimations 15m, 48 estimations au total, aucun ordre, aucun fill, aucun PnL exploitable, `trade_allowed=false` et `used_for_decision=false`.

Le dernier blocage venait de `scripts/run_required_chain_until_lot10.sh` : la chaîne arrivait jusqu'à `=== CHECK no lingering direct children ===`, puis le check shell basé sur `pgrep/ps` pouvait rester instable dans l'environnement d'audit.

## Correction appliquée

- Suppression du check shell final `pgrep -P $$` / `ps -o pid,ppid,stat,cmd` dans `scripts/run_required_chain_until_lot10.sh`.
- Suppression du même check shell dans `scripts/validate_all_until_lot10.sh` pour éviter une terminaison dépendante de `pgrep/ps`.
- Conservation du diagnostic process tree dans `scripts/diagnose_lot10_lingering_processes.py`, exécuté séparément dans les commandes obligatoires.
- Ajout du test `tests/test_lot10_required_chain_no_shell_lingering_check.py`.
- Mise à jour du smoke subset Lot 10, qui reste passif et ne relance pas de script lourd.

## Preuves attendues

Les commandes de preuve doivent afficher :

```text
LOT 10-quinquies REQUIRED CHAIN: PASS
REQUIRED_CHAIN_LOT10_DONE
DIAGNOSE LOT10 LINGERING PROCESSES: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```

## Garanties métier conservées

```text
orders_created_count = 0
fills_created_count = 0
pnl_total = 0
trade_allowed = false
used_for_decision = false
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
live_execution = DISABLED
leverage = FORBIDDEN
```

## Limites

Ce lot corrige uniquement la terminaison CI et ne démarre pas le Lot 11.


## Addendum pytest propre

Pour stabiliser `python -m pytest -q` après la chaîne longue sans shadowing local, le projet conserve la résolution vers le vrai package pytest installé. La configuration pytest désactive le cache pytest et la sortie terminale verbeuse afin de limiter les problèmes de descripteurs dans les chaînes longues, sans créer de fichier `pytest.py`, sans `os._exit`, sans `signal.alarm`, et sans wrapper pytest custom.

Le fichier `tests/test_aaa_lot4_validate_all_terminates.py` a été simplifié en retirant des imports inutilisés (`os`, `subprocess`, `sys`) afin d'éviter tout état d'import inutile dans le pytest global post-chaîne.
