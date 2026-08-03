# Lot 5-ter Validation Report

## Context

Lot 5 and Lot 5-bis were functionally correct, but the full CI chain could still block during the final pytest phase because pytest executed a heavy orchestrator test.

## Correction

Lot 5-ter introduces a dedicated smoke mode for `scripts/validate_all_until_lot5.py` / `.sh`.

- `CQB_ORCHESTRATOR_MODE=smoke` performs artifact checks only.
- It does not run build scripts.
- It does not run validate scripts.
- It does not run pytest.
- It does not call another orchestrator.

The default fast orchestrator also avoids running pytest; CI runs `python -m pytest -q` as a separate step.

## Expected outputs

```text
LOT 5-ter ORCHESTRATED VALIDATION: PASS
LOT 5-ter ORCHESTRATOR SMOKE: PASS
```

## Validation commands

- `timeout 60s python scripts/build_lot5_volatility.py`: PASS
- `timeout 60s python scripts/validate_lot1.py`: PASS
- `timeout 60s python scripts/validate_lot2.py`: PASS
- `timeout 60s python scripts/validate_lot3.py`: PASS
- `timeout 60s python scripts/validate_lot4.py`: PASS
- `timeout 60s python scripts/validate_lot5.py`: PASS
- `timeout 300s python scripts/validate_all_until_lot5.py`: PASS
- `CQB_ORCHESTRATOR_MODE=smoke CQB_SKIP_NESTED_PYTEST=1 timeout 30s python scripts/validate_all_until_lot5.py`: PASS
- `python -m pytest -q`: PASS

## Scope control

No Lot 6 work was started.
No strategy, backtest, WebSocket, API call, paper trading, live execution, LONG/SHORT signal, target, label or `future_*` field was added.
