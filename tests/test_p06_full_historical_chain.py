from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_full_lot0_to_lot25_required_chain_executes_under_coverage() -> None:
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
    assert completed.returncode == 0, (
        "Lot 0-25 required chain failed.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}"
    )
    assert "LOT 25 REQUIRED CHAIN: PASS" in completed.stdout
