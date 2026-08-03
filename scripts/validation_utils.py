#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script_streamed(script: str, timeout: int = 60) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT while running {script} after {timeout}s")
        return False

    if result.returncode != 0:
        print(f"FAILED {script} with rc={result.returncode}")
        return False
    return True


# Backward-compatible alias for older callers. It streams output and does not capture pipes.
def run_script(script: str, timeout: int = 60) -> bool:
    return run_script_streamed(script, timeout=timeout)


def run_shell_script(script: str, timeout: int = 300) -> bool:
    try:
        result = subprocess.run(
            ["bash", script],
            cwd=ROOT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT while running {script} after {timeout}s")
        return False

    if result.returncode != 0:
        print(f"FAILED {script} with rc={result.returncode}")
        return False
    return True
