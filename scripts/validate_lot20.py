#!/usr/bin/env python3
from __future__ import annotations

import string
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.closure import (
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
    CLOSURE_INVARIANTS,
    DATASET_CATALOG_PATH,
    DEFAULT_CLOSURE_BLOCK_REASONS,
    LEGACY_ACTIVE_TEST_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    LOT20_VALIDATION_REPORT_PATH,
    RENAMED_ACTIVE_TEST_PATH,
    ArchiveManifest,
    ClosureCheck,
    build_closure_checksum,
    load_json,
    load_jsonl,
    read_text_limited,
    write_validation_report,
)
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file

REQUIRED_FILES = [
    "src/crypto_quant_bot/closure/__init__.py",
    "src/crypto_quant_bot/closure/models.py",
    "src/crypto_quant_bot/closure/archive.py",
    "src/crypto_quant_bot/closure/io.py",
    "scripts/run_lot20_v1_closure.py",
    "scripts/validate_lot20.py",
    "scripts/validate_lot20_archive_extracted.py",
    "scripts/validate_all_until_lot20.py",
    "scripts/run_required_chain_until_lot20.sh",
    "scripts/diagnose_lot20_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot20.py",
    LOT20_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
    "docs/LOT_20_V1_CLOSURE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_20.md",
    RENAMED_ACTIVE_TEST_PATH,
]
EXPECTED_CATALOG_IDS = {"v1_closure_lot20", "v1_closure_checks_lot20"}
HEX_DIGITS = set(string.hexdigits)
ALLOWED_OUTPUT_EXCEPTIONS = {
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
}
FORBIDDEN_TEXT_FRAGMENTS = [
    "order_id",
    "fill",
    "pnl",
    "profit",
    "loss",
    "position",
    "target",
    "label",
    "future",
    "long",
    "short",
    "buy",
    "sell",
    "entry_price",
    "exit_price",
    "stop_loss",
    "take_profit",
    "paper_trading=true",
    "live_execution=enabled",
    "trade_allowed=true",
    "execution_allowed=true",
    "external_connectivity_allowed=true",
    "api_key",
    "websocket",
    "ws://",
    "wss://",
    "http://",
    "https://",
]


def fail(message: str) -> int:
    print("LOT 20 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def validate_checksum(value: str) -> bool:
    return len(value) == 64 and all(char in HEX_DIGITS for char in value)


def _scrub_allowed_exceptions(text: str) -> str:
    scrubbed = text.lower()
    for token in ALLOWED_OUTPUT_EXCEPTIONS:
        scrubbed = scrubbed.replace(token.lower(), "")
    return scrubbed


def validate_output_text(path: Path) -> str | None:
    text = _scrub_allowed_exceptions(read_text_limited(path))
    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        if fragment in text:
            return f"{path.name} contains forbidden fragment: {fragment}"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 20 artifact: {relative}")

    snapshot_path = ROOT / LOT20_OUTPUT_PATH
    checks_path = ROOT / LOT20_CHECKS_OUTPUT_PATH
    report_path = ROOT / LOT20_REPORT_OUTPUT_PATH
    archive_manifest_path = ROOT / LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH
    archive_path = ROOT / ARCHIVE_OUTPUT_PATH
    archive_sha256_path = ROOT / ARCHIVE_SHA256_OUTPUT_PATH
    validation_report_path = ROOT / LOT20_VALIDATION_REPORT_PATH

    snapshot = load_json(snapshot_path)
    if not isinstance(snapshot, dict):
        return fail("closure payload must be a JSON object")
    checks_rows = load_jsonl(checks_path, max_lines=128)

    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "closure_state": "V1_DEFENSIVE_AUDIT_CLOSED",
        "archive_state": "ARCHIVE_CREATED",
        "archive_created": True,
        "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
        "acceptance_state": "ACCEPTANCE_BUNDLE_GENERATED",
        "compliance_state": "COMPLIANT",
        "no_trading_state": "ENFORCED",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "pytest_state": "GREEN",
        "exact_chain_state": "GREEN",
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "trade_allowed": False,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "exchange_connector_present": False,
        "order_router_present": False,
        "api_key_present": False,
        "websocket_present": False,
        "paper_trading_present": False,
        "strategy_present": False,
        "forbidden_semantics_present": False,
        "critical_counts_valid": True,
    }
    for key, value in expected_pairs.items():
        if snapshot.get(key) != value:
            return fail(f"invalid {key}: {snapshot.get(key)}")

    observed_archive_checksum = sha256_file(archive_path)
    sha_line = read_text_limited(archive_sha256_path).strip()
    expected_sha_line = f"{observed_archive_checksum}  {archive_path.name}"
    if sha_line != expected_sha_line:
        return fail("archive sha256 file content mismatch")
    if observed_archive_checksum != snapshot.get("archive_sha256"):
        return fail("archive checksum mismatch")
    if archive_path.stat().st_size <= 0:
        return fail("archive is empty")
    if archive_path.stat().st_size != snapshot.get("archive_size_bytes"):
        return fail("archive_size_bytes mismatch")
    if snapshot.get("archive_path") != ARCHIVE_OUTPUT_PATH:
        return fail("archive_path mismatch")
    if snapshot.get("archive_sha256_path") != ARCHIVE_SHA256_OUTPUT_PATH:
        return fail("archive_sha256_path mismatch")

    if not validate_checksum(str(snapshot.get("closure_checksum", ""))):
        return fail("closure_checksum missing or invalid")
    if build_closure_checksum(snapshot) != snapshot.get("closure_checksum"):
        return fail("closure_checksum mismatch")

    snapshot_checks = snapshot.get("closure_checks")
    if not isinstance(snapshot_checks, list) or not snapshot_checks:
        return fail("closure_checks must be a non-empty list")
    if len(snapshot_checks) != len(checks_rows):
        return fail("closure_checks length mismatch")
    if any(row.get("status") != "PASS" for row in checks_rows):
        return fail("closure_checks contain a blocking status")

    block_reasons = snapshot.get("closure_block_reasons")
    if not isinstance(block_reasons, list) or set(DEFAULT_CLOSURE_BLOCK_REASONS) - set(block_reasons):
        return fail("missing required closure_block_reasons")

    invariants = snapshot.get("invariants")
    if not isinstance(invariants, dict):
        return fail("invariants missing")
    for key, value in CLOSURE_INVARIANTS.items():
        if invariants.get(key) != value:
            return fail(f"invariant mismatch for {key}: {invariants.get(key)}")

    included_paths = snapshot.get("included_paths")
    excluded_paths = snapshot.get("excluded_paths")
    if not isinstance(included_paths, list) or not included_paths:
        return fail("included_paths must be non-empty")
    if not isinstance(excluded_paths, list) or not excluded_paths:
        return fail("excluded_paths must be non-empty")
    if RENAMED_ACTIVE_TEST_PATH not in included_paths:
        return fail("renamed active test is missing from included_paths")
    if LEGACY_ACTIVE_TEST_PATH in included_paths:
        return fail("legacy long-named test must not appear in included_paths")

    with tarfile.open(archive_path, "r:gz") as archive_handle:
        member_names = archive_handle.getnames()
    if RENAMED_ACTIVE_TEST_PATH not in member_names:
        return fail("renamed active test is missing from archive")
    if LEGACY_ACTIVE_TEST_PATH in member_names:
        return fail("legacy long-named test is still present in archive")

    for path in [snapshot_path, checks_path, report_path, archive_manifest_path]:
        message = validate_output_text(path)
        if message:
            return fail(message)

    catalog_records = DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 20 entries")

    manifest = ArchiveManifest(
        **{
            **snapshot,
            "closure_checks": [ClosureCheck(**row) for row in checks_rows],
        }
    )
    write_validation_report(
        validation_report_path,
        manifest=manifest,
        closure_check_count=len(checks_rows),
    )
    validation_message = validate_output_text(validation_report_path)
    if validation_message:
        return fail(validation_message)

    print("LOT 20 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
