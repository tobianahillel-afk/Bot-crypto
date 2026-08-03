# Lot 10-quaterdecies — Terminaison réelle validate_lot5 après chaîne historique

## Résumé

Lot 10-quaterdecies ne commence pas le Lot 11. Il corrige uniquement la terminaison de `scripts/validate_lot5.py` lorsqu'il est exécuté après la séquence historique Lot 0 → Lot 5.

Le Lot 10-terdecies supprimait les hacks stdout/stderr et rétablissait une terminaison naturelle des scripts. L'audit chef de projet suivant a localisé un blocage résiduel à `scripts/validate_lot5.py` après `scripts/build_lot5_volatility.py` dans une chaîne longue, alors que `validate_lot5.py` passait isolément.

## Cause corrigée

`validate_lot5.py` vérifiait la présence des datasets Lot 5 dans `data/audit/dataset_catalog.json` par lecture texte brute. Cette approche restait fonctionnelle sur un fichier court, mais elle était moins robuste dans une chaîne longue répétée où le catalogue est régénéré par plusieurs lots.

La correction rend le contrôle catalogue borné et structuré :

- lecture via `json.load` ;
- taille maximale contrôlée ;
- vérification limitée aux quatre `dataset_id` Lot 5 attendus ;
- aucune lecture brute inutile du catalogue complet sous forme de texte ;
- aucun scan récursif ;
- aucune boucle non bornée ;
- aucune écriture dans le catalogue depuis `validate_lot5.py`.

## Corrections appliquées

- `scripts/validate_lot5.py` lit les JSONL Lot 5 avec bornes explicites de taille et de nombre de lignes.
- `scripts/validate_lot5.py` lit `dataset_catalog.json` avec `json.load` et vérifie un ensemble borné de quatre IDs.
- `src/crypto_quant_bot/data/catalog.py` conserve `DatasetCatalog.upsert` idempotent et ajoute une lecture/écriture par context managers avec taille maximale de catalogue.
- Ajout du diagnostic ciblé `scripts/diagnose_lot5_validate_after_chain.py`.
- Ajout du test statique `tests/test_lot5_validate_after_chain_static.py`.

## Preuves de validation

Commandes exécutées avec `rc=0` :

```text
timeout 60s python scripts/diagnose_pytest_resolution.py
timeout 300s python scripts/diagnose_lot5_validate_after_chain.py
timeout 300s python scripts/diagnose_lot7_build_after_chain.py
timeout 300s python scripts/diagnose_lot8_no_lookahead_after_chain.py
timeout 300s python scripts/diagnose_exact_chain_until_lot10.py
timeout 300s python scripts/diagnose_after_pytest_lingering.py
timeout 300s python scripts/diagnose_exact_chain_return_shell.py
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
```

Marqueurs obtenus :

```text
DIAGNOSE PYTEST RESOLUTION: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
VALIDATE_LOT5_CHAIN_DONE
EXACT_CHAIN_DONE
```

Résultat pytest :

```text
163 passed
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

Aucun élément métier interdit n'a été ajouté : pas de stratégie, pas d'ordre réel, pas d'ordre simulé exploitable, pas de PnL exploitable, pas de paper trading, pas de signal LONG/SHORT, pas de target/label/future_*, pas d'appel API et pas de WebSocket.
