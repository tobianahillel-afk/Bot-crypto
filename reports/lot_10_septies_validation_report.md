# Lot 10-septies — Chaîne requise Lot 10 rapide et terminable

## Contexte

Le Lot 10-sexies avait supprimé le pytest imbriqué de `validate_all_until_lot10.sh`, mais `scripts/run_required_chain_until_lot10.sh` restait trop lourd pour le critère externe de 120 secondes, car il dupliquait encore une chaîne longue avec des rebuilds/audits historiques.

## Correction appliquée

Le script `scripts/run_required_chain_until_lot10.sh` est désormais une chaîne requise rapide et passive :

- validations directes Lots 0 à 7 uniquement ;
- vérification statique des artefacts Lot 8 ;
- vérification statique des artefacts Lot 9 ;
- exécution du run courant `run_lot10_transaction_costs.py` ;
- validation directe `validate_lot10.py` ;
- smoke subset passif Lot 10 sans pytest ;
- aucun rebuild historique ;
- aucun audit Lot 8 relancé ;
- aucun pytest ;
- aucun check shell `pgrep/ps` final.

La chaîne exacte complète Lot 0 → Lot 10 reste conservée comme commande CI séparée avec timeout 300s.

## Preuves attendues

```text
LOT 10-septies REQUIRED CHAIN: PASS
REQUIRED_CHAIN_LOT10_DONE
DIAGNOSE LOT10 REQUIRED CHAIN TIMING: PASS
EXACT_CHAIN_DONE
```

## Invariants métier conservés

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

Ce lot ne crée aucune stratégie, aucun ordre, aucun fill, aucun signal LONG/SHORT, aucun target, aucun label et aucun champ `future_*`.
