#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.lineage import (
    compute_lot16_source_catalog_checksum,
    count_lot16_source_catalog_entries,
    LOT16_SOURCE_CATALOG_SCOPE,
)
from crypto_quant_bot.lineage.io import load_json

CATALOG_PATH = ROOT / "data" / "audit" / "dataset_catalog.json"
MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"


def fail(message: str) -> int:
    print("DIAGNOSE LOT16 SOURCE CATALOG CHECKSUM: FAIL", flush=True)
    print(message, flush=True)
    return 1


def main() -> int:
    if not CATALOG_PATH.exists():
        return fail(f"missing dataset catalog: {CATALOG_PATH}")
    if not MANIFEST_PATH.exists():
        return fail(f"missing manifest: {MANIFEST_PATH}")
    catalog_payload = load_json(CATALOG_PATH)
    manifest_payload = load_json(MANIFEST_PATH)
    if not isinstance(manifest_payload, dict):
        return fail("reproducibility manifest must be a JSON object")
    try:
        observed_checksum = compute_lot16_source_catalog_checksum(catalog_payload)
        source_catalog_entry_count = count_lot16_source_catalog_entries(catalog_payload)
    except TypeError as exc:
        return fail(str(exc))
    expected_checksum = str(manifest_payload.get("source_catalog_checksum", ""))
    print(f"source_catalog_checksum_expected={expected_checksum}", flush=True)
    print(f"source_catalog_checksum_observed={observed_checksum}", flush=True)
    print(f"source_catalog_scope={LOT16_SOURCE_CATALOG_SCOPE}", flush=True)
    print(f"source_catalog_entry_count={source_catalog_entry_count}", flush=True)
    if manifest_payload.get("source_catalog_scope") != LOT16_SOURCE_CATALOG_SCOPE:
        return fail(f"unexpected source_catalog_scope: {manifest_payload.get('source_catalog_scope')}")
    if manifest_payload.get("reproducibility_scope_lot16") != LOT16_SOURCE_CATALOG_SCOPE:
        return fail(f"unexpected reproducibility_scope_lot16: {manifest_payload.get('reproducibility_scope_lot16')}")
    if manifest_payload.get("source_catalog_entry_count") != source_catalog_entry_count:
        return fail("source_catalog_entry_count mismatch")
    if expected_checksum != observed_checksum:
        return fail("source_catalog_checksum mismatch")
    result = subprocess.run(
        ["python", "scripts/validate_lot16.py"],
        cwd=ROOT,
        timeout=60,
        check=False,
    )
    if int(result.returncode) != 0:
        return fail(f"validate_lot16.py returned rc={int(result.returncode)}")
    print("DIAGNOSE LOT16 SOURCE CATALOG CHECKSUM: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
