# Lot 10 Report — Transaction Costs, Spread & Slippage Model V0

Le Lot 10 ajoute une couche neutre de modélisation des coûts de transaction. Il lit les BacktestStep `WAIT` du Lot 9 et les MarketState validés du Lot 7 pour produire une estimation théorique de frais, spread et slippage.

## Résumé

Outputs attendus :

```text
data/audit/transaction_cost_lot10_run_result.json
data/audit/transaction_cost_lot10_5m_estimates.jsonl
data/audit/transaction_cost_lot10_15m_estimates.jsonl
reports/lot_10_transaction_costs_report.md
```

Résultat attendu :

```text
5m estimates = 36
15m estimates = 12
estimate_count = 48
orders_created_count = 0
fills_created_count = 0
pnl_total = 0
trade_allowed = false
used_for_decision = false
```

## Sécurité

`TransactionCostEstimate` n'est pas un ordre. Le champ `side` vaut toujours `neutral` et `order_type` vaut toujours `hypothetical_noop`. Les coûts ne sont pas utilisés pour décider un trade.

## Limites V0

Le modèle est volontairement simple : frais taker théoriques, spread par défaut borné et slippage de base éventuellement ajusté par volatilité. Il ne produit aucun PnL exploitable et ne constitue pas une stratégie.

## Validation finale

Les commandes finales Lot 10 confirment :

```text
LOT 10 TRANSACTION COSTS: PASS
LOT 10 VALIDATION: PASS
LOT 10 ORCHESTRATED VALIDATION: PASS
LOT 10 ORCHESTRATOR SMOKE: PASS
pytest: all tests passed
EXACT_CHAIN_DONE
```

## Lot 10-bis — CI termination correction

Lot 10 Transaction Costs V0 was functionally correct: it generated 36 5m estimates, 12 15m estimates, 48 total neutral estimates, zero orders, zero fills and zero exploitable PnL.

The Lot 10-bis correction is limited to CI termination robustness. The wrapper `scripts/validate_all_until_lot10.py` no longer uses `os._exit(code)`. It now delegates once to `scripts/validate_all_until_lot10.sh` with `subprocess.run`, `timeout=300`, `check=False`, no output capture and `raise SystemExit(main())`.

A bounded required chain script was added at `scripts/run_required_chain_until_lot10.sh`. It executes the Lot 0 to Lot 10 chain step by step with timeouts and ends with a passive pytest smoke subset. The diagnostic script `scripts/diagnose_lot10_chain.py` checks the critical Lot 8 to Lot 10 sequence.

Expected proofs are `LOT10_WRAPPER_DONE`, `REQUIRED_CHAIN_LOT10_DONE`, `DIAGNOSE LOT10 CHAIN: PASS`, `PYTEST_DONE` and `EXACT_CHAIN_DONE`.

## Lot 10-bis final CI note

`run_required_chain_until_lot10.sh` now performs the functional Lot 0 to Lot 10 chain and then a passive smoke verification of Lot 10 outputs and wrapper invariants. Full pytest remains a separate command and is still required. This avoids placing pytest inside the required bounded chain, which was the source of non-returning process/fd behavior in audit.

## Lot 10-ter — CI process tree termination

Lot 10-ter keeps Transaction Costs V0 unchanged and fixes the remaining CI process-tree termination issue. The required Lot 10 chain now uses a strictly passive smoke subset, checks for lingering direct children before printing PASS, and includes a dedicated Lot 10 lingering process diagnostic.

The correction adds `scripts/diagnose_lot10_lingering_processes.py`, `tests/test_lot10_outputs_static.py`, and `tests/test_lot10_required_chain_smoke_subset_is_passive.py`. The required markers are `REQUIRED_CHAIN_LOT10_DONE`, `DIAGNOSE LOT10 LINGERING PROCESSES: PASS`, and `EXACT_CHAIN_DONE`.

## Lot 10-quater — CI propre finale

Le Lot 10-quater supprime le fichier local `pytest.py` qui shadowait le vrai package pytest. Il supprime aussi `os._exit(...)` du code actif et ajoute un diagnostic de résolution pytest. Le modèle Transaction Costs V0 reste inchangé : aucune stratégie, aucun ordre, aucun fill et aucun PnL exploitable.

## Lot 10-quinquies — Correction finale no-lingering check

Le Lot 10-quinquies corrige le dernier blocage CI localisé dans le check shell final de `scripts/run_required_chain_until_lot10.sh`. Le bloc `pgrep -P $$` / `ps -o pid,ppid,stat,cmd` a été supprimé du script requis afin que la chaîne ne dépende plus d'une introspection shell instable dans l'environnement d'audit.

La preuve process tree reste assurée séparément par `scripts/diagnose_lot10_lingering_processes.py`, qui est exécuté dans les commandes obligatoires. La chaîne requise affiche maintenant `LOT 10-quinquies REQUIRED CHAIN: PASS`, puis retourne au shell avec `REQUIRED_CHAIN_LOT10_DONE`.


Note CI Lot 10-quinquies: `python -m pytest -q` continue de résoudre vers le package pytest installé. La configuration pytest évite le cache pytest et la sortie terminale verbeuse afin de limiter les problèmes de descripteurs dans les chaînes longues, sans fichier local `pytest.py`, sans `os._exit` et sans wrapper pytest custom.

## Addendum Lot 10-sexies — CI sans pytest imbriqué

Le Lot 10-sexies supprime le pytest smoke subset encore présent dans `scripts/validate_all_until_lot10.sh`. L’orchestrateur Lot 10 redevient strictement responsable de l’enchaînement des validations directes et de la vérification des artefacts, tandis que `python -m pytest -q` reste une étape externe séparée dans la chaîne CI exacte.


## Lot 10-septies — Chaîne requise rapide

Le Lot 10-septies rend `scripts/run_required_chain_until_lot10.sh` rapide et passif. Le script ne duplique plus les rebuilds historiques ni les audits Lot 8. Il vérifie statiquement les artefacts Lot 8 / Lot 9, relance uniquement le run courant Lot 10 et sa validation, puis affiche `LOT 10-septies REQUIRED CHAIN: PASS`. Le pytest complet reste exécuté séparément dans la chaîne exacte CI.

## Lot 10-octies — Chaînes rapides passives

Le Lot 10-octies rend les chaînes rapides Lot 10 réellement terminables :

- `validate_all_until_lot10.sh` ne lance plus les validations historiques Lots 0 à 9 en mode fast ;
- `run_required_chain_until_lot10.sh` est shell-only/passif pour les Lots 0 à 9 ;
- les audits et builds lourds restent réservés à la chaîne exacte complète ;
- seuls `run_lot10_transaction_costs.py` et `validate_lot10.py` sont exécutés pour le lot courant ;
- `LOT10_WRAPPER_DONE` et `REQUIRED_CHAIN_LOT10_DONE` prouvent le retour shell des chaînes rapides.

## Lot 10-nonies — Chaîne exacte Lot 0 → Lot 10 terminable

Le Lot 10-nonies corrige le rejet restant après Lot 10-octies. Lot 10-octies avait rendu terminables les chaînes rapides/passives, mais l'audit chef de projet bloquait encore sur la chaîne exacte complète Lot 0 → Lot 10, observée après `LOT 5 VALIDATION: PASS`.

La correction reste strictement non fonctionnelle : Transaction Costs V0 n'est pas modifié, aucune stratégie n'est créée, aucun ordre n'est créé, aucun PnL exploitable n'est produit et `used_for_decision=false` reste inchangé.

Ajouts principaux :

```text
scripts/diagnose_exact_chain_until_lot10.py
tests/test_exact_chain_scripts_terminate.py
reports/lot_10_nonies_validation_report.md
```

Les scripts de la chaîne exacte ont été normalisés vers un pattern de sortie naturel `raise SystemExit(main())` avec flush explicite, notamment autour de l'enchaînement Lot 5 → Lot 6 et des scripts historiques Lot 3 → Lot 7.

Preuves obtenues :

```text
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
152 passed
```

## Lot 10-decies — Stabilisation audit_lot8_no_lookahead

Le Lot 10-decies corrige le rejet restant après Lot 10-nonies. Lot 10-nonies avait ajouté le diagnostic exact Lot 0 → Lot 10, mais l'audit chef de projet a localisé le blocage suivant autour de `scripts/audit_lot8_no_lookahead.py`, après la séquence complète jusqu'au Lot 7 et après `scripts/audit_lot8_feature_registry.py`.

La correction rend l'audit Lot 8 no-lookahead borné, passif et terminable : il audite uniquement les fichiers explicitement listés dans la politique `AUDITED_DATASET_RELATIVE_PATHS`, sans scan récursif du dépôt, sans scan global de `data/`, sans subprocess, sans PIPE, sans capture de sortie et sans écriture cumulative non idempotente.

Ajouts principaux :

```text
scripts/diagnose_lot8_no_lookahead_after_chain.py
tests/test_lot8_no_lookahead_audit_is_bounded.py
tests/test_lot8_no_lookahead_after_chain_terminates.py
reports/lot_10_decies_validation_report.md
```

Preuves attendues :

```text
LOT 8 NO-LOOKAHEAD AUDIT: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```

Preuves obtenues dans l'archive Lot 10-decies :

```text
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
155 passed
```

## Lot 10-undecies — Terminaison réelle build_lot7_market_state

Lot 10-undecies corrects the remaining exact-chain termination issue localized by audit around `scripts/build_lot7_market_state.py` after the historical Lot 0 to Lot 6 sequence. The Lot 7 build script now ends with a normal `main()` return, `print("LOT 7 MARKET STATE BUILD: PASS", flush=True)`, and `raise SystemExit(main())`.

Acceptance evidence is stored in `reports/lot_10_undecies_validation_report.md` and command logs under `reports/lot_10_undecies_command_logs/`. Expected markers are `DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS`, `DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS`, `DIAGNOSE EXACT CHAIN LOT10: PASS`, and `EXACT_CHAIN_DONE`.


## Lot 10-duodecies — Retour shell réel après EXACT_CHAIN_DONE

Lot 10-undecies corrected `build_lot7_market_state.py`. The following chef de projet audit then showed that the exact Lot 0 to Lot 10 chain could print `EXACT_CHAIN_DONE` while the external process still did not return reliably to the shell.

Lot 10-duodecies adds diagnostics for the post-pytest process tree and the exact-chain shell return:

- `scripts/diagnose_after_pytest_lingering.py`
- `scripts/diagnose_exact_chain_return_shell.py`

The pytest suite is kept passive/static for long-chain behavior. No pytest test launches the exact long chain or nested pytest.

Lot 10-terdecies removes the previous stdout/stderr detach workaround and removes `sitecustomize.py`; pytest now runs through the normal installed package resolution and the exact chain returns naturally.


## Lot 10-terdecies — Suppression des hacks stdout/stderr et terminaison naturelle

Lot 10-terdecies follows the chef de projet audit of Lot 10-duodecies. The audit found that active build, validation and audit scripts had introduced artificial stdout/stderr detachment through helper functions and `/dev/null` descriptor redirection after printing PASS. These workarounds were removed because they could mask or provoke unstable behavior in long CI chains.

The active scripts now terminate naturally with `raise SystemExit(main())`; the `main()` functions print their PASS markers with normal stdout/stderr behavior and return `0`. No script redirects stdout or stderr to `/dev/null`. The global `sitecustomize.py` pytest-environment workaround was also removed.

Added safeguards:

```text
tests/test_no_stdout_stderr_detach_hacks.py
reports/lot_10_terdecies_validation_report.md
reports/lot_10_terdecies_command_logs/
```

Proof markers obtained:

```text
DIAGNOSE PYTEST RESOLUTION: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
161 passed
```

## Lot 10-quaterdecies — Terminaison réelle validate_lot5 après chaîne historique

Lot 10-terdecies supprimait les hacks stdout/stderr et rétablissait une terminaison naturelle. L'audit chef de projet suivant a localisé le blocage restant à `scripts/validate_lot5.py` après la séquence historique jusqu'à `scripts/build_lot5_volatility.py` : le script passait isolément mais pouvait ne pas rendre la main en chaîne longue.

Lot 10-quaterdecies corrige `validate_lot5.py` sans changement métier Transaction Costs V0. Le contrôle de `data/audit/dataset_catalog.json` est désormais structuré et borné : lecture via `json.load`, taille maximale contrôlée, et vérification limitée aux quatre `dataset_id` Lot 5 attendus. Le script conserve une sortie naturelle avec `print("LOT 5 VALIDATION: PASS", flush=True)` et `raise SystemExit(main())`.

Ajouts :

```text
scripts/diagnose_lot5_validate_after_chain.py
tests/test_lot5_validate_after_chain_static.py
reports/lot_10_quaterdecies_validation_report.md
reports/lot_10_quaterdecies_command_logs/
```

Preuves obtenues :

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
VALIDATE_LOT5_CHAIN_DONE
PYTEST_DONE
EXACT_CHAIN_DONE
163 passed
```


## Lot 10-quindecies — Terminaison réelle validate_lot4 après chaîne historique

Lot 10-quaterdecies corrigeait `scripts/validate_lot5.py`. L'audit chef de projet suivant a localisé le blocage restant à `scripts/validate_lot4.py` après la séquence historique jusqu'à `scripts/build_lot4_volume_vwap.py` : le script passait isolément mais pouvait ne pas rendre la main en chaîne longue.

Lot 10-quindecies corrige `validate_lot4.py` sans changement métier Transaction Costs V0. Le contrôle de `data/audit/dataset_catalog.json` est désormais structuré et borné : lecture via `json.load`, taille maximale contrôlée, et vérification limitée aux `dataset_id` Lot 4 attendus. Le script conserve une sortie naturelle avec `print("LOT 4 VALIDATION: PASS", flush=True)` et `raise SystemExit(main())`.

Ajouts :

```text
scripts/diagnose_lot4_validate_after_chain.py
tests/test_lot4_validate_after_chain_static.py
reports/lot_10_quindecies_validation_report.md
reports/lot_10_quindecies_command_logs/
```

Preuves obtenues :

```text
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
VALIDATE_LOT4_CHAIN_DONE
PYTEST_DONE
EXACT_CHAIN_DONE
165 passed
```


## Lot 10-sexdecies — Diagnostics naturels sans Popen/process group

Lot 10-quindecies corrigeait `scripts/validate_lot4.py`. L'audit chef de projet suivant a montré que `scripts/diagnose_lot5_validate_after_chain.py` pouvait afficher `DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS` mais ne pas retourner réellement au shell.

Lot 10-sexdecies corrige les diagnostics eux-mêmes, sans changement métier Transaction Costs V0. Les diagnostics actifs n'utilisent plus `subprocess.Popen`, `start_new_session=True`, `os.killpg`, `signal.SIGTERM`, `signal.SIGKILL` ou `process.wait()`. Ils utilisent désormais `subprocess.run(..., timeout=..., check=False)` avec marqueurs `BEFORE` / `AFTER`, retour `124` en cas de timeout et sortie naturelle avec `raise SystemExit(main())`.

Ajouts :

```text
scripts/diagnose_* corrigés avec subprocess.run simple
tests/test_diagnostics_use_subprocess_run_only.py
reports/lot_10_sexdecies_validation_report.md
reports/lot_10_sexdecies_command_logs/
```

Preuves obtenues :

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
166 passed
rc=0
```


## Lot 10-septendecies — Identification descendant/fd hérité après diagnostic Lot 5

Lot 10-sexdecies supprimait `subprocess.Popen`, les process groups et la gestion manuelle `SIGTERM` / `SIGKILL` des diagnostics. L'audit chef de projet suivant a montré que `scripts/diagnose_lot5_validate_after_chain.py` pouvait afficher `DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS` puis `DIAG5_DONE`, mais que le process externe pouvait encore ne pas retourner naturellement.

Lot 10-septendecies ajoute un diagnostic `/proc` ciblé pour identifier, étape par étape, un éventuel descendant ou fd stdout/stderr hérité après la séquence Lot 0 → Lot 5. Dans l'état final audité localement, aucun script de la séquence Lot 0 → Lot 5 ne laisse de descendant ou de fd problématique : le diagnostic affiche `NO_LINGERING_AFTER:<step>` après chaque étape puis `DIAGNOSE LOT5 FD LINGERING OWNER: PASS`. Le résultat observé nomme donc explicitement l'owner final comme absent (`none detected`) plutôt que de masquer le problème par un kill ou un détachement artificiel.

Ajouts :

```text
scripts/diagnose_lot5_fd_lingering_owner.py
tests/test_no_background_process_or_fd_hacks.py
tests/test_lot5_diagnostics_return_shell_static.py
reports/lot_10_septendecies_validation_report.md
reports/lot_10_septendecies_command_logs/
```

Preuves obtenues :

```text
DIAGNOSE LOT5 FD LINGERING OWNER: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAG5_DONE
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
169 passed
rc=0
```


## Lot 10-octodecies — Identification et correction du blocage Lot 4 exact chain

Lot 10-septendecies ajoutait un diagnostic fd/process Lot 5. L'audit chef de projet suivant a montré que le blocage apparaît plus tôt, autour de `scripts/build_lot4_volume_vwap.py` puis `scripts/validate_lot4.py` : `build_lot4_volume_vwap.py` retournait `rc=0`, puis la chaîne entrait dans `validate_lot4.py` sans retour naturel fiable dans l'environnement d'audit.

Lot 10-octodecies ajoute un diagnostic fd/process ciblé Lot 4 : `scripts/diagnose_lot4_fd_lingering_owner.py`. Il inspecte `/proc` après chaque étape Lot 0 → Lot 4 et affiche `NO_LINGERING_AFTER:<step>` pour chaque étape saine. Le script fautif identifié côté audit est `scripts/validate_lot4.py`; la correction appliquée est un durcissement non métier du contrôle borné des champs interdits, en conservant la sortie naturelle `print("LOT 4 VALIDATION: PASS", flush=True)` et `raise SystemExit(main())`.

Ajouts :

```text
scripts/diagnose_lot4_fd_lingering_owner.py
tests/test_lot4_fd_lingering_owner_static.py
tests/test_lot4_chain_scripts_no_background_or_fd_hacks.py
reports/lot_10_octodecies_validation_report.md
reports/lot_10_octodecies_command_logs/
```

Preuves obtenues :

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
172 passed
rc=0
```


## Lot 10-novemdecies — Identification et correction du blocage Lot 6 exact chain

Lot 10-octodecies corrigeait `validate_lot4.py`, mais l'audit chef de projet suivant a montré que le blocage exact-chain s'était déplacé plus tard, autour de `build_lot6_regime.py` puis `validate_lot6.py`.

Le diagnostic ajouté `scripts/diagnose_lot6_validate_after_chain.py` exécute la chaîne historique Lot 0 à Lot 6 avec un timeout explicite par étape, des marqueurs `BEFORE:` / `AFTER:`, puis un contrôle `/proc` des descendants directs/indirects, des processus Python projet encore vivants et des héritages stdout/stderr visibles.

Le script fautif réel identifié est `scripts/validate_lot6.py`. La cause résiduelle était un contrôle de `data/audit/dataset_catalog.json` par lecture texte brute. La correction remplace ce scan par une lecture JSON structurée via `DatasetCatalog.load()`, bornée et limitée aux deux `dataset_id` Lot 6 attendus :

- `btc_eur_5m_regime_lot6`
- `btc_eur_15m_regime_lot6`

Les lectures de fichiers Lot 6 ont aussi été normalisées avec context managers explicites dans `scripts/build_lot6_regime.py` et `scripts/validate_lot6.py`.

Ajouts :

```text
scripts/diagnose_lot6_validate_after_chain.py
tests/test_lot6_validate_after_chain_static.py
reports/lot_10_novemdecies_validation_report.md
```

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


## Addendum Lot 11 — Consommation documentaire du Lot 10

Le Lot 11 consomme les sorties Lot 10 uniquement comme contexte documentaire pour un Risk Engine défensif. Les estimations de coûts de transaction ne sont pas utilisées pour ouvrir une position ; elles servent seulement à horodater et documenter les snapshots de blocage du Risk Engine.

Les invariants Lot 10 restent donc inchangés même après ajout du Lot 11 :

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Addendum Lot 12 — Consommation documentaire du Lot 10

Le Lot 12 consomme aussi les sorties Lot 10 uniquement comme contexte documentaire de sécurité d’exposition et de capital. Ces estimations ne doivent jamais devenir une source d’allocation, de rebalancing, d’exposition active, de stratégie, d’ordre, de fill ou de PnL exploitable.

Les invariants Lot 10 restent inchangés après ajout du Lot 12 :

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`
