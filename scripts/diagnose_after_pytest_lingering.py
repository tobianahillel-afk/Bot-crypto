#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_TIMEOUT_SECONDS = 240

SEQUENCES: list[tuple[str, str, str]] = [
    ("pytest_only", "python -m pytest -q && echo PYTEST_DONE", "PYTEST_DONE"),
    (
        "pytest_after_lot10",
        "python scripts/run_lot10_transaction_costs.py && "
        "python scripts/validate_lot10.py && "
        "python -m pytest -q && "
        "echo PYTEST_AFTER_LOT10_DONE",
        "PYTEST_AFTER_LOT10_DONE",
    ),
]


def flush_streams() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def run_sequence(label: str, command: str, marker: str) -> int:
    print(f"BEFORE:{label}", flush=True)
    print(f"COMMAND:{label}:bash -lc {command}", flush=True)
    print(f"EXPECTED_MARKER:{label}:{marker}", flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(
            ["bash", "-lc", command],
            cwd=ROOT,
            timeout=GLOBAL_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - started
        print(
            f"TIMEOUT:{label}:rc=124:duration_seconds={duration:.3f}:timeout_seconds={GLOBAL_TIMEOUT_SECONDS}",
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
    for label, command, marker in SEQUENCES:
        rc = run_sequence(label, command, marker)
        if rc != 0:
            print(f"DIAGNOSE AFTER PYTEST LINGERING: FAIL sequence={label} rc={rc}", flush=True)
            return rc
    print("DIAGNOSE AFTER PYTEST LINGERING: PASS", flush=True)
    flush_streams()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
