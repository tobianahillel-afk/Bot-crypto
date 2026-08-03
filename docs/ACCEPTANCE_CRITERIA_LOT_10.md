# Acceptance Criteria — Lot 10

Le Lot 10 est accepté si :

```text
config/transaction_costs.yaml existe et ne contient aucune clé API.
src/crypto_quant_bot/contracts/costs.py existe.
src/crypto_quant_bot/costs/ existe avec config, fees, spread, slippage, estimator et writer.
scripts/run_lot10_transaction_costs.py produit les outputs attendus.
scripts/validate_lot10.py valide directement le Lot 10 sans appeler d'autre validate_lotX.py.
transaction_cost_lot10_5m_estimates.jsonl contient 36 lignes.
transaction_cost_lot10_15m_estimates.jsonl contient 12 lignes.
transaction_cost_lot10_run_result.json indique estimate_count=48.
orders_created_count=0.
fills_created_count=0.
pnl_total=0.
trade_allowed=false.
used_for_decision=false.
side=neutral partout.
order_type=hypothetical_noop partout.
aucun future_*, target, label, signal LONG/SHORT, buy ou sell n'est présent dans les outputs.
Decision Engine reste WAIT.
Risk Engine bloque toujours.
live_execution=DISABLED.
leverage=FORBIDDEN.
```

Le Lot 10 ne doit pas créer de stratégie, de paper trading, d'exécution live, d'ordre réel, d'ordre simulé exploitable ou de PnL exploitable.

## Résultat de validation observé

```text
LOT 10 TRANSACTION COSTS: PASS
LOT 10 VALIDATION: PASS
LOT 10 ORCHESTRATED VALIDATION: PASS
LOT 10 ORCHESTRATOR SMOKE: PASS
137 passed
EXACT_CHAIN_DONE
```

## Lot 10-bis acceptance addendum

The Lot 10 CI wrapper must terminate naturally and return to the shell. `scripts/validate_all_until_lot10.py` must not contain `os._exit`, `os.execv`, `os.execve`, `os.execvp`, `os.execvpe`, `capture_output=True`, `stdout=subprocess.PIPE` or `stderr=subprocess.PIPE`.

The following commands must return `rc=0` without timeout: `python scripts/validate_all_until_lot10.py`, `bash scripts/run_required_chain_until_lot10.sh`, `python scripts/diagnose_lot10_chain.py`, `python -m pytest -q`, and the exact Lot 0 to Lot 10 chain ending with `EXACT_CHAIN_DONE`.

## Lot 10-bis CI stability addendum

The bounded required chain may use a passive smoke verification for Lot 10 outputs and wrapper invariants. Full pytest must still pass separately and the exact Lot 0 to Lot 10 chain must emit `EXACT_CHAIN_DONE` with rc=0.

## Lot 10-ter acceptance addendum

The Lot 10 required chain must terminate cleanly. `scripts/run_required_chain_until_lot10.sh` must use bounded steps and a passive smoke subset, then print `LOT 10-quinquies REQUIRED CHAIN: PASS` before returning to the shell. Process-tree proof is provided separately by `scripts/diagnose_lot10_lingering_processes.py`.

The smoke subset must not launch pytest, validate_all, run_required_chain, `run_lot9_backtest_replay.py`, or `run_lot10_transaction_costs.py`. It may only read already generated artifacts and verify static invariants.

## Critères additionnels Lot 10-quater

- Aucun fichier local `pytest.py`, dossier `pytest/`, `unittest.py`, `subprocess.py`, `signal.py` ou `os.py` à la racine.
- `python -m pytest -q` doit lancer le vrai package pytest installé.
- Aucun `os._exit`, `signal.alarm` ou `CQB_DISABLE_PYTEST_FORCE_EXIT` dans le code actif (`scripts/`, `src/`, `tests/`).
- La chaîne requise Lot 10 doit afficher `LOT 10-quinquies REQUIRED CHAIN: PASS` puis retourner au shell.
- La chaîne exacte doit afficher `EXACT_CHAIN_DONE`.

## Addendum Lot 10-quinquies

Critères ajoutés :

- `scripts/run_required_chain_until_lot10.sh` ne doit plus contenir `pgrep -P $$`.
- `scripts/run_required_chain_until_lot10.sh` ne doit plus contenir `ps -o pid,ppid,stat,cmd`.
- `scripts/run_required_chain_until_lot10.sh` doit afficher `LOT 10-quinquies REQUIRED CHAIN: PASS` puis retourner au shell.
- La preuve process tree est portée par `scripts/diagnose_lot10_lingering_processes.py`.
- Les marqueurs `REQUIRED_CHAIN_LOT10_DONE` et `EXACT_CHAIN_DONE` doivent être obtenus sans timeout.


Note CI Lot 10-quinquies: `python -m pytest -q` continue de résoudre vers le package pytest installé. La configuration pytest évite le cache pytest et la sortie terminale verbeuse afin de limiter les problèmes de descripteurs dans les chaînes longues, sans fichier local `pytest.py`, sans `os._exit` et sans wrapper pytest custom.

## Critères additionnels Lot 10-sexies

- `scripts/validate_all_until_lot10.sh` ne doit contenir aucun appel `python -m pytest`.
- Le mode fast ne lance pas pytest.
- Le mode full ne lance pas pytest.
- Le mode smoke est shell-only et ne lance aucun script Python.
- Le pytest complet reste exécuté séparément par la chaîne CI exacte.


## Critères complémentaires Lot 10-septies

- `run_required_chain_until_lot10.sh` ne doit pas appeler les scripts de build historiques.
- `run_required_chain_until_lot10.sh` ne doit pas relancer les audits Lot 8.
- `run_required_chain_until_lot10.sh` ne doit pas lancer pytest.
- `run_required_chain_until_lot10.sh` doit afficher `LOT 10-septies REQUIRED CHAIN: PASS`.
- `diagnose_lot10_required_chain_timing.py` doit afficher `DIAGNOSE LOT10 REQUIRED CHAIN TIMING: PASS`.
- La chaîne exacte complète reste exécutée séparément avec `python -m pytest -q`.

## Addendum Lot 10-octies

Critères complémentaires :

- `validate_all_until_lot10.sh` en mode fast est passif pour les Lots 0 à 9 ;
- `validate_all_until_lot10.sh` en mode smoke est shell-only ;
- `run_required_chain_until_lot10.sh` ne relance pas les builds historiques ;
- `run_required_chain_until_lot10.sh` ne relance pas les audits Lot 8 ;
- `run_required_chain_until_lot10.sh` ne lance pas de test global ;
- `run_required_chain_until_lot10.sh` retourne `REQUIRED_CHAIN_LOT10_DONE` sous le timeout demandé ;
- la chaîne exacte complète reste le contrôle de bout en bout séparé.

## Addendum Lot 10-nonies

Critères complémentaires :

- `scripts/diagnose_exact_chain_until_lot10.py` doit exécuter exactement la chaîne Lot 0 → Lot 10 avec marqueurs avant/après, durée, return code et timeout par étape.
- Le diagnostic exact doit afficher `DIAGNOSE EXACT CHAIN LOT10: PASS` uniquement si toutes les étapes rendent réellement la main.
- La commande exacte complète Lot 0 → Lot 10, suivie de `python -m pytest -q`, doit afficher `EXACT_CHAIN_DONE` et retourner `rc=0` sans timeout.
- `tests/test_exact_chain_scripts_terminate.py` doit vérifier statiquement que chaque script Python appelé directement par la chaîne exacte sort proprement via `main()` et ne contient pas de patterns non terminables ou de capture de pipes.
- Les chaînes rapides Lot 10 restent rapides/passives et ne remplacent pas la chaîne exacte.

Preuves attendues :

```text
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
pytest: all tests passed
```

## Addendum Lot 10-decies

Critères complémentaires :

- `scripts/audit_lot8_no_lookahead.py` doit auditer uniquement les fichiers explicitement listés par la politique Lot 8 no-lookahead.
- `scripts/audit_lot8_no_lookahead.py` ne doit pas scanner récursivement le dépôt, `data/` ou des chemins implicites.
- `scripts/audit_lot8_no_lookahead.py` ne doit pas utiliser subprocess, PIPE, capture de sortie, `os._exit`, `os.exec*`, `signal.alarm` ou boucle non bornée.
- `scripts/diagnose_lot8_no_lookahead_after_chain.py` doit reproduire la mini-chaîne jusqu'à `audit_lot8_no_lookahead.py` avec marqueurs BEFORE/AFTER, durée, rc et timeout par étape.
- Le diagnostic ciblé doit afficher `DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS`.
- Le diagnostic exact doit afficher `DIAGNOSE EXACT CHAIN LOT10: PASS`.
- La commande exacte complète doit afficher `EXACT_CHAIN_DONE` et retourner `rc=0` sans timeout.
- Les invariants défensifs Lot 10 restent inchangés : WAIT, BLOCK_TRADING, `trade_allowed=false`, live execution disabled et leverage forbidden.

Preuves attendues :

```text
LOT 8 NO-LOOKAHEAD AUDIT: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
pytest: all tests passed
```

Preuves Lot 10-decies observées :

```text
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
155 passed
```

## Lot 10-undecies acceptance addendum

Lot 10-undecies corrects the remaining exact-chain termination issue localized by audit around `scripts/build_lot7_market_state.py` after the historical Lot 0 to Lot 6 sequence. The Lot 7 build script now ends with a normal `main()` return, `print("LOT 7 MARKET STATE BUILD: PASS", flush=True)`, and `raise SystemExit(main())`.

Acceptance evidence is stored in `reports/lot_10_undecies_validation_report.md` and command logs under `reports/lot_10_undecies_command_logs/`. Expected markers are `DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS`, `DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS`, `DIAGNOSE EXACT CHAIN LOT10: PASS`, and `EXACT_CHAIN_DONE`.


## Lot 10-duodecies acceptance addendum

The exact Lot 0 to Lot 10 chain must not only print `EXACT_CHAIN_DONE`; it must also return to the shell with `rc=0` before the external timeout.

Additional required diagnostics:

```bash
timeout 300s python scripts/diagnose_after_pytest_lingering.py
timeout 300s python scripts/diagnose_exact_chain_return_shell.py
```

Expected markers:

```text
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
EXACT_CHAIN_DONE
```

The pytest suite must remain passive for long-chain checks: no nested pytest, no exact-chain launch, and no active long subprocess in tests.


## Lot 10-terdecies acceptance addendum

The exact Lot 0 to Lot 10 chain must return to the shell naturally without stdout/stderr detach hacks. Active code must not contain manual `/dev/null` redirection helpers, `os.dup2`-based standard stream replacement, local pytest shadowing, `os._exit`, `signal.alarm`, or `CQB_DISABLE_PYTEST_FORCE_EXIT`.

Additional static safeguard:

```text
tests/test_no_stdout_stderr_detach_hacks.py
```

Required proof commands include:

```bash
timeout 300s python scripts/diagnose_lot7_build_after_chain.py
timeout 300s python scripts/diagnose_lot8_no_lookahead_after_chain.py
timeout 300s python scripts/diagnose_exact_chain_until_lot10.py
timeout 300s python scripts/diagnose_after_pytest_lingering.py
timeout 300s python scripts/diagnose_exact_chain_return_shell.py
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
```

Expected markers:

```text
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
rc=0
```

## Lot 10-quaterdecies acceptance addendum

`validate_lot5.py` must terminate naturally after the historical Lot 0 → Lot 5 chain. The script must not use subprocesses, PIPE, `os._exit`, `signal.alarm`, stdout/stderr detach helpers, recursive scans, persistent locks or unbounded catalog reads.

Additional targeted diagnostic:

```bash
timeout 300s python scripts/diagnose_lot5_validate_after_chain.py
```

Required marker:

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
```

The exact Lot 5 mini-chain must also return:

```text
VALIDATE_LOT5_CHAIN_DONE
rc=0
```

The full exact Lot 0 → Lot 10 chain must still return:

```text
EXACT_CHAIN_DONE
rc=0
```

Static safeguard:

```text
tests/test_lot5_validate_after_chain_static.py
```


## Lot 10-quindecies acceptance addendum

`validate_lot4.py` must terminate naturally after the historical Lot 0 → Lot 4 chain. The script must not use subprocesses, PIPE, `os._exit`, `signal.alarm`, stdout/stderr detach helpers, recursive scans, persistent locks or unbounded catalog reads.

Additional targeted diagnostic:

```bash
timeout 300s python scripts/diagnose_lot4_validate_after_chain.py
```

Required marker:

```text
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
```

The exact Lot 4 mini-chain must also return:

```text
VALIDATE_LOT4_CHAIN_DONE
rc=0
```

The downstream diagnostics and full exact Lot 0 → Lot 10 chain must still return:

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
EXACT_CHAIN_DONE
rc=0
```

Static safeguard:

```text
tests/test_lot4_validate_after_chain_static.py
```


## Lot 10-sexdecies acceptance addendum

All active long-chain diagnostics must terminate naturally using `subprocess.run(..., timeout=..., check=False)`.

The following diagnostics must not use `subprocess.Popen`, `start_new_session=True`, process groups, manual signal termination, PIPE capture, DEVNULL redirection, `os._exit`, `signal.alarm`, stdout/stderr detach helpers, or non-daemon thread hacks:

```text
scripts/diagnose_lot4_validate_after_chain.py
scripts/diagnose_lot5_validate_after_chain.py
scripts/diagnose_lot7_build_after_chain.py
scripts/diagnose_lot8_no_lookahead_after_chain.py
scripts/diagnose_exact_chain_until_lot10.py
scripts/diagnose_after_pytest_lingering.py
scripts/diagnose_exact_chain_return_shell.py
scripts/diagnose_lingering_processes.py
```

Required markers:

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
EXACT_CHAIN_DONE
rc=0
```

Static safeguard:

```text
tests/test_diagnostics_use_subprocess_run_only.py
```


## Lot 10-septendecies acceptance addendum

`diagnose_lot5_validate_after_chain.py` and the shell command wrapping it must return naturally after printing their final markers.

Required commands:

```bash
timeout 120s python scripts/diagnose_lot5_fd_lingering_owner.py
timeout 120s bash -lc 'python scripts/diagnose_lot5_validate_after_chain.py; echo DIAG5_DONE'
```

Required markers:

```text
DIAGNOSE LOT5 FD LINGERING OWNER: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAG5_DONE
rc=0
```

The fd/process owner diagnostic must inspect the Lot 0 → Lot 5 sequence after every step and must not rely on process group kills, stdout/stderr detaches, PIPE capture, DEVNULL redirection, `os._exit`, `signal.alarm`, or background process tricks.

Static safeguards:

```text
tests/test_no_background_process_or_fd_hacks.py
tests/test_lot5_diagnostics_return_shell_static.py
```

The exact Lot 0 → Lot 10 chain must still return:

```text
EXACT_CHAIN_DONE
rc=0
```


## Lot 10-octodecies acceptance addendum

The Lot 0 → Lot 4 mini-chain must return naturally:

```bash
timeout 120s bash -lc '
python scripts/validate_lot0.py &&
python scripts/ingest_ohlcvt_fixture.py &&
python scripts/validate_lot1.py &&
python scripts/build_lot2_datasets.py &&
python scripts/validate_lot2.py &&
python scripts/build_lot3_pivots.py &&
python scripts/validate_lot3.py &&
python scripts/build_lot4_volume_vwap.py &&
python scripts/validate_lot4.py &&
echo VALIDATE_LOT4_CHAIN_DONE
'
```

Required markers:

```text
DIAGNOSE LOT4 FD LINGERING OWNER: PASS
VALIDATE_LOT4_CHAIN_DONE
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
rc=0
```

Static safeguards:

```text
tests/test_lot4_fd_lingering_owner_static.py
tests/test_lot4_chain_scripts_no_background_or_fd_hacks.py
```

The Lot 4 fd/process owner diagnostic must inspect after every step and must not rely on process group kills, stdout/stderr detaches, PIPE capture, DEVNULL redirection, `os._exit`, `signal.alarm`, or background process tricks.


## Addendum Lot 10-novemdecies

Critères complémentaires :

- `scripts/diagnose_lot6_validate_after_chain.py` doit exécuter exactement la chaîne historique Lot 0 → Lot 6 avec `BEFORE:<step>` puis `AFTER:<step>:rc=<code>:duration_seconds=<duration>`.
- Après chaque étape, le diagnostic doit vérifier l'absence de descendants directs/indirects résiduels, de processus Python projet encore vivants et d'héritage stdout/stderr visible via `/proc` si disponible.
- Le diagnostic doit afficher `NO_LINGERING_AFTER:<step>` après chaque étape saine.
- `scripts/validate_lot6.py` ne doit plus lire `data/audit/dataset_catalog.json` en texte brut ; il doit utiliser une lecture JSON structurée, bornée et limitée aux `dataset_id` Lot 6 attendus.
- `scripts/build_lot6_regime.py`, `scripts/validate_lot6.py` et `scripts/diagnose_lot6_validate_after_chain.py` doivent se terminer par `raise SystemExit(main())`.
- `tests/test_lot6_validate_after_chain_static.py` doit protéger contre `capture_output=True`, `PIPE`, `DEVNULL`, `os._exit`, `signal.alarm`, `close_standard_streams`, `os.dup2`, `multiprocessing`, `threading.Thread`, `atexit.register`, `subprocess.Popen`, `os.fork`, `pty`, `asyncio.create_task`, `os.system`, `os.spawn`, `os.posix_spawn`, `while True`, `os.walk` et `rglob`.

Preuves attendues :

```text
DIAGNOSE LOT6 VALIDATE AFTER CHAIN: PASS
VALIDATE_LOT6_CHAIN_DONE
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
rc=0
```


## Addendum Lot 11 on top of Lot 10

Les sorties Lot 10 peuvent être relues par le Lot 11 uniquement comme contexte documentaire. Elles ne doivent pas devenir une source de stratégie, d'ouverture de position, d'ordre, de fill ou de PnL exploitable.

Les invariants Lot 10 doivent rester inchangés après exécution du Lot 11 :

- `trade_allowed=false`
- `used_for_decision=false`
- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Addendum Lot 12 on top of Lot 10

- Les sorties Lot 10 peuvent être relues par le Lot 12 uniquement comme contexte documentaire.
- Elles ne doivent pas devenir une source d’allocation capital, de rebalancing, d’exposition active, de stratégie, d’ordre, de fill ou de PnL exploitable.
- Les invariants `trade_allowed=false`, `used_for_decision=false`, `TradingDecision = WAIT`, `SystemDecision = BLOCK_TRADING`, `live_execution = DISABLED` et `leverage = FORBIDDEN` doivent rester inchangés après exécution du Lot 12.
