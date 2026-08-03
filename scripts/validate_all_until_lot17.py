#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

STEPS: list[tuple[list[str], int]] = [
    (["python", "scripts/validate_all_until_lot16.py"], 300),
    (["python", "scripts/run_lot17_health_monitor.py"], 60),
    (["python", "scripts/validate_lot17.py"], 60),
]


def main() -> int:
    for command, timeout_seconds in STEPS:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        if result.returncode != 0:
            return int(result.returncode)
    print("LOT 17 ORCHESTRATED VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
