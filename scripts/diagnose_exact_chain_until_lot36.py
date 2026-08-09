#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = tuple(f"scripts/validate_lot{lot}.py" for lot in range(31, 37))


def diagnose() -> dict[str, object]:
    results: list[dict[str, object]] = []
    for path in VALIDATORS:
        completed = subprocess.run(
            [sys.executable, path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        results.append(
            {
                "validator": path,
                "return_code": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
    return {
        "schema_version": "lot36-chain-diagnostic-v1",
        "all_passed": all(item["return_code"] == 0 for item in results),
        "results": results,
    }


def main() -> int:
    payload = diagnose()
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
