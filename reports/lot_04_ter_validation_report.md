# Lot 4-quater Validation Report

## Scope

Lot 4-quater corrige définitivement l'orchestrateur de validation jusqu'au Lot 4 sans modifier le périmètre fonctionnel du Lot 4.

No trading, no strategy, no backtest, no WebSocket, no API call, no paper trading, no live execution.

## Root cause

The previous Python orchestrator still relied on a complex subprocess loop and could timeout during the full validation chain, around `scripts/build_lot3_pivots.py` or before the next step. Pytest also did not prove the orchestrator path because the real orchestrator test could be skipped unless an environment flag was set.

## Correction applied

- Added `scripts/validate_all_until_lot4.sh` as the authoritative simple Bash orchestrator.
- Replaced `scripts/validate_all_until_lot4.py` with a minimal Python delegate to the Bash script.
- Removed Python subprocess orchestration loops from the Python wrapper.
- Removed `capture_output=True`, `Popen`, and `os.exec*` from the Python wrapper.
- Added explicit per-step timeouts in the Bash orchestrator.
- Preserved `CQB_SKIP_NESTED_PYTEST=1` for pytest recursion protection.
- Updated orchestrator tests so pytest no longer skips the real orchestrator validation.
- Shared one real session-scoped orchestrator execution between orchestrator tests to avoid duplicated long subprocess chains inside pytest.

## Commands validated

```bash
python scripts/validate_lot0.py
python scripts/ingest_ohlcvt_fixture.py
python scripts/validate_lot1.py
python scripts/build_lot2_datasets.py
python scripts/validate_lot2.py
python scripts/build_lot3_pivots.py
python scripts/validate_lot3.py
python scripts/build_lot4_volume_vwap.py
python scripts/validate_lot4.py
python -m pytest -q

timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
timeout 300s bash -lc '<full validation chain>'
```

## Result

All required commands terminate without validation timeout.

```text
LOT 4-quater VALIDATION: PASS
pytest: all tests passed
no validation timeout
```

## Defensive invariants

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```
