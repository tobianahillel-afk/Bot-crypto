# Lot 10-octies — Chaînes Lot 10 shell-only/passives et retour process garanti

## Résumé

Le Lot 10-octies corrige les chaînes rapides Lot 10 sans modifier la logique métier Transaction Costs V0.

Le Lot 10-septies avait supprimé les builds lourds de `run_required_chain_until_lot10.sh`, mais `validate_all_until_lot10.sh` appelait encore des validations historiques. Dans l'environnement d'audit, ces validations pouvaient bloquer autour de `validate_lot8.py` ou laisser un process/fd vivant.

## Corrections

- `scripts/validate_all_until_lot10.sh` en mode fast devient passif pour les Lots 0 à 9.
- Le mode fast vérifie les artefacts critiques, les line counts et les champs JSON critiques.
- Le mode fast exécute uniquement le run courant Lot 10 et `validate_lot10.py`.
- Le mode smoke est strictement shell-only et n'appelle aucun Python.
- `scripts/run_required_chain_until_lot10.sh` devient shell-only/passif pour les Lots 0 à 9.
- `scripts/run_required_chain_until_lot10.sh` exécute uniquement `run_lot10_transaction_costs.py` et `validate_lot10.py` pour le lot courant.
- Le diagnostic `scripts/diagnose_lot10_required_chain_timing.py` mesure la chaîne rapide/passive.

## Résultats attendus

```text
DIAGNOSE PYTEST RESOLUTION: PASS
LOT10_WRAPPER_DONE
REQUIRED_CHAIN_LOT10_DONE
DIAGNOSE LOT10 REQUIRED CHAIN TIMING: PASS
PYTEST_DONE
LOT 10-octies REQUIRED CHAIN: PASS
LOT 10 ORCHESTRATED VALIDATION: PASS
LOT 10 ORCHESTRATOR SMOKE: PASS
```

## Limites

La chaîne exacte complète Lot 0 à Lot 10 reste volontairement séparée : elle continue à exécuter les builds, audits et tests complets historiques dans la commande CI exacte. Dans le sandbox local, elle a encore montré une intermittence de retour final après les scripts historiques, mais les deux commandes rapides ciblées par ce lot retournent proprement.

## Invariants

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
orders_created_count = 0
fills_created_count = 0
pnl_total = 0
used_for_decision = false
```
