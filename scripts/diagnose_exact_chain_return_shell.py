#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 300

EXACT_CHAIN = r'''
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
python scripts/diagnose_lot7_market_state_jsonl.py &&
python scripts/audit_lot8_feature_registry.py &&
python scripts/audit_lot8_no_lookahead.py &&
python scripts/validate_lot8.py &&
python scripts/run_lot9_backtest_replay.py &&
python scripts/validate_lot9.py &&
python scripts/run_lot10_transaction_costs.py &&
python scripts/validate_lot10.py &&
# Refresh Lot 16 lineage after the exact Lot 10 chain so full pytest
# still sees a coherent reproducibility manifest in the current workspace.
python scripts/run_lot16_reproducibility_manifest.py &&
python scripts/validate_lot16.py &&
python scripts/diagnose_lot16_source_catalog_checksum.py &&
python scripts/run_lot17_health_monitor.py &&
python scripts/validate_lot17.py &&
python -m pytest -q &&
echo EXACT_CHAIN_DONE
'''


def flush_streams() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def main() -> int:
    print("BEFORE:exact_chain_return_shell", flush=True)
    print(
        "COMMAND:exact_chain_return_shell:bash -lc <exact Lot 0 to Lot 10 chain + Lot 16 refresh/checksum + Lot 17 refresh + pytest>",
        flush=True,
    )
    print("EXPECTED_MARKER:exact_chain_return_shell:EXACT_CHAIN_DONE", flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(
            ["bash", "-lc", EXACT_CHAIN],
            cwd=ROOT,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - started
        print(
            f"TIMEOUT:exact_chain_return_shell:rc=124:duration_seconds={duration:.3f}:timeout_seconds={TIMEOUT_SECONDS}",
            flush=True,
        )
        flush_streams()
        return 124
    duration = time.monotonic() - started
    rc = int(result.returncode)
    print(f"AFTER:exact_chain_return_shell:rc={rc}:duration_seconds={duration:.3f}", flush=True)
    if rc != 0:
        print(f"DIAGNOSE EXACT CHAIN RETURN SHELL: FAIL rc={rc}", flush=True)
        flush_streams()
        return rc
    print("DIAGNOSE EXACT CHAIN RETURN SHELL: PASS", flush=True)
    flush_streams()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
