# Lot 10-decies — Stabilisation audit_lot8_no_lookahead dans la chaîne exacte

## Résumé

Lot 10-decies ne commence pas le Lot 11 et ne modifie pas la logique métier Transaction Costs V0.

Le Lot 10-nonies avait ajouté un diagnostic exact de chaîne Lot 0 → Lot 10 et normalisé les sorties des scripts historiques. L'audit chef de projet a ensuite localisé le blocage restant autour de `scripts/audit_lot8_no_lookahead.py`, après la séquence complète jusqu'au Lot 7 et après `scripts/audit_lot8_feature_registry.py`.

## Cause corrigée

Le point à stabiliser était l'audit Lot 8 no-lookahead exécuté en contexte de chaîne longue. Le correctif rend l'audit explicitement borné par sa politique d'audit : seules les sorties gold listées dans `src/crypto_quant_bot/audit/lookahead.py` sont auditées. Aucun scan récursif du dépôt, de `data/` ou de chemins implicites n'est utilisé.

## Corrections

- `scripts/audit_lot8_no_lookahead.py` exécute désormais l'audit borné via la politique explicite `default_audited_dataset_paths(ROOT)`.
- Le script écrit `data/audit/no_lookahead_audit_lot8.json` et `reports/lot_08_no_lookahead_report.md` de manière idempotente.
- Le script sort par `raise SystemExit(main())` avec flush explicite stdout/stderr.
- Aucun subprocess, PIPE, capture de sortie, `os._exit`, `os.exec*`, `signal.alarm` ou thread n'est introduit.
- `scripts/diagnose_lot8_no_lookahead_after_chain.py` reproduit la mini-chaîne fautive jusqu'à `audit_lot8_no_lookahead.py`, avec marqueurs BEFORE/AFTER, durée, rc et timeout par étape.
- `scripts/diagnose_exact_chain_until_lot10.py` reste le diagnostic complet de référence pour la chaîne exacte Lot 0 → Lot 10.

## Preuves attendues

```text
LOT 8 NO-LOOKAHEAD AUDIT: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
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

Aucune stratégie, aucun ordre réel, aucun ordre simulé exploitable, aucun PnL exploitable, aucun paper trading, aucun signal LONG/SHORT, aucun target, label ou future_*, aucun appel API et aucun WebSocket ne sont créés.

## Résultats observés dans l'archive finale

Toutes les commandes obligatoires ont retourné `rc=0`.

```text
DIAGNOSE PYTEST RESOLUTION: PASS
LOT 8 NO-LOOKAHEAD AUDIT: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
LOT 10 TRANSACTION COSTS: PASS
LOT 10 VALIDATION: PASS
LOT10_WRAPPER_DONE
REQUIRED_CHAIN_LOT10_DONE
DIAGNOSE LOT10 REQUIRED CHAIN TIMING: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
LOT 10 ORCHESTRATOR SMOKE: PASS
155 passed
```

## Logs de preuve

Les sorties complètes des commandes sont conservées dans :

```text
reports/lot_10_decies_command_logs/
```

Le log `03_diagnose_lot8_no_lookahead_after_chain.log` confirme le passage par :

```text
BEFORE:audit_lot8_feature_registry
LOT 8 FEATURE REGISTRY AUDIT: PASS
AFTER:audit_lot8_feature_registry:rc=0
BEFORE:audit_lot8_no_lookahead
LOT 8 NO-LOOKAHEAD AUDIT: PASS
AFTER:audit_lot8_no_lookahead:rc=0
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
```

Le log `11_exact_chain.log` confirme :

```text
LOT 8 NO-LOOKAHEAD AUDIT: PASS
LOT 10 VALIDATION: PASS
155 passed
EXACT_CHAIN_DONE
```
