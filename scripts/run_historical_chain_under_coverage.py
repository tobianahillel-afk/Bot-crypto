#!/usr/bin/env python3
"""Run the complete Lot 0-25 required chain as a CI integration proof."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        ["bash", "scripts/run_required_chain_until_lot25.sh"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=360,
        check=False,
    )
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=__import__("sys").stderr)
    if completed.returncode != 0:
        return completed.returncode
    if "LOT 25 REQUIRED CHAIN: PASS" not in completed.stdout:
        print("HISTORICAL_CHAIN_PASS_MARKER_MISSING", file=__import__("sys").stderr)
        return 1
    print("P0_6_HISTORICAL_CHAIN: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
