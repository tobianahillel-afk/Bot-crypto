# Lot 10-nonies — Chaîne exacte Lot 0 → Lot 10 terminable

## Résumé

Le Lot 10-nonies ne commence pas le Lot 11 et ne modifie pas la logique métier Transaction Costs V0.

Le lot corrige uniquement la robustesse de terminaison de la chaîne exacte complète Lot 0 → Lot 10, c'est-à-dire la commande imposée qui enchaîne les validations historiques, les builds/audits nécessaires, `python -m pytest -q`, puis `EXACT_CHAIN_DONE`.

## Constat d'audit repris

Le Lot 10-octies avait corrigé les chaînes rapides/passives :

- `scripts/validate_all_until_lot10.py` / `.sh` ;
- `scripts/run_required_chain_until_lot10.sh` ;
- absence de `pytest.py` local ;
- absence de `os._exit`, `signal.alarm` et `CQB_DISABLE_PYTEST_FORCE_EXIT` dans le code actif.

Le rejet restant ne venait donc plus des wrappers rapides. Il venait de la chaîne exacte complète.

Le chef de projet avait observé le blocage après :

```text
LOT 5 VALIDATION: PASS
```

Dans la reproduction locale pré-correction, la chaîne exacte pouvait aussi se figer dans l'enchaînement des scripts historiques, avec un symptôme similaire : un script affichait un marqueur `PASS`, mais le contrôle shell n'atteignait pas systématiquement le marqueur final imposé.

## Cause corrigée

La cause corrigée est non fonctionnelle : discipline de terminaison insuffisamment uniforme sur plusieurs scripts de la chaîne exacte.

Les scripts passifs/historiques les plus sensibles étaient les stubs de build et les validations autour de l'enchaînement Lot 3 → Lot 7, notamment :

```text
scripts/build_lot2_datasets.py
scripts/build_lot3_pivots.py
scripts/build_lot4_volume_vwap.py
scripts/validate_lot4.py
scripts/build_lot5_volatility.py
scripts/validate_lot5.py
scripts/build_lot6_regime.py
scripts/validate_lot6.py
scripts/build_lot7_market_state.py
scripts/validate_lot7.py
```

La correction appliquée ne change pas les sorties métier. Elle normalise les points d'entrée vers un retour naturel et explicite :

```text
raise SystemExit(main())
```

avec flush explicite `stdout` / `stderr` avant la sortie.

## Diagnostic ajouté

Ajout de :

```text
scripts/diagnose_exact_chain_until_lot10.py
```

Ce diagnostic exécute exactement les étapes de la chaîne imposée, dans le même ordre, avec :

- marqueur avant chaque étape ;
- marqueur après chaque étape ;
- durée mesurée ;
- return code ;
- timeout par étape ;
- arrêt clair sur la première étape fautive ;
- stdout/stderr hérités, sans `capture_output=True`, sans `stdout=subprocess.PIPE`, sans `stderr=subprocess.PIPE` ;
- terminaison propre du process group en cas de timeout.

## Test anti-script non terminable

Ajout de :

```text
tests/test_exact_chain_scripts_terminate.py
```

Le test vérifie statiquement que chaque script Python appelé directement par la chaîne exacte :

- expose un `main()` ;
- sort via `raise SystemExit(main())` ;
- ne contient pas `capture_output=True` ;
- ne contient pas `stdout=subprocess.PIPE` ;
- ne contient pas `stderr=subprocess.PIPE` ;
- ne contient pas de terminaison brutale ou d'exec process ;
- ne contient pas d'alarme signal.

## Preuves d'exécution

Toutes les commandes obligatoires ont été exécutées avec timeout externe et ont retourné `rc=0`.

| Commande | Résultat |
|---|---:|
| `timeout 60s python scripts/diagnose_pytest_resolution.py` | rc=0 |
| `timeout 60s python scripts/run_lot10_transaction_costs.py` | rc=0 |
| `timeout 60s python scripts/validate_lot10.py` | rc=0 |
| `timeout 120s bash -lc 'python scripts/validate_all_until_lot10.py; echo LOT10_WRAPPER_DONE'` | rc=0 |
| `timeout 120s bash -lc 'bash scripts/run_required_chain_until_lot10.sh; echo REQUIRED_CHAIN_LOT10_DONE'` | rc=0 |
| `timeout 120s python scripts/diagnose_lot10_required_chain_timing.py` | rc=0 |
| `timeout 300s python scripts/diagnose_exact_chain_until_lot10.py` | rc=0 |
| `timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'` | rc=0 |
| chaîne exacte complète Lot 0 → Lot 10 + pytest + `EXACT_CHAIN_DONE` | rc=0 |

Marqueurs obtenus :

```text
DIAGNOSE PYTEST RESOLUTION: PASS
LOT 10 TRANSACTION COSTS: PASS
LOT 10 VALIDATION: PASS
LOT10_WRAPPER_DONE
REQUIRED_CHAIN_LOT10_DONE
DIAGNOSE LOT10 REQUIRED CHAIN TIMING: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
LOT 10 ORCHESTRATED VALIDATION: PASS
LOT 10 ORCHESTRATOR SMOKE: PASS
```

## Résultat pytest

```text
152 passed
```

## Résultat chaîne exacte

La chaîne imposée affiche maintenant :

```text
EXACT_CHAIN_DONE
```

et retourne :

```text
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

Aucune stratégie, aucun ordre réel, aucun ordre simulé exploitable, aucun PnL exploitable, aucun paper trading, aucun signal LONG/SHORT, aucun target, label ou future_*, aucun appel API et aucun WebSocket n'ont été ajoutés.

## Limites

Ce lot ne traite que la terminaison de la chaîne exacte Lot 0 → Lot 10. Il ne démarre pas le Lot 11.
