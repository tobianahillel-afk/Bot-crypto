# Acceptance Criteria — Lot 6

Lot 6 is accepted only if:

```text
contracts/regime.py exists
src/crypto_quant_bot/regime/ exists
config/regime.yaml exists
build_lot6_regime.py exists
validate_lot6.py exists
5m regime dataset has 36 rows
15m regime dataset has 12 rows
regime_state values are authorized
scores are bounded
components is a dict
used_for_decision=false
no future_*, target, label or LONG/SHORT signal exists
reports are generated
catalog contains Lot 6 datasets
previous validations still pass
orchestrator Lot 6 fast and smoke pass
pytest passes
```
