#!/usr/bin/env python3
from __future__ import annotations

import shutil
import tarfile
import tempfile
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.closure import (
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
    LEGACY_ACTIVE_TEST_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    RENAMED_ACTIVE_TEST_PATH,
)
from crypto_quant_bot.data.checksum import sha256_file

REQUIRED_PREFIXES = [
    "src/",
    "scripts/",
    "tests/",
    "docs/",
    "reports/",
    "data/audit/",
]
REQUIRED_EXTRACTED_PATHS = [
    "src/crypto_quant_bot/closure/archive.py",
    "src/crypto_quant_bot/closure/io.py",
    "scripts/run_lot20_v1_closure.py",
    "scripts/validate_lot20.py",
    "scripts/validate_lot20_archive_extracted.py",
    "docs/LOT_20_V1_CLOSURE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_20.md",
    "reports/lot_19_release_candidate_report.md",
    "reports/lot_18_validation_report.md",
    "data/audit/release_candidate_lot19.json",
    "data/audit/no_trading_compliance_lot18.json",
]
STAGED_RELATIVE_PATHS = [
    LOT20_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
]


def fail(message: str) -> int:
    print("LOT 20 ARCHIVE EXTRACTED VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def _copy_into_extraction(extracted_root: Path, relative_path: str) -> None:
    source_path = ROOT / relative_path
    target_path = extracted_root / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def main() -> int:
    archive_path = ROOT / ARCHIVE_OUTPUT_PATH
    sha256_path = ROOT / ARCHIVE_SHA256_OUTPUT_PATH
    if not archive_path.exists():
        return fail(f"missing archive: {ARCHIVE_OUTPUT_PATH}")
    if not sha256_path.exists():
        return fail(f"missing sha256 sidecar: {ARCHIVE_SHA256_OUTPUT_PATH}")

    observed_archive_checksum = sha256_file(archive_path)
    expected_sha_line = f"{observed_archive_checksum}  {archive_path.name}"
    if sha256_path.read_text(encoding="utf-8").strip() != expected_sha_line:
        return fail("archive sha256 sidecar mismatch")

    with tarfile.open(archive_path, "r:gz") as archive_handle:
        member_names = sorted(archive_handle.getnames())
        for prefix in REQUIRED_PREFIXES:
            if not any(name.startswith(prefix) for name in member_names):
                return fail(f"archive missing required prefix: {prefix}")
        if RENAMED_ACTIVE_TEST_PATH not in member_names:
            return fail("renamed active test is missing from archive")
        if LEGACY_ACTIVE_TEST_PATH in member_names:
            return fail("legacy long-named test is still present in archive")
        with tempfile.TemporaryDirectory(prefix="cqb_lot20_archive_", dir="/tmp") as tmp_dir:
            extracted_root = Path(tmp_dir)
            archive_handle.extractall(extracted_root, filter="data")

            for prefix in REQUIRED_PREFIXES:
                if not (extracted_root / prefix).exists():
                    return fail(f"extracted archive missing path: {prefix}")
            for relative_path in REQUIRED_EXTRACTED_PATHS:
                if not (extracted_root / relative_path).exists():
                    return fail(f"extracted archive missing critical path: {relative_path}")
            if not (extracted_root / RENAMED_ACTIVE_TEST_PATH).exists():
                return fail("renamed active test is missing after extraction")
            if (extracted_root / LEGACY_ACTIVE_TEST_PATH).exists():
                return fail("legacy long-named test is still present after extraction")

            for relative_path in STAGED_RELATIVE_PATHS:
                _copy_into_extraction(extracted_root, relative_path)

            validate_result = subprocess.run(
                ["python", "scripts/validate_lot20.py"],
                cwd=extracted_root,
                timeout=60,
                check=False,
            )
            if validate_result.returncode != 0:
                return int(validate_result.returncode)

            pytest_result = subprocess.run(
                ["python", "-m", "pytest", "-q"],
                cwd=extracted_root,
                timeout=120,
                check=False,
            )
            if pytest_result.returncode != 0:
                return int(pytest_result.returncode)

    print("LOT 20 ARCHIVE EXTRACTED VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
