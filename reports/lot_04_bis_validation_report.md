# Lot 4-bis Validation Robustness Report

Status: PASS

Scope:
- Validation robustness only.
- No trading feature added.
- No strategy, no backtest, no WebSocket, no API, no paper trading, no live execution.

Corrections:
- `scripts/validate_lot3.py` now validates directly and no longer runs nested subprocess chains.
- `scripts/validate_lot4.py` now validates directly and no longer calls `validate_lot3.py` or build scripts.
- `scripts/validate_all_until_lot4.py` orchestrates full validation with explicit timeouts.
- `scripts/validation_utils.py` handles subprocess timeouts and failures cleanly.
- Validation replay output is stable: `data/audit/replay_validation/latest_validation_replay.json`.
- Uncontrolled `reports/replay_*.json` artifacts were removed from the validation output area.

Timeout checks:
- `timeout 60s python scripts/validate_lot3.py`: PASS
- `timeout 60s python scripts/build_lot4_volume_vwap.py`: PASS
- `timeout 60s python scripts/validate_lot4.py`: PASS
- `timeout 180s python -m pytest -q`: PASS
- `timeout 300s python scripts/validate_all_until_lot4.py`: PASS

Full command chain:

```bash
python scripts/validate_lot0.py &&
python scripts/ingest_ohlcvt_fixture.py &&
python scripts/validate_lot1.py &&
python scripts/build_lot2_datasets.py &&
python scripts/validate_lot2.py &&
python scripts/build_lot3_pivots.py &&
python scripts/validate_lot3.py &&
python scripts/build_lot4_volume_vwap.py &&
python scripts/validate_lot4.py &&
python -m pytest -q
```

Result:

```text
LOT 0 VALIDATION: PASS
LOT 1 FIXTURE INGESTION: PASS
LOT 1 VALIDATION: PASS
LOT 2 DATASET BUILD: PASS
LOT 2 VALIDATION: PASS
LOT 3 PIVOT BUILD: PASS
LOT 3 VALIDATION: PASS
LOT 4 VOLUME/VWAP BUILD: PASS
LOT 4 VALIDATION: PASS
43 passed
```

Safety invariants:
- TradingDecision = WAIT
- SystemDecision = BLOCK_TRADING
- trade_allowed = false
- Risk Engine blocks by default
- live_execution = DISABLED
- leverage = FORBIDDEN

Final result:

```text
LOT 4-bis VALIDATION: PASS
```

## Superseded by Lot 4-quater

Lot 4-bis improved direct validations, but the full Python orchestrator could still timeout in audit conditions.
Lot 4-quater supersedes the orchestrator implementation by using a Bash orchestrator and a minimal Python delegate.
