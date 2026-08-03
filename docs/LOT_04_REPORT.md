# Lot 4 Report

Lot 4 ajoute :

- Volume Profile V1 ;
- VWAP session V1 ;
- Anchored VWAP V1 ;
- anchors déterministes ;
- contracts dédiés ;
- datasets gold ;
- rapports ;
- validation et tests.

Le Lot 4 ne contient pas :

- trading ;
- stratégie ;
- backtest ;
- WebSocket ;
- API ;
- ML ;
- IA/news ;
- paper trading ;
- live execution.

Le système reste défensif :

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
```

## Lot 4-bis — Validation Robustness

Lot 4-bis ne modifie pas le périmètre fonctionnel du Lot 4.
Il corrige uniquement la robustesse de validation :

- `validate_lot3.py` ne relance plus toute la chaîne imbriquée ;
- `validate_lot4.py` ne relance plus `validate_lot3.py` ni les builds précédents ;
- `validate_lot3.py` et `validate_lot4.py` vérifient directement les artefacts et invariants nécessaires ;
- `scripts/validate_all_until_lot4.py` orchestre la chaîne complète avec timeouts explicites ;
- les validations ne génèrent plus de nombreux `reports/replay_*.json` aléatoires ;
- le replay de validation est écrit dans `data/audit/replay_validation/latest_validation_replay.json`.

Commandes de robustesse :

```bash
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
```

Résultat attendu :

```text
LOT 4-bis VALIDATION: PASS
```

## Lot 4-quinquies — Orchestrator Validation Robustness

Lot 4-quinquies ne modifie pas le périmètre fonctionnel du Lot 4.
Il corrige uniquement l'orchestrateur complet `scripts/validate_all_until_lot4.py`.

Cause corrigée : l'orchestrateur Lot 4-bis utilisait encore des captures stdout/stderr via `capture_output=True` dans certains subprocess. Dans l'environnement d'audit, cette capture pouvait rester bloquée malgré des validations individuelles valides.

Corrections :

- `scripts/validation_utils.py` expose `run_script_streamed(...)` et `run_module_streamed(...)` ;
- `scripts/validate_all_until_lot4.py` streame stdout/stderr directement vers la console ;
- aucun `capture_output=True` n'est utilisé dans l'orchestrateur ;
- les scripts projet ont un timeout de 60 secondes ;
- pytest a un timeout de 180 secondes ;
- `CQB_SKIP_NESTED_PYTEST=1` permet aux tests d'exécuter l'orchestrateur sans récursion pytest ;
- `LOT 4-quinquies VALIDATION: PASS` est le message final attendu.

Commandes de robustesse :

```bash
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
```

Résultat attendu :

```text
LOT 4-quinquies VALIDATION: PASS
```

## Lot 4-quinquies update — definitive orchestrator correction

Lot 4-quinquies does not change Lot 4 functional outputs. It replaces the remaining fragile full-validation orchestrator path with a simple Bash orchestrator plus a minimal Python delegate.

Validation command:

```bash
timeout 300s python scripts/validate_all_until_lot4.py
```

Expected result:

```text
LOT 4-quinquies VALIDATION: PASS
```

## Lot 4-quinquies — validation orchestrée définitive

- `CQB_ORCHESTRATOR_MODE=fast` est le mode par défaut de `scripts/validate_all_until_lot4.sh`.
- Le mode fast vérifie les artefacts clés et lance les validations Lot 0 à Lot 4 sans rebuild lourd.
- `CQB_ORCHESTRATOR_MODE=full` conserve le rebuild complet explicite.
- `scripts/validate_all_until_lot4.py` reste un wrapper Python minimal vers le script Bash.
- Le test orchestrateur lance réellement le wrapper avec `CQB_SKIP_NESTED_PYTEST=1` et ne skippe plus.
- La sortie attendue est `LOT 4-quinquies VALIDATION: PASS`.


## Lot 4-sexies — CI pytest orchestrator test included

Lot 4-sexies fixes the remaining CI issue: `python -m pytest -q` was still deselecting the orchestrator test through `pyproject.toml`. The `-k not test_validate_all_until_lot4_executes_without_nested_pytest` filter has been removed. The orchestrator test now runs by default and expects `LOT 4-sexies VALIDATION: PASS`.

Lot 4-sexies final behavior: fast orchestrator validation does not run nested pytest; the default `python -m pytest -q` run executes the orchestrator test directly, with 0 skipped and 0 deselected tests.

Lot 4-sexies CI detail: `pyproject.toml` has no `-k` deselection filter. It keeps `-s` to avoid capture-related hangs while still executing the orchestrator test by default.

Lot 4-sexies pytest exit stabilization: pytest records the real exit status and forces process termination after unconfigure to avoid post-summary hangs in the audit environment.


## Lot 4-septies — Suppression des validations imbriquées

Lot 4-septies corrige le dernier blocage CI : les validations individuelles ne doivent plus s'appeler entre elles. `scripts/validate_lot2.py` ne relance plus `validate_lot0.py` ni `validate_lot1.py`, et aucun `validate_lot1.py` / `validate_lot2.py` / `validate_lot3.py` / `validate_lot4.py` ne contient `capture_output=True` ni d'appel à un autre script de validation de lot.

L'orchestrateur `validate_all_until_lot4.py` / `.sh` est désormais le seul responsable de l'enchaînement complet multi-lots. Le message final attendu est `LOT 4-septies VALIDATION: PASS`.
