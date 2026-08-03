#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

STEPS: list[tuple[str, list[str], int]] = [
    ('validate_lot0', ['python', 'scripts/validate_lot0.py'], 60),
    ('ingest_ohlcvt_fixture', ['python', 'scripts/ingest_ohlcvt_fixture.py'], 60),
    ('validate_lot1', ['python', 'scripts/validate_lot1.py'], 60),
    ('build_lot2_datasets', ['python', 'scripts/build_lot2_datasets.py'], 60),
    ('validate_lot2', ['python', 'scripts/validate_lot2.py'], 60),
    ('build_lot3_pivots', ['python', 'scripts/build_lot3_pivots.py'], 60),
    ('validate_lot3', ['python', 'scripts/validate_lot3.py'], 60),
    ('build_lot4_volume_vwap', ['python', 'scripts/build_lot4_volume_vwap.py'], 60),
    ('validate_lot4', ['python', 'scripts/validate_lot4.py'], 60),
    ('build_lot5_volatility', ['python', 'scripts/build_lot5_volatility.py'], 60),
    ('validate_lot5', ['python', 'scripts/validate_lot5.py'], 60),
    ('build_lot6_regime', ['python', 'scripts/build_lot6_regime.py'], 60),
    ('validate_lot6', ['python', 'scripts/validate_lot6.py'], 60),
    ('build_lot7_market_state', ['python', 'scripts/build_lot7_market_state.py'], 60),
    ('validate_lot7', ['python', 'scripts/validate_lot7.py'], 60),
    ('audit_lot8_feature_registry', ['python', 'scripts/audit_lot8_feature_registry.py'], 60),
    ('audit_lot8_no_lookahead', ['python', 'scripts/audit_lot8_no_lookahead.py'], 60),
    ('validate_lot8', ['python', 'scripts/validate_lot8.py'], 60),
    ('run_lot9_backtest_replay', ['python', 'scripts/run_lot9_backtest_replay.py'], 60),
    ('validate_lot9', ['python', 'scripts/validate_lot9.py'], 60),
    ('run_lot10_transaction_costs', ['python', 'scripts/run_lot10_transaction_costs.py'], 60),
    ('validate_lot10', ['python', 'scripts/validate_lot10.py'], 60),
    ('pytest', ['python', '-m', 'pytest', '-q'], 120),
]


def flush_streams() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def run_step(label: str, command: list[str], timeout_seconds: int) -> int:
    print(f"BEFORE:{label}", flush=True)
    print(f"COMMAND:{label}:{' '.join(command)}", flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - started
        print(
            f"TIMEOUT:{label}:rc=124:duration_seconds={duration:.3f}:timeout_seconds={timeout_seconds}",
            flush=True,
        )
        flush_streams()
        return 124
    duration = time.monotonic() - started
    rc = int(result.returncode)
    print(f"AFTER:{label}:rc={rc}:duration_seconds={duration:.3f}", flush=True)
    flush_streams()
    return rc


def main() -> int:
    for label, command, timeout_seconds in STEPS:
        rc = run_step(label, command, timeout_seconds)
        if rc != 0:
            print(f"DIAGNOSE EXACT CHAIN LOT10: FAIL first_step={label} rc={rc}", flush=True)
            return rc
    print("DIAGNOSE EXACT CHAIN LOT10: PASS", flush=True)
    flush_streams()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
