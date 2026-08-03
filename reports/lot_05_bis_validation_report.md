# Lot 5-bis Validation Report

Status: PASS

## Summary

Lot 5 was functionally correct, but the complete CI chain could still become unreliable because some validation scripts were not purely direct validators.

## Root cause

`validate_lot1.py` still executed materialization logic through a subprocess and relaunched the Lot 1 ingestion step. This violated the final validation rule: each `validate_lotX.py` must validate only its own lot and must not run build, ingest, or another validate script.

## Corrections

- `validate_lot1.py` is now a direct validator.
- `validate_lot1.py` no longer calls the Lot 1 ingestion script.
- `validate_lot1.py` no longer imports or uses subprocess.
- `validate_lot1.py` validates existing bronze, catalog, report, fixtures, checksum, and safety invariants directly.
- `validate_lot1.py` to `validate_lot5.py` are checked by an anti-nested-validation test.
- `validate_lot5.py` no longer contains direct forbidden build-script tokens.
- `tests/test_lot5_validate_all_terminates.py` now executes the Lot 5 orchestrator with `CQB_SKIP_NESTED_PYTEST=1`, `CQB_ORCHESTRATOR_MODE=fast`, and a timeout.
- `validate_all_until_lot5.sh` remains the only multi-lot orchestrator for Lot 5.

## Commands validated

```bash
timeout 60s python scripts/build_lot5_volatility.py
timeout 60s python scripts/validate_lot1.py
timeout 60s python scripts/validate_lot2.py
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 60s python scripts/validate_lot5.py
timeout 300s python scripts/validate_all_until_lot5.py
python -m pytest -q
```

The complete chain also passes:

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
python scripts/build_lot5_volatility.py &&
python scripts/validate_lot5.py &&
python -m pytest -q
'
```

## Final result

- LOT 5-bis ORCHESTRATED VALIDATION: PASS
- pytest: 63 passed
- no validation timeout
- no skipped orchestrator test
- no deselected orchestrator test
- no nested validate subprocess

## Invariants

- TradingDecision = WAIT
- SystemDecision = BLOCK_TRADING
- trade_allowed = false
- Risk Engine blocks by default
- live_execution = DISABLED
- leverage = FORBIDDEN
