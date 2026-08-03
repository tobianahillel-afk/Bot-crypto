# Lot 10-quindecies — Terminaison réelle validate_lot4 après chaîne historique

## Résumé

Lot 10-quindecies corrige le blocage localisé par l'audit chef de projet à `scripts/validate_lot4.py` après la séquence historique Lot 0 → `build_lot4_volume_vwap.py`.

Le Lot 10-quaterdecies corrigeait `validate_lot5.py`. L'audit suivant a montré que `validate_lot4.py` passait isolément mais pouvait ne pas rendre la main en chaîne longue après `build_lot4_volume_vwap.py`.

## Correction

`validate_lot4.py` ne lit plus `data/audit/dataset_catalog.json` en texte brut. Le contrôle catalogue est désormais borné et structuré :

- lecture via `json.load` ;
- taille maximale de catalogue contrôlée ;
- vérification limitée aux `dataset_id` Lot 4 attendus ;
- lecture JSONL bornée par taille et nombre de lignes ;
- aucun scan récursif ;
- aucun subprocess ;
- sortie naturelle avec `print("LOT 4 VALIDATION: PASS", flush=True)` puis `raise SystemExit(main())`.

## Fichiers ajoutés

```text
scripts/diagnose_lot4_validate_after_chain.py
tests/test_lot4_validate_after_chain_static.py
reports/lot_10_quindecies_command_logs/
```

## Preuves d'exécution

Les commandes finales ont été exécutées et leurs logs sont conservés dans `reports/lot_10_quindecies_command_logs/`.

Marqueurs obtenus :

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
VALIDATE_LOT4_CHAIN_DONE
EXACT_CHAIN_DONE
```

Tous les retours de commandes finales sont `rc=0`.

## Résultat pytest

```text
165 passed
```

## Invariants sécurité/métier

Le lot ne modifie pas la logique métier Transaction Costs V0 et ne crée pas de stratégie, ordre réel, ordre simulé exploitable, PnL exploitable, paper trading, signal LONG/SHORT, target, label, `future_*`, appel API ou WebSocket.

Invariants conservés :

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```
