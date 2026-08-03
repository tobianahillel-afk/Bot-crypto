#!/usr/bin/env python3
from __future__ import annotations

import json
import string
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.health import (
    DEFAULT_HEALTH_BLOCK_REASONS,
    HealthCheck,
    HealthSnapshot,
    build_dataset_catalog_checksum,
    build_health_checksum,
    load_json,
    load_jsonl,
    read_text_limited,
    write_validation_report,
)
from crypto_quant_bot.health.monitor import (
    DATASET_CATALOG_PATH,
    HEALTH_CHECKS_OUTPUT_PATH,
    HEALTH_INVARIANTS,
    HEALTH_MONITOR_OUTPUT_PATH,
    HEALTH_REPORT_OUTPUT_PATH,
    HEALTH_VALIDATION_REPORT_PATH,
)

REQUIRED_FILES = [
    "src/crypto_quant_bot/health/__init__.py",
    "src/crypto_quant_bot/health/models.py",
    "src/crypto_quant_bot/health/monitor.py",
    "src/crypto_quant_bot/health/io.py",
    "scripts/run_lot17_health_monitor.py",
    "scripts/validate_lot17.py",
    "scripts/validate_all_until_lot17.py",
    "scripts/run_required_chain_until_lot17.sh",
    "scripts/diagnose_lot17_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot17.py",
    HEALTH_MONITOR_OUTPUT_PATH,
    HEALTH_CHECKS_OUTPUT_PATH,
    HEALTH_REPORT_OUTPUT_PATH,
    "docs/LOT_17_HEALTH_MONITOR.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_17.md",
]
EXPECTED_CATALOG_IDS = {"health_monitor_lot17", "health_checks_lot17"}
HEX_DIGITS = set(string.hexdigits)
ALLOWED_STRING_VALUES = {"NO_ORDER_ROUTER"}


def fail(message: str) -> int:
    print("LOT 17 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def validate_checksum(value: str) -> bool:
    return len(value) == 64 and all(char in HEX_DIGITS for char in value)


def has_forbidden_content(obj: Any, *, max_nodes: int = 100_000) -> bool:
    forbidden_key_parts = (
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
        "paper_trading",
    )
    forbidden_values = {"LONG", "SHORT", "BUY", "SELL"}
    stack = [obj]
    seen = 0
    while stack:
        seen += 1
        if seen > max_nodes:
            return True
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                lowered = str(key).lower()
                if any(part in lowered for part in forbidden_key_parts):
                    return True
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if current in ALLOWED_STRING_VALUES:
                continue
            lowered = current.lower()
            if any(part in lowered for part in forbidden_key_parts):
                return True
            if current.upper() in forbidden_values:
                return True
    return False


def validate_report_text(path: Path) -> str | None:
    text = read_text_limited(path).lower()
    forbidden_fragments = [
        "trade_allowed=true",
        "execution_allowed=true",
        "external_connectivity_allowed=true",
        "live_execution=enabled",
        "paper_trading",
    ]
    for fragment in forbidden_fragments:
        if fragment in text:
            return f"report contains forbidden fragment: {fragment}"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 17 artifact: {relative}")
    snapshot_path = ROOT / HEALTH_MONITOR_OUTPUT_PATH
    checks_path = ROOT / HEALTH_CHECKS_OUTPUT_PATH
    report_path = ROOT / HEALTH_REPORT_OUTPUT_PATH
    validation_report_path = ROOT / HEALTH_VALIDATION_REPORT_PATH
    snapshot = load_json(snapshot_path)
    if not isinstance(snapshot, dict):
        return fail("health monitor payload must be a JSON object")
    checks_rows = load_jsonl(checks_path, max_lines=64)
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "integrity_state": "VERIFIED",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "monitoring_mode": "LOCAL_STATIC_ONLY",
        "external_connectivity_allowed": False,
        "execution_allowed": False,
        "trade_allowed": False,
        "dataset_catalog_readable": True,
        "lot16_manifest_readable": True,
        "lot16_artifacts_readable": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
        "required_diagnostics_present": True,
        "critical_counts_valid": True,
        "checksum_references_valid": True,
    }
    for key, value in expected_pairs.items():
        if snapshot.get(key) != value:
            return fail(f"invalid {key}: {snapshot.get(key)}")
    if not validate_checksum(str(snapshot.get("health_checksum", ""))):
        return fail("health_checksum missing or invalid")
    if build_health_checksum(snapshot) != snapshot.get("health_checksum"):
        return fail("health_checksum mismatch")
    if int(snapshot.get("artifact_count", 0)) <= 0:
        return fail("artifact_count must be positive")
    snapshot_checks = snapshot.get("health_checks")
    if not isinstance(snapshot_checks, list) or not snapshot_checks:
        return fail("health_checks must be a non-empty list")
    if len(snapshot_checks) != len(checks_rows):
        return fail("health_checks length mismatch")
    block_reasons = snapshot.get("health_block_reasons")
    if not isinstance(block_reasons, list) or set(DEFAULT_HEALTH_BLOCK_REASONS) - set(block_reasons):
        return fail("missing required health_block_reasons")
    invariants = snapshot.get("invariants")
    if not isinstance(invariants, dict):
        return fail("invariants missing")
    for key, value in HEALTH_INVARIANTS.items():
        if invariants.get(key) != value:
            return fail(f"invariant mismatch for {key}: {invariants.get(key)}")
    if has_forbidden_content(snapshot):
        return fail("health snapshot contains forbidden trading content")
    if any(has_forbidden_content(row) for row in checks_rows):
        return fail("health checks contain forbidden trading content")
    report_message = validate_report_text(report_path)
    if report_message:
        return fail(report_message)
    catalog_records = DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 17 entries")
    if build_dataset_catalog_checksum(catalog_records) != snapshot.get("dataset_catalog_checksum"):
        return fail("dataset_catalog_checksum mismatch")
    snapshot_object = HealthSnapshot(
        **{
            **snapshot,
            "health_checks": [HealthCheck(**row) for row in checks_rows],
        }
    )
    write_validation_report(
        validation_report_path,
        snapshot=snapshot_object,
        health_check_count=len(checks_rows),
    )
    print("LOT 17 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
