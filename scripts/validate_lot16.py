#!/usr/bin/env python3
from __future__ import annotations

import string
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.lineage import (
    DEFAULT_LINEAGE_BLOCK_REASONS,
    compute_lot16_source_catalog_checksum,
    count_lot16_source_catalog_entries,
    LOT16_SOURCE_CATALOG_SCOPE,
    REPLAY_COMMAND,
    build_manifest_checksum,
)
from crypto_quant_bot.lineage.io import count_lines, load_json, load_jsonl, read_text_limited, write_validation_report

REQUIRED_FILES = [
    "src/crypto_quant_bot/lineage/__init__.py",
    "src/crypto_quant_bot/lineage/models.py",
    "src/crypto_quant_bot/lineage/manifest.py",
    "src/crypto_quant_bot/lineage/io.py",
    "scripts/run_lot16_reproducibility_manifest.py",
    "scripts/validate_lot16.py",
    "scripts/validate_all_until_lot16.py",
    "scripts/run_required_chain_until_lot16.sh",
    "scripts/diagnose_lot16_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot16.py",
    "data/audit/reproducibility_manifest_lot16.json",
    "data/audit/reproducibility_artifacts_lot16.jsonl",
    "reports/lot_16_reproducibility_report.md",
    "docs/LOT_16_REPRODUCIBILITY.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_16.md",
]
EXPECTED_CATALOG_IDS = {"reproducibility_manifest_lot16", "reproducibility_artifacts_lot16"}
EXPECTED_COUNTS = {
    "lot12": {"5m": 36, "15m": 12, "total": 48},
    "lot13": {"5m": 36, "15m": 12, "total": 48},
    "lot14": {"5m": 36, "15m": 12, "total": 48},
    "lot15": {"5m": 36, "15m": 12, "total": 48},
}
HEX_DIGITS = set(string.hexdigits)
ALLOWED_STRING_VALUES = {"NO_ORDER_ROUTER"}


def fail(message: str) -> int:
    print("LOT 16 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def validate_checksum(value: str) -> bool:
    return len(value) == 64 and all(char in HEX_DIGITS for char in value)


def has_forbidden_content(obj: Any, *, max_nodes: int = 80_000) -> bool:
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


def validate_artifact_row(row: dict[str, Any], index: int, jsonl_path: Path) -> str | None:
    required_fields = [
        "artifact_id",
        "lot",
        "artifact_type",
        "path",
        "checksum_sha256",
        "size_bytes",
        "line_count",
        "required",
        "produced_by",
        "consumes",
        "validation_command",
        "created_at",
    ]
    for field in required_fields:
        if field not in row:
            return f"{jsonl_path}:{index} missing field {field}"
    if row.get("required") is not True:
        return f"{jsonl_path}:{index} required must be true"
    path = ROOT / str(row.get("path", ""))
    if not path.exists():
        return f"{jsonl_path}:{index} missing artifact path {path}"
    if not validate_checksum(str(row.get("checksum_sha256", ""))):
        return f"{jsonl_path}:{index} invalid checksum_sha256"
    if str(row.get("checksum_sha256")) != sha256_file(path):
        return f"{jsonl_path}:{index} checksum mismatch"
    if int(row.get("size_bytes", -1)) != path.stat().st_size:
        return f"{jsonl_path}:{index} size mismatch"
    if int(row.get("line_count", -1)) != count_lines(path):
        return f"{jsonl_path}:{index} line_count mismatch"
    if has_forbidden_content(row):
        return f"{jsonl_path}:{index} contains forbidden trading content"
    return None


def validate_report_text(path: Path) -> str | None:
    text = read_text_limited(path)
    lowered = text.lower()
    forbidden_fragments = [
        "trade_allowed=true",
        "execution_allowed=true",
        "external_connectivity_allowed=true",
        "live_execution=enabled",
        "paper_trading",
    ]
    for fragment in forbidden_fragments:
        if fragment in lowered:
            return f"report contains forbidden fragment: {fragment}"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 16 artifact: {relative}")
    manifest_path = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"
    artifacts_path = ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl"
    report_path = ROOT / "reports" / "lot_16_reproducibility_report.md"
    validation_report_path = ROOT / "reports" / "lot_16_validation_report.md"
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        return fail("manifest must be a JSON object")
    artifacts_rows = load_jsonl(artifacts_path, max_lines=256)
    if manifest.get("manifest_version") in {None, ""}:
        return fail("manifest_version missing")
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "lineage_state": "RECORDED",
        "external_connectivity_allowed": False,
        "execution_allowed": False,
        "trade_allowed": False,
    }
    for key, value in expected_pairs.items():
        if manifest.get(key) != value:
            return fail(f"invalid {key}: {manifest.get(key)}")
    if not validate_checksum(str(manifest.get("source_catalog_checksum", ""))):
        return fail("source_catalog_checksum missing or invalid")
    if not validate_checksum(str(manifest.get("manifest_checksum", ""))):
        return fail("manifest_checksum missing or invalid")
    if build_manifest_checksum(manifest) != manifest.get("manifest_checksum"):
        return fail("manifest_checksum mismatch")
    source_catalog_path = ROOT / str(manifest.get("source_catalog_path", ""))
    if not source_catalog_path.exists():
        return fail("source_catalog_path missing on disk")
    source_catalog_payload = load_json(source_catalog_path)
    try:
        source_catalog_checksum = compute_lot16_source_catalog_checksum(source_catalog_payload)
        source_catalog_entry_count = count_lot16_source_catalog_entries(source_catalog_payload)
    except TypeError as exc:
        return fail(str(exc))
    if manifest.get("reproducibility_scope_lot16") != LOT16_SOURCE_CATALOG_SCOPE:
        return fail(f"unexpected reproducibility_scope_lot16: {manifest.get('reproducibility_scope_lot16')}")
    if manifest.get("source_catalog_scope") != LOT16_SOURCE_CATALOG_SCOPE:
        return fail(f"unexpected source_catalog_scope: {manifest.get('source_catalog_scope')}")
    if manifest.get("source_catalog_entry_count") != source_catalog_entry_count:
        return fail("source_catalog_entry_count mismatch")
    if str(manifest.get("source_catalog_checksum")) != source_catalog_checksum:
        return fail("source_catalog_checksum mismatch")
    if manifest.get("artifact_count") != len(artifacts_rows):
        return fail("artifact_count must match JSONL row count")
    manifest_artifacts = manifest.get("artifacts")
    if not isinstance(manifest_artifacts, list) or len(manifest_artifacts) != len(artifacts_rows):
        return fail("manifest artifacts length mismatch")
    for index, row in enumerate(artifacts_rows, start=1):
        message = validate_artifact_row(row, index, artifacts_path)
        if message:
            return fail(message)
    critical_counts = manifest.get("critical_counts")
    if not isinstance(critical_counts, dict):
        return fail("critical_counts missing")
    for key, expected in EXPECTED_COUNTS.items():
        if critical_counts.get(key) != expected:
            return fail(f"critical_counts mismatch for {key}: {critical_counts.get(key)}")
    replay_commands = manifest.get("replay_commands")
    if not isinstance(replay_commands, list) or REPLAY_COMMAND not in replay_commands:
        return fail("replay_commands must include exact chain until Lot 16")
    validation_commands = manifest.get("validation_commands")
    if not isinstance(validation_commands, list) or "python scripts/validate_lot16.py" not in validation_commands:
        return fail("validation_commands must include validate_lot16.py")
    block_reasons = manifest.get("lineage_block_reasons")
    if not isinstance(block_reasons, list) or set(DEFAULT_LINEAGE_BLOCK_REASONS) - set(block_reasons):
        return fail("missing required lineage_block_reasons")
    if has_forbidden_content(manifest):
        return fail("manifest contains forbidden trading content")
    report_message = validate_report_text(report_path)
    if report_message:
        return fail(report_message)
    catalog_records = DatasetCatalog(source_catalog_path).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 16 entries")
    write_validation_report(validation_report_path, artifact_count=len(artifacts_rows))
    print("LOT 16 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
