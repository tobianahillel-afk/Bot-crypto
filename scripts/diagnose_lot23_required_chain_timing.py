#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str], timeout_seconds: int) -> int:
    print(f"=== TIMING {label} ===", flush=True)
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, timeout=timeout_seconds, check=False)
    duration = time.monotonic() - started
    status = "OK" if result.returncode == 0 else "FAIL"
    print(f"step={label} duration_seconds={duration:.3f} rc={result.returncode} status={status}", flush=True)
    return int(result.returncode)


def main() -> int:
    rc = run_step("lot23_required_chain", ["bash", "scripts/run_required_chain_until_lot23.sh"], 300)
    if rc != 0:
        return rc
    print("DIAGNOSE LOT23 REQUIRED CHAIN TIMING: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
