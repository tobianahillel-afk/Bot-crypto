# Acceptance Criteria — Lot 9

Le Lot 9 est accepté si les critères suivants sont vrais.

## Artefacts

```text
src/crypto_quant_bot/contracts/backtest.py
src/crypto_quant_bot/backtest/
scripts/run_lot9_backtest_replay.py
scripts/validate_lot9.py
scripts/validate_all_until_lot9.py
scripts/validate_all_until_lot9.sh
```

## Outputs

```text
data/audit/backtest_lot9_run_config.json
data/audit/backtest_lot9_run_result.json
data/audit/backtest_lot9_5m_steps.jsonl
data/audit/backtest_lot9_15m_steps.jsonl
reports/lot_09_backtest_replay_report.md
```

## Résultats attendus

```text
5m steps = 36
15m steps = 12
decision_counts.WAIT = 48
orders_created_count = 0
fills_created_count = 0
pnl_total = 0
lookahead_violations = []
```

## Interdictions

Aucun trading réel, aucune stratégie, aucun paper trading, aucun signal LONG/SHORT, aucun target, aucun label, aucun future_* et aucun ordre exploitable ne doivent être créés.

## Addendum Lot 9-bis — Critères CI finale

Le Lot 9-bis est accepté si les critères suivants sont vrais :

```text
scripts/validate_all_until_lot5.py à scripts/validate_all_until_lot9.py ne contiennent aucun os.execv/os.execve/os.execvp/os.execvpe.
Ces wrappers ne capturent pas stdout/stderr.
Ces wrappers délèguent une seule fois au shell via subprocess.run(..., timeout=300, check=False).
Les orchestrateurs shell Lots 5 à 9 terminent explicitement par exit 0 après le message PASS.
Les tests d'orchestrateurs utilisent uniquement CQB_ORCHESTRATOR_MODE=smoke et CQB_SKIP_NESTED_PYTEST=1.
validate_lot9.py reste direct et ne lance aucun subprocess, build, audit ou autre validate_lotX.py.
timeout 300s python scripts/validate_all_until_lot9.py termine avec rc=0.
La chaîne complète obligatoire termine avec rc=0.
python -m pytest -q passe sans test skipped ni deselected.
```

Le Lot 9-bis ne doit créer aucune stratégie, aucun signal LONG/SHORT, aucun target, aucun label, aucun `future_*`, aucun paper trading, aucun appel API et aucun WebSocket.

## Critères complémentaires Lot 9-ter

- `timeout 300s bash scripts/run_required_chain_until_lot9.sh` doit retourner `0`.
- La chaîne complète obligatoire exacte doit retourner `0` sans timeout.
- Les scripts Lot 8 et Lot 9 doivent finir en moins de 10 secondes dans les validations ciblées.
- `dataset_catalog.json` ne doit pas grossir après deux exécutions successives de `run_lot9_backtest_replay.py`.
- Les tests orchestrateurs restent en smoke uniquement.
- Aucun test ne doit être skipped ou deselected.


## Critères complémentaires Lot 9-ter

- `scripts/run_required_chain_until_lot9.sh` existe et exécute la chaîne obligatoire avec un timeout par étape.
- `audit_lot8_feature_registry.py`, `audit_lot8_no_lookahead.py`, `validate_lot8.py`, `run_lot9_backtest_replay.py` et `validate_lot9.py` terminent en moins de 10 secondes en validation ciblée.
- La chaîne complète obligatoire termine avec `rc=0` sous `timeout 300s`.
- `dataset_catalog.json` reste stable après deux exécutions successives de `run_lot9_backtest_replay.py`.
- Les tests orchestrateurs restent en mode `smoke` uniquement.
- Aucun test orchestrateur n'est skipped ou deselected.

## Critères complémentaires Lot 9-quater

- `scripts/run_required_chain_until_lot9.sh` ne doit plus lancer le pytest complet.
- Le script doit lancer uniquement un pytest smoke subset borné après la chaîne fonctionnelle.
- Le script doit afficher `LOT 9-quater REQUIRED CHAIN: PASS` et sortir avec `exit 0`.
- `scripts/diagnose_pytest_after_chain.py` doit exister et exécuter les fichiers `tests/test_*.py` séparément avec timeout de 30 secondes par fichier.
- La commande complète obligatoire exacte avec `python -m pytest -q` final doit retourner `rc=0` sous `timeout 300s`.
- Le pytest complet reste lancé séparément par la CI et doit passer sans skipped ni deselected.
- Les tests orchestrateurs restent en mode `smoke` uniquement.
- `dataset_catalog.json` reste stable.

## Critères complémentaires Lot 9-quinquies

- `tests/conftest.py` ne contient aucune logique de terminaison forcée pytest.
- `tests/conftest.py` ne contient pas `os._exit`, `signal.alarm`, `pytest_sessionfinish`, `pytest_terminal_summary` ou `pytest_unconfigure`.
- `scripts/run_required_chain_until_lot9.sh` ne lance pas de pytest complet et n'utilise pas de variable de contournement de terminaison pytest.
- `scripts/diagnose_pytest_after_chain.py` n'utilise pas de variable de contournement de terminaison pytest.
- `timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'` affiche `PYTEST_DONE` et retourne `0`.
- `timeout 120s bash -lc 'bash scripts/run_required_chain_until_lot9.sh; echo REQUIRED_CHAIN_DONE'` affiche `REQUIRED_CHAIN_DONE` et retourne `0`.
- La chaîne complète obligatoire avec `echo EXACT_CHAIN_DONE` affiche `EXACT_CHAIN_DONE` et retourne `0`.
- Aucun test orchestrateur n'est skipped ou deselected.
- `dataset_catalog.json` reste stable.

## Critères complémentaires Lot 9-sexies

- `scripts/run_required_chain_until_lot9.sh` doit afficher `LOT 9-sexies REQUIRED CHAIN: PASS` uniquement après le smoke subset et le contrôle d'absence d'enfant direct.
- Le smoke subset de `run_required_chain_until_lot9.sh` doit être passif : lecture de fichiers et invariants uniquement.
- Le smoke subset ne doit pas appeler `test_lot9_dataset_catalog_stability.py`.
- `tests/test_lot9_dataset_catalog_static.py` doit vérifier statiquement les entrées Lot 9 du catalogue sans subprocess.
- `scripts/diagnose_lingering_processes.py` doit afficher `DIAGNOSE LINGERING PROCESSES: PASS` quand aucun descendant ne reste vivant.
- `timeout 120s bash -lc 'bash scripts/run_required_chain_until_lot9.sh; echo REQUIRED_CHAIN_DONE'` doit afficher `REQUIRED_CHAIN_DONE` et retourner `0`.
- La chaîne complète exacte avec `echo EXACT_CHAIN_DONE` doit afficher `EXACT_CHAIN_DONE` et retourner `0`.
- Aucun test orchestrateur ne doit être skipped ou deselected.
- `dataset_catalog.json` doit rester stable et sans doublon `dataset_id`.

## Transition vers Lot 10

Le Lot 10 peut lire les artefacts Lot 9 validés, mais il ne doit pas modifier le replay V0, ne doit pas créer de stratégie, ne doit pas créer d'ordre, ne doit pas créer de fill et ne doit pas générer de PnL exploitable.
