#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tarfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.checksum import sha256_file

ARCHIVE_RELATIVE_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
ARCHIVE_SHA256_RELATIVE_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
FREEZE_REPORT_RELATIVE_PATH = "reports/lot_21_v1_archive_freeze_report.md"
PROJECT_MANAGER_APPROVED_SHA256 = "372f6e85353ce147766a4d4d724096aabb820c0872bffad14bf70a56f62d162d"
PROJECT_MANAGER_APPROVED_SIZE_BYTES = 365440
LEGACY_CLOSURE_STEP = "run_lot20_" "v1_closure.py"
LEGACY_CLOSURE_DISPLAY = "scripts/" + LEGACY_CLOSURE_STEP
CHAIN_REQUIREMENTS = [
    (
        ROOT / "scripts" / "validate_all_until_lot21.py",
        '["python", "scripts/validate_v1_archive_frozen.py"]',
    ),
    (
        ROOT / "scripts" / "run_required_chain_until_lot21.sh",
        "python scripts/validate_v1_archive_frozen.py",
    ),
    (
        ROOT / "scripts" / "diagnose_exact_chain_until_lot21.py",
        "python scripts/validate_v1_archive_frozen.py &&",
    ),
]


def fail(message: str) -> int:
    print("V1 ARCHIVE FROZEN VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}{path.suffix}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def _run(command: list[str], timeout_seconds: int) -> int:
    result = subprocess.run(
        command,
        cwd=ROOT,
        timeout=timeout_seconds,
        check=False,
    )
    return int(result.returncode)


def main() -> int:
    archive_path = ROOT / ARCHIVE_RELATIVE_PATH
    archive_sha256_path = ROOT / ARCHIVE_SHA256_RELATIVE_PATH
    freeze_report_path = ROOT / FREEZE_REPORT_RELATIVE_PATH

    if not archive_path.exists():
        return fail(f"missing archive: {ARCHIVE_RELATIVE_PATH}")
    if not archive_sha256_path.exists():
        return fail(f"missing archive sha256 sidecar: {ARCHIVE_SHA256_RELATIVE_PATH}")

    observed_archive_sha256 = sha256_file(archive_path)
    observed_archive_size_bytes = archive_path.stat().st_size
    expected_sha_line = f"{observed_archive_sha256}  {archive_path.name}"
    observed_sha_line = archive_sha256_path.read_text(encoding="utf-8").strip()
    if observed_sha_line != expected_sha_line:
        return fail("archive sha256 sidecar mismatch")

    try:
        with tarfile.open(archive_path, "r:gz") as archive_handle:
            if not archive_handle.getnames():
                return fail("archive is empty after opening")
    except tarfile.TarError as exc:
        return fail(f"archive is not extractible: {exc}")

    rc = _run(["python", "scripts/validate_lot20.py"], 60)
    if rc != 0:
        return rc
    rc = _run(["python", "scripts/validate_lot20_archive_extracted.py"], 180)
    if rc != 0:
        return rc

    for path, required_step in CHAIN_REQUIREMENTS:
        text = path.read_text(encoding="utf-8")
        if LEGACY_CLOSURE_STEP in text:
            return fail(f"{path.name} still replays the Lot 20 closure script")
        if required_step not in text:
            return fail(f"{path.name} must validate the frozen archive before Lot 21")

    canonical_archive_matches_project_manager_proof = (
        observed_archive_sha256 == PROJECT_MANAGER_APPROVED_SHA256
        and observed_archive_size_bytes == PROJECT_MANAGER_APPROVED_SIZE_BYTES
    )
    incident_state = (
        "ORIGINAL_LOT20BIS_ARCHIVE_RETAINED"
        if canonical_archive_matches_project_manager_proof
        else "ORIGINAL_LOT20BIS_ARCHIVE_OVERWRITTEN_BEFORE_FREEZE"
    )
    report_body = (
        "# Lot 21-bis V1 Archive Freeze Report\n\n"
        "Status: PASS\n\n"
        f"why_lot21_bis_exists = The initial Lot 21 V2 chains were still replaying {LEGACY_CLOSURE_DISPLAY} and could overwrite the canonical V1 archive.\n\n"
        f"source_v1_archive_path = {ARCHIVE_RELATIVE_PATH}\n\n"
        "source_v1_archive_frozen = true\n\n"
        f"source_v1_archive_sha256 = {observed_archive_sha256}\n\n"
        f"source_v1_archive_size_bytes = {observed_archive_size_bytes}\n\n"
        f"project_manager_approved_lot20bis_sha256 = {PROJECT_MANAGER_APPROVED_SHA256}\n\n"
        f"project_manager_approved_lot20bis_size_bytes = {PROJECT_MANAGER_APPROVED_SIZE_BYTES}\n\n"
        f"canonical_archive_matches_project_manager_proof = {str(canonical_archive_matches_project_manager_proof).lower()}\n\n"
        f"incident_state = {incident_state}\n\n"
        "freeze_policy = V2_CHAINS_VALIDATE_ONLY_NO_ARCHIVE_REGENERATION\n\n"
        "validation_chain = validate_lot20.py -> validate_lot20_archive_extracted.py -> validate_v1_archive_frozen.py\n\n"
        "The canonical Lot 20 archive path is now treated as a frozen V1 proof for every V2 planning-only chain.\n\n"
        "If the project-manager-approved checksum is no longer present on this canonical path, the original Lot 20-bis proof was overwritten before the freeze guard existed.\n\n"
        "Lot 21-bis therefore freezes the currently extracted-and-validated archive and forbids any future overwrite from V2 chains.\n"
    )
    try:
        _atomic_write_text(freeze_report_path, report_body)
    except Exception as exc:
        return fail(f"unable to write archive freeze report: {exc}")

    print("V1 ARCHIVE FROZEN VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
