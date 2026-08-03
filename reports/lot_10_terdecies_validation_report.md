# Lot 10-terdecies — Validation Report

## Scope

Lot 10-terdecies is a non-functional CI termination correction for Crypto Quant Bot V3.1-Ops. It does not start Lot 11 and does not change Transaction Costs V0 business behavior.

## Audit finding addressed

Lot 10-duodecies added post-pytest diagnostics, but the chef de projet audit detected artificial stdout/stderr termination workarounds in active scripts. Those hacks used helpers and file-descriptor redirection to `/dev/null` after PASS markers.

Examples removed from active code:

```text
close_standard_streams
os.open(os.devnull
os.dup2(
devnull_fd
stdout=subprocess.DEVNULL
stderr=subprocess.DEVNULL
stdin=subprocess.DEVNULL
```

These patterns were removed because they can mask the real process-tree state and can make long shell chains unstable.

## Corrections

- Removed stdout/stderr detach helper functions from active Lot 0 to Lot 10 scripts.
- Removed manual `/dev/null` file-descriptor redirection.
- Removed `sitecustomize.py`; pytest now resolves normally to the installed pytest package.
- Kept the natural termination pattern: `raise SystemExit(main())`.
- Added `tests/test_no_stdout_stderr_detach_hacks.py` to prevent reintroduction of the detach hacks.
- Kept Transaction Costs V0 unchanged.

## Proof commands

```bash
timeout 60s python scripts/diagnose_pytest_resolution.py
timeout 300s python scripts/diagnose_lot7_build_after_chain.py
timeout 300s python scripts/diagnose_lot8_no_lookahead_after_chain.py
timeout 300s python scripts/diagnose_exact_chain_until_lot10.py
timeout 300s python scripts/diagnose_after_pytest_lingering.py
timeout 300s python scripts/diagnose_exact_chain_return_shell.py
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
```

Exact chain proof:

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
python scripts/build_lot6_regime.py &&
python scripts/validate_lot6.py &&
python scripts/build_lot7_market_state.py &&
python scripts/validate_lot7.py &&
python scripts/audit_lot8_feature_registry.py &&
python scripts/audit_lot8_no_lookahead.py &&
python scripts/validate_lot8.py &&
python scripts/run_lot9_backtest_replay.py &&
python scripts/validate_lot9.py &&
python scripts/run_lot10_transaction_costs.py &&
python scripts/validate_lot10.py &&
python -m pytest -q &&
echo EXACT_CHAIN_DONE
'
```

## Observed results

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

Command return codes:

```text
01_diagnose_pytest_resolution: rc=0 duration=2s
02_diagnose_lot7_build_after_chain: rc=0 duration=23s
03_diagnose_lot8_no_lookahead_after_chain: rc=0 duration=27s
04_diagnose_exact_chain_until_lot10: rc=0 duration=39s
05_diagnose_after_pytest_lingering: rc=0 duration=16s
06_diagnose_exact_chain_return_shell: rc=0 duration=41s
07_pytest: rc=0 duration=3s
08_exact_chain: rc=0 duration=33s
```

## Invariants

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

No strategy, order, fill, exploitable PnL, paper trading, LONG/SHORT signal, target, label, future_* field, API call or WebSocket was added.
