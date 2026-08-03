# Lot 4-septies Validation Report

Status: PASS

## Context

Lot 4-sexies removed the pytest deselection filter and ensured the orchestrator test was included in the default pytest run.

However, the full CI chain could still block because `scripts/validate_lot2.py` still contained nested validation logic using `subprocess.run(..., capture_output=True)` and called previous validation scripts.

## Correction

Lot 4-septies removes nested validations from individual lot validators.

Rules now enforced:

- each `validate_lotX.py` validates only its own lot;
- no `validate_lotX.py` calls another validate script;
- no `capture_output=True` is used in lot validation scripts;
- `validate_all_until_lot4.py` / `.sh` is the only multi-lot orchestrator;
- the complete CI chain terminates under timeout.

## Validated Commands

```bash
timeout 60s python scripts/build_lot3_pivots.py
timeout 60s python scripts/build_lot4_volume_vwap.py
timeout 60s python scripts/validate_lot2.py
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
python -m pytest -q
```

The full command chain also passes:

```bash
timeout 300s bash -lc '
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
'
```

## Result

```text
LOT 4-septies VALIDATION: PASS
pytest: all tests passed
no validation timeout
no skipped orchestrator test
no deselected orchestrator test
no nested validate subprocess
```

## Scope Preservation

No Lot 5 was started. No trading signal, target, label, future field, backtest, WebSocket, API call, paper trading, ML, AI/news, or live execution was added.
