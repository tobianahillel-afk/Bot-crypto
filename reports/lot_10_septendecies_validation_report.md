# Lot 10-septendecies Validation Report

## Scope

Lot 10-septendecies is limited to diagnosis and stabilization of the Lot 5 diagnostic return-to-shell behavior. It does not start Lot 11 and does not modify Transaction Costs V0 business logic.

## Background

Lot 10-sexdecies removed `subprocess.Popen`, process groups and manual signal handling from the active diagnostics. The next project-manager audit showed that `scripts/diagnose_lot5_validate_after_chain.py` could print `DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS` and the wrapper could print `DIAG5_DONE`, while the external process still did not return reliably.

## Added owner diagnostic

Added:

```text
scripts/diagnose_lot5_fd_lingering_owner.py
```

The diagnostic executes the exact Lot 0 → Lot 5 sequence progressively and inspects `/proc` after each step for:

```text
- direct or indirect descendants of the diagnostic process;
- project-related Python processes still alive;
- inherited stdout/stderr fd links when visible through /proc.
```

It uses stdlib only and does not use PIPE capture, DEVNULL redirection, `os._exit`, `signal.alarm`, stdout/stderr detaches, process groups or artificial kill logic.

## Owner result

In the final local validation, the diagnostic found no lingering owner after any step:

```text
NO_LINGERING_AFTER:validate_lot0
NO_LINGERING_AFTER:ingest_ohlcvt_fixture
NO_LINGERING_AFTER:validate_lot1
NO_LINGERING_AFTER:build_lot2_datasets
NO_LINGERING_AFTER:validate_lot2
NO_LINGERING_AFTER:build_lot3_pivots
NO_LINGERING_AFTER:validate_lot3
NO_LINGERING_AFTER:build_lot4_volume_vwap
NO_LINGERING_AFTER:validate_lot4
NO_LINGERING_AFTER:build_lot5_volatility
NO_LINGERING_AFTER:validate_lot5
DIAGNOSE LOT5 FD LINGERING OWNER: PASS
```

Therefore no child script in the Lot 0 → Lot 5 sequence was modified blindly. The observed owner in the final archive is `none detected`.

## Static safeguards

Added:

```text
tests/test_no_background_process_or_fd_hacks.py
tests/test_lot5_diagnostics_return_shell_static.py
```

These tests guard against background process/fd hacks and ensure the Lot 5 diagnostic keeps a simple `subprocess.run(..., timeout=..., check=False)` pattern with natural `raise SystemExit(main())` exit.

## Command evidence

```text
timeout 60s python scripts/diagnose_pytest_resolution.py                         rc=0
timeout 120s python scripts/diagnose_lot5_fd_lingering_owner.py                  rc=0
timeout 120s bash -lc 'python scripts/diagnose_lot5_validate_after_chain.py; echo DIAG5_DONE' rc=0
timeout 300s python scripts/diagnose_lot4_validate_after_chain.py                rc=0
timeout 300s python scripts/diagnose_lot5_validate_after_chain.py                rc=0
timeout 300s python scripts/diagnose_lot7_build_after_chain.py                   rc=0
timeout 300s python scripts/diagnose_lot8_no_lookahead_after_chain.py            rc=0
timeout 300s python scripts/diagnose_exact_chain_until_lot10.py                  rc=0
timeout 300s python scripts/diagnose_after_pytest_lingering.py                   rc=0
timeout 300s python scripts/diagnose_exact_chain_return_shell.py                 rc=0
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'                    rc=0
exact Lot 0 → Lot 10 chain                                                        rc=0
```

Required markers obtained:

```text
DIAGNOSE PYTEST RESOLUTION: PASS
DIAGNOSE LOT5 FD LINGERING OWNER: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAG5_DONE
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
169 passed
```

## Safety invariants

Unchanged:

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

## Business logic

No trading strategy, order, exploitable simulated order, exploitable PnL, paper trading, LONG/SHORT signal, target, label, `future_*`, API call or WebSocket was added.
