#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = tuple(f"scripts/validate_lot{lot}.py" for lot in range(31, 37))


class ChainValidationError(RuntimeError):
    """Raised when any required V3 lot validator fails."""


def run_validator(path: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ChainValidationError(f"{path} failed: {detail}")
    output = completed.stdout.strip().splitlines()
    if not output:
        raise ChainValidationError(f"{path} produced no validation evidence")
    payload = json.loads(output[-1])
    if not isinstance(payload, dict) or payload.get("status") != "PASS":
        raise ChainValidationError(f"{path} did not produce PASS evidence")
    return payload


def validate_chain() -> dict[str, object]:
    results = {path: run_validator(path) for path in VALIDATORS}
    return {
        "schema_version": "lot36-required-chain-validation-v1",
        "status": "PASS",
        "validated_lots": list(range(31, 37)),
        "validator_count": len(results),
        "validators": results,
        "v3_closed": False,
        "post_merge_audit_required": True,
        "next_lot": 37,
        "next_lot_status": "PLANNED_LOCKED",
    }


def main() -> int:
    try:
        print(json.dumps(validate_chain(), sort_keys=True))
    except (ChainValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT36 REQUIRED CHAIN: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
