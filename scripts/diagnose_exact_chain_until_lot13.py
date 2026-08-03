#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

EXACT_CHAIN = """
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
python scripts/run_lot11_risk_engine.py &&
python scripts/validate_lot11.py &&
python scripts/run_lot12_exposure_guard.py &&
python scripts/validate_lot12.py &&
python scripts/run_lot13_portfolio_freeze.py &&
python scripts/validate_lot13.py &&
python -m pytest -q &&
echo EXACT_CHAIN_LOT13_DONE
""".strip()


def main() -> int:
    print("BEFORE:exact_chain_lot13", flush=True)
    print("COMMAND:exact_chain_lot13:bash -lc <exact Lot 0 to Lot 13 chain>", flush=True)
    print("EXPECTED_MARKER:exact_chain_lot13:EXACT_CHAIN_LOT13_DONE", flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(
            ["bash", "-lc", EXACT_CHAIN],
            cwd=ROOT,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - started
        print(f"TIMEOUT:exact_chain_lot13:rc=124:duration_seconds={duration:.3f}", flush=True)
        print("DIAGNOSE EXACT CHAIN LOT13: FAIL", flush=True)
        return 124
    duration = time.monotonic() - started
    rc = int(result.returncode)
    print(f"AFTER:exact_chain_lot13:rc={rc}:duration_seconds={duration:.3f}", flush=True)
    if rc != 0:
        print("DIAGNOSE EXACT CHAIN LOT13: FAIL", flush=True)
        return rc
    print("DIAGNOSE EXACT CHAIN LOT13: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
