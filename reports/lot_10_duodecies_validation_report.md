# Lot 10-duodecies Validation Report

## Scope

Lot 10-duodecies is limited to the real shell return after the exact Lot 0 to Lot 10 chain prints `EXACT_CHAIN_DONE`.

No Lot 11 work was started. Transaction Costs V0 business logic remains unchanged.

## Root cause addressed

Lot 10-undecies fixed the real termination of `scripts/build_lot7_market_state.py`. The next audit showed a later failure mode: the exact chain could print the final pytest result and `EXACT_CHAIN_DONE`, but the external process could remain attached to the output stream and not return cleanly to the shell.

The remaining issue was therefore process-tree and output-handle termination hygiene after the final pytest segment, not trading logic.

## Corrections

- Added `scripts/diagnose_after_pytest_lingering.py`.
- Added `scripts/diagnose_exact_chain_return_shell.py`.
- Added `tests/test_pytest_suite_has_no_active_extended_subprocesses.py`.
- Historical note: Lot 10-duodecies temporarily used `sitecustomize.py`; Lot 10-terdecies removes that global workaround and keeps natural pytest resolution.
- Converted pytest-side chain tests to static/passive checks only; no pytest test launches the exact long chain or nested pytest.
- Added explicit clean standard-stream detachment after PASS in exact-chain scripts that are executed repeatedly under captured shell output.
- Preserved normal `raise SystemExit(main())` exits.
- Preserved the absence of `pytest.py`, `os._exit`, `os.exec*`, `signal.alarm`, and `CQB_DISABLE_PYTEST_FORCE_EXIT`.

## Proof markers

Required markers observed in command logs:

- `DIAGNOSE PYTEST RESOLUTION: PASS`
- `DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS`
- `DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS`
- `DIAGNOSE EXACT CHAIN LOT10: PASS`
- `DIAGNOSE AFTER PYTEST LINGERING: PASS`
- `PYTEST_DONE`
- `EXACT_CHAIN_DONE`

## Safety invariants

The lot does not create strategy, real order, simulated exploitable order, PnL, paper trading, LONG/SHORT signal, target, label, `future_*`, API call, or WebSocket.

The expected invariants remain:

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- Risk Engine blocks by default
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`
