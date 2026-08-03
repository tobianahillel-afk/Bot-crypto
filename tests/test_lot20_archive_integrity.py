import hashlib
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
SHA256_PATH = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
RENAMED_TEST_PATH = "tests/test_pytest_suite_has_no_active_extended_subprocesses.py"
LEGACY_TEST_PATH = "tests/test_pytest_suite_has_no_active_" + "long" + "_subprocesses.py"


def require_lot20_archive() -> None:
    if not ARCHIVE_PATH.exists():
        pytest.skip("Lot 20 archive is generated after run_lot20_v1_closure.py")


def test_lot20_archive_sha256_matches_sidecar():
    require_lot20_archive()
    digest = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
    expected_line = f"{digest}  {ARCHIVE_PATH.name}"
    assert SHA256_PATH.read_text(encoding="utf-8").strip() == expected_line


def test_lot20_archive_is_non_empty_and_excludes_runtime_cache_paths():
    require_lot20_archive()
    assert ARCHIVE_PATH.stat().st_size > 0
    with tarfile.open(ARCHIVE_PATH, "r:gz") as handle:
        names = sorted(handle.getnames())
    assert names
    forbidden_markers = [
        ".git/",
        "__pycache__/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".venv/",
        "venv/",
        "dist/",
        "tmp/",
    ]
    for marker in forbidden_markers:
        assert all(marker not in name for name in names)
    assert RENAMED_TEST_PATH in names
    assert LEGACY_TEST_PATH not in names
