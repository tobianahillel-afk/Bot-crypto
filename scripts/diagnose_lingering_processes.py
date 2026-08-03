#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT_SECONDS = 30


def flush_streams() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def main(argv: list[str]) -> int:
    command = argv if argv else [sys.executable, "-c", "print('diagnose child process completed', flush=True)"]
    print("BEFORE:diagnose_lingering_processes", flush=True)
    print(f"COMMAND:diagnose_lingering_processes:{' '.join(command)}", flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - started
        print(
            f"TIMEOUT:diagnose_lingering_processes:rc=124:duration_seconds={duration:.3f}:timeout_seconds={DEFAULT_TIMEOUT_SECONDS}",
            flush=True,
        )
        flush_streams()
        return 124
    duration = time.monotonic() - started
    rc = int(result.returncode)
    print(f"AFTER:diagnose_lingering_processes:rc={rc}:duration_seconds={duration:.3f}", flush=True)
    if rc != 0:
        print(f"DIAGNOSE LINGERING PROCESSES: FAIL rc={rc}", flush=True)
        flush_streams()
        return rc
    print("DIAGNOSE LINGERING PROCESSES: PASS", flush=True)
    flush_streams()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
