#!/usr/bin/env python3
from __future__ import annotations

import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.release import (
    ARCHIVE_CANDIDATE_PATHS,
    DEFAULT_RELEASE_BLOCK_REASONS,
    DATASET_CATALOG_PATH,
    LOT19_ACCEPTANCE_OUTPUT_PATH,
    LOT19_CHECKS_OUTPUT_PATH,
    LOT19_OUTPUT_PATH,
    LOT19_REPORT_OUTPUT_PATH,
    LOT19_VALIDATION_REPORT_PATH,
    RELEASE_INVARIANTS,
    ReleaseCandidateCheck,
    ReleaseCandidateSnapshot,
    build_release_checksum,
    load_json,
    load_jsonl,
    read_text_limited,
    write_validation_report,
)

REQUIRED_FILES = [
    "src/crypto_quant_bot/release/__init__.py",
    "src/crypto_quant_bot/release/models.py",
    "src/crypto_quant_bot/release/candidate.py",
    "src/crypto_quant_bot/release/io.py",
    "scripts/run_lot19_release_candidate.py",
    "scripts/validate_lot19.py",
    "scripts/validate_all_until_lot19.py",
    "scripts/run_required_chain_until_lot19.sh",
    "scripts/diagnose_lot19_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot19.py",
    LOT19_OUTPUT_PATH,
    LOT19_CHECKS_OUTPUT_PATH,
    LOT19_REPORT_OUTPUT_PATH,
    LOT19_ACCEPTANCE_OUTPUT_PATH,
    "docs/LOT_19_RELEASE_CANDIDATE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_19.md",
]
EXPECTED_CATALOG_IDS = {"release_candidate_lot19", "release_candidate_checks_lot19"}
HEX_DIGITS = set(string.hexdigits)
ALLOWED_OUTPUT_EXCEPTIONS = {
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "NO_ARCHIVE_CREATED",
    "archive_created=false",
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
    ".tar.gz",
    ".zip",
    ".whl",
    ".exe",
]


def fail(message: str) -> int:
    print("LOT 19 VALIDATION: FAIL", flush=True)
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
            return fail(f"missing Lot 19 artifact: {relative}")
    snapshot_path = ROOT / LOT19_OUTPUT_PATH
    checks_path = ROOT / LOT19_CHECKS_OUTPUT_PATH
    report_path = ROOT / LOT19_REPORT_OUTPUT_PATH
    acceptance_path = ROOT / LOT19_ACCEPTANCE_OUTPUT_PATH
    validation_report_path = ROOT / LOT19_VALIDATION_REPORT_PATH
    snapshot = load_json(snapshot_path)
    if not isinstance(snapshot, dict):
        return fail("release candidate payload must be a JSON object")
    checks_rows = load_jsonl(checks_path, max_lines=128)
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
        "acceptance_state": "ACCEPTANCE_BUNDLE_GENERATED",
        "packaging_state": "NO_ARCHIVE_CREATED",
        "archive_created": False,
        "compliance_state": "COMPLIANT",
        "no_trading_state": "ENFORCED",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "integrity_state": "VERIFIED",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "pytest_state": "EXPECTED_GREEN",
        "exact_chain_state": "EXPECTED_GREEN",
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "trading_decision": "WAIT",
        "system_decision": "BLOCK_TRADING",
        "final_decision": "WAIT",
        "final_system_decision": "BLOCK_TRADING",
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
        "health_monitor_valid": True,
        "no_trading_compliance_valid": True,
        "reproducibility_manifest_valid": True,
        "dataset_catalog_valid": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
    }
    for key, value in expected_pairs.items():
        if snapshot.get(key) != value:
            return fail(f"invalid {key}: {snapshot.get(key)}")
    if not validate_checksum(str(snapshot.get("release_checksum", ""))):
        return fail("release_checksum missing or invalid")
    if build_release_checksum(snapshot) != snapshot.get("release_checksum"):
        return fail("release_checksum mismatch")
    snapshot_checks = snapshot.get("release_checks")
    if not isinstance(snapshot_checks, list) or not snapshot_checks:
        return fail("release_checks must be a non-empty list")
    if len(snapshot_checks) != len(checks_rows):
        return fail("release_checks length mismatch")
    block_reasons = snapshot.get("release_block_reasons")
    if not isinstance(block_reasons, list) or set(DEFAULT_RELEASE_BLOCK_REASONS) - set(block_reasons):
        return fail("missing required release_block_reasons")
    criteria = snapshot.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria:
        return fail("acceptance_criteria must be a non-empty list")
    invariants = snapshot.get("invariants")
    if not isinstance(invariants, dict):
        return fail("invariants missing")
    for key, value in RELEASE_INVARIANTS.items():
        if invariants.get(key) != value:
            return fail(f"invariant mismatch for {key}: {invariants.get(key)}")
    for path in [snapshot_path, checks_path, report_path, acceptance_path]:
        message = validate_output_text(path)
        if message:
            return fail(message)
    archive_hits = [relative_path for relative_path in ARCHIVE_CANDIDATE_PATHS if (ROOT / relative_path).exists()]
    if archive_hits:
        return fail(f"Lot 19 archive outputs detected: {archive_hits}")
    catalog_records = DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 19 entries")
    snapshot_object = ReleaseCandidateSnapshot(
        **{
            **snapshot,
            "release_checks": [ReleaseCandidateCheck(**row) for row in checks_rows],
        }
    )
    write_validation_report(
        validation_report_path,
        snapshot=snapshot_object,
        release_check_count=len(checks_rows),
    )
    validation_message = validate_output_text(validation_report_path)
    if validation_message:
        return fail(validation_message)
    print("LOT 19 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
