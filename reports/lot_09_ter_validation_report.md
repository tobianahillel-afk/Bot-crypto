# Lot 9-ter — Robustesse CI complète / chaîne obligatoire stable

## Contexte

Le Lot 9 et le Lot 9-bis étaient conformes côté Backtest Replay V0 : le replay produisait 36 steps en 5m, 12 steps en 15m, 48 décisions `WAIT`, aucun ordre, aucun fill, aucun PnL exploitable et aucune violation lookahead.

Le rejet restant concernait uniquement la stabilité de la chaîne complète obligatoire en environnement d'audit.

## Corrections Lot 9-ter

- Ajout de `scripts/run_required_chain_until_lot9.sh` avec un `timeout` par étape.
- Bornage des scripts Lot 8 critiques : `audit_lot8_feature_registry.py`, `audit_lot8_no_lookahead.py`, `validate_lot8.py`.
- Stabilisation de `run_lot9_backtest_replay.py` après les audits Lot 8.
- Écriture atomique simple des rapports et JSON d'audit.
- Stabilisation de `dataset_catalog.json` par upsert idempotent sur `dataset_id`.
- Ajout de tests de stabilité Lot 8 -> Lot 9.
- Conservation des tests orchestrateurs en mode `smoke` uniquement.

## Résultats

```text
LOT 9-ter REQUIRED CHAIN: PASS
LOT 9 ORCHESTRATED VALIDATION: PASS
LOT 9 ORCHESTRATOR SMOKE: PASS
pytest: 117 passed
required exact chain: rc=0
no validation timeout
no skipped orchestrator test
no deselected orchestrator test
dataset_catalog stable
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

## Limites

Lot 9-ter ne démarre pas le Lot 10 et ne crée aucune stratégie, aucun PnL exploitable, aucun signal LONG/SHORT, aucun target, label, future_*, appel API ou WebSocket.
