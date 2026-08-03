#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
PER_FILE_TIMEOUT_SECONDS = 30
GLOBAL_TIMEOUT_SECONDS = 180


def main() -> int:
    env = os.environ.copy()
    env["CQB_SKIP_NESTED_PYTEST"] = "1"
    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    for test_file in test_files:
        print(f"=== PYTEST FILE {test_file.name} ===", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *[str(path) for path in test_files]],
            cwd=ROOT,
            env=env,
            timeout=GLOBAL_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("DIAGNOSE PYTEST AFTER CHAIN: TIMEOUT global pytest run", flush=True)
        return 1
    if result.returncode != 0:
        print("DIAGNOSE PYTEST AFTER CHAIN: FAIL global pytest run", flush=True)
        return int(result.returncode)
    print("DIAGNOSE PYTEST AFTER CHAIN: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
