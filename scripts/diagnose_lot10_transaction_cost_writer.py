#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUN_SCRIPT = ROOT / "scripts" / "run_lot10_transaction_costs.py"
VALIDATE_SCRIPT = ROOT / "scripts" / "validate_lot10.py"
OUTPUTS = {
    "5m": ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl",
    "15m": ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl",
}
RUN_RESULT_PATH = ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json"
DATASET_CATALOG_PATH = ROOT / "data" / "audit" / "dataset_catalog.json"
LOT16_MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"
FIXED_TMP_PATHS = [
    ROOT / "data" / "audit" / ".transaction_cost_lot10_5m_estimates.jsonl.tmp",
    ROOT / "data" / "audit" / ".transaction_cost_lot10_15m_estimates.jsonl.tmp",
    ROOT / "data" / "audit" / ".transaction_cost_lot10_run_result.json.tmp",
]
EXPECTED_COUNTS = {"5m": 36, "15m": 12}


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"invalid JSONL row in {path}")
        rows.append(payload)
    return rows


def _run(command: list[str], timeout_seconds: int) -> int:
    result = subprocess.run(command, cwd=ROOT, timeout=timeout_seconds, check=False)
    return int(result.returncode)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fingerprint(path: Path) -> tuple[int, str] | None:
    if not path.exists():
        return None
    return (path.stat().st_size, _sha256(path))


def _validate_outputs() -> int:
    if not RUN_RESULT_PATH.exists():
        print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
        print(f"missing output: {RUN_RESULT_PATH}", flush=True)
        return 1
    payload = json.loads(RUN_RESULT_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
        print(f"invalid JSON object in {RUN_RESULT_PATH}", flush=True)
        return 1
    if _run(["python", str(VALIDATE_SCRIPT)], 60) != 0:
        print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
        print("validate_lot10.py failed", flush=True)
        return 1
    total = 0
    for timeframe, path in OUTPUTS.items():
        if not path.exists():
            print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
            print(f"missing output: {path}", flush=True)
            return 1
        rows = _load_jsonl(path)
        print(f"timeframe={timeframe} rows={len(rows)} path={path}", flush=True)
        if len(rows) != EXPECTED_COUNTS[timeframe]:
            print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
            print(f"unexpected row count for {timeframe}: {len(rows)}", flush=True)
            return 1
        total += len(rows)
    if total != 48:
        print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
        print(f"unexpected total row count: {total}", flush=True)
        return 1
    for path in FIXED_TMP_PATHS:
        if path.exists():
            print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
            print(f"fixed tmp residue detected: {path}", flush=True)
            return 1
    residual_tmp = list((ROOT / "data" / "audit").glob(".transaction_cost_lot10*tmp*"))
    if residual_tmp:
        print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
        print(f"unexpected residual tmp files: {[str(path) for path in residual_tmp]}", flush=True)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate existing Lot 10 transaction cost artifacts without mutating them by default. "
            "Use --rerun only for an explicit Lot 10 rebuild."
        )
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="explicitly rerun Lot 10 before validation; this mode may rewrite Lot 10 artifacts and the dataset catalog",
    )
    args = parser.parse_args()

    tracked_paths = [DATASET_CATALOG_PATH, LOT16_MANIFEST_PATH]
    before_fingerprints = {path: _fingerprint(path) for path in tracked_paths}

    if args.rerun and _run(["python", str(RUN_SCRIPT)], 60) != 0:
        print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
        print("run_lot10_transaction_costs.py failed", flush=True)
        return 1

    validation_rc = _validate_outputs()
    if validation_rc != 0:
        return validation_rc

    if not args.rerun:
        after_fingerprints = {path: _fingerprint(path) for path in tracked_paths}
        for path in tracked_paths:
            if before_fingerprints[path] != after_fingerprints[path]:
                print("DIAGNOSE LOT10 TRANSACTION COST WRITER: FAIL", flush=True)
                print(f"diagnostic mutated tracked artifact: {path}", flush=True)
                return 1
    print("DIAGNOSE LOT10 TRANSACTION COST WRITER: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
