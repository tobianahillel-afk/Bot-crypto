#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

STEPS: list[tuple[list[str], int]] = [
    (["python", "scripts/validate_all_until_lot23.py"], 300),
    (["python", "scripts/diagnose_lot7_market_state_jsonl.py"], 60),
    (["python", "scripts/diagnose_lot10_transaction_cost_writer.py"], 60),
    (["python", "scripts/diagnose_lot16_source_catalog_checksum.py"], 60),
    (["python", "scripts/validate_v1_archive_frozen.py"], 120),
    (["python", "scripts/run_lot24_trend_range_momentum.py"], 60),
    (["python", "scripts/validate_lot24.py"], 60),
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
    print("LOT 24 ORCHESTRATED VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
