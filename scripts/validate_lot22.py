#!/usr/bin/env python3
from __future__ import annotations

import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis import (
    ALLOWED_CONTEXT_LABELS,
    ANALYSIS_INVARIANTS,
    ARCHIVE_OUTPUT_PATH,
    DATASET_CATALOG_PATH,
    DEFAULT_ANALYSIS_BLOCK_REASONS,
    LOT20_OUTPUT_PATH,
    LOT21_OUTPUT_PATH,
    LOT22_ACCEPTANCE_DOC_PATH,
    LOT22_OUTPUT_PATH,
    LOT22_OVERVIEW_DOC_PATH,
    LOT22_REPORT_OUTPUT_PATH,
    LOT22_TIMEFRAMES_OUTPUT_PATH,
    LOT22_VALIDATION_REPORT_PATH,
    MarketContextSnapshot,
    MarketTimeframeSummary,
    build_analysis_checksum,
    load_json,
    load_jsonl,
    read_text_limited,
    write_validation_report,
)

REQUIRED_FILES = [
    "src/crypto_quant_bot/market_analysis/__init__.py",
    "src/crypto_quant_bot/market_analysis/models.py",
    "src/crypto_quant_bot/market_analysis/foundation.py",
    "src/crypto_quant_bot/market_analysis/io.py",
    "scripts/run_lot22_market_analysis.py",
    "scripts/validate_lot22.py",
    "scripts/validate_all_until_lot22.py",
    "scripts/run_required_chain_until_lot22.sh",
    "scripts/diagnose_lot22_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot22.py",
    LOT22_OUTPUT_PATH,
    LOT22_TIMEFRAMES_OUTPUT_PATH,
    LOT22_REPORT_OUTPUT_PATH,
    LOT22_OVERVIEW_DOC_PATH,
    LOT22_ACCEPTANCE_DOC_PATH,
]
EXPECTED_CATALOG_IDS = {
    "market_analysis_lot22",
    "market_analysis_timeframes_lot22",
}
HEX_DIGITS = set(string.hexdigits)
WS_URL_TOKEN = "ws" + "://"
WSS_URL_TOKEN = "wss" + "://"
HTTP_URL_TOKEN = "http" + "://"
HTTPS_URL_TOKEN = "https" + "://"
FORBIDDEN_DIRECTIONAL_TOKENS = ["B" + "UY", "S" + "ELL", "L" + "ONG", "SH" + "ORT"]
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
    "position_size",
    "entry_price",
    "exit_price",
    "stop_loss",
    "take_profit",
    "paper_trading=true",
    "live_execution=enabled",
    "trade_allowed=true",
    "execution_allowed=true",
    "external_connectivity_allowed=true",
    "api_key_value",
    "secret_key_value",
    "websocket_url",
    WS_URL_TOKEN,
    WSS_URL_TOKEN,
    HTTP_URL_TOKEN,
    HTTPS_URL_TOKEN,
]


def fail(message: str) -> int:
    print("LOT 22 VALIDATION: FAIL", flush=True)
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
    raw_text = read_text_limited(path)
    for token in FORBIDDEN_DIRECTIONAL_TOKENS:
        if token in raw_text:
            return f"{path.name} contains forbidden directional token: {token}"
    text = _scrub_allowed_exceptions(raw_text)
    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        if fragment in text:
            return f"{path.name} contains forbidden fragment: {fragment}"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 22 artifact: {relative}")

    registry_path = ROOT / LOT22_OUTPUT_PATH
    timeframes_path = ROOT / LOT22_TIMEFRAMES_OUTPUT_PATH
    report_path = ROOT / LOT22_REPORT_OUTPUT_PATH
    validation_report_path = ROOT / LOT22_VALIDATION_REPORT_PATH
    archive_path = ROOT / ARCHIVE_OUTPUT_PATH

    snapshot = load_json(registry_path)
    if not isinstance(snapshot, dict):
        return fail("market analysis payload must be a JSON object")
    timeframe_rows = load_jsonl(timeframes_path, max_lines=32)

    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "analysis_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "execution_allowed": False,
        "trade_allowed": False,
        "external_connectivity_allowed": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "source_v1_archive_frozen": True,
        "v2_scope_state": "OPENED_AS_PLANNING_ONLY",
    }
    for key, value in expected_pairs.items():
        if snapshot.get(key) != value:
            return fail(f"invalid {key}: {snapshot.get(key)}")

    if snapshot.get("dataset_timeframes") != ["5m", "15m"]:
        return fail("dataset_timeframes must be ['5m', '15m']")
    if snapshot.get("analysis_timeframes") != ["5m", "15m"]:
        return fail("analysis_timeframes must be ['5m', '15m']")

    input_rows_by_timeframe = snapshot.get("input_rows_by_timeframe")
    if not isinstance(input_rows_by_timeframe, dict):
        return fail("input_rows_by_timeframe must be a mapping")
    for timeframe in ["5m", "15m"]:
        if int(input_rows_by_timeframe.get(timeframe, 0)) <= 0:
            return fail(f"input_rows_by_timeframe[{timeframe}] must be > 0")

    if not validate_checksum(str(snapshot.get("analysis_checksum", ""))):
        return fail("analysis_checksum missing or invalid")
    if build_analysis_checksum(snapshot) != snapshot.get("analysis_checksum"):
        return fail("analysis_checksum mismatch")

    if not isinstance(snapshot.get("timeframe_summaries"), list) or not snapshot.get("timeframe_summaries"):
        return fail("timeframe_summaries must be non-empty")
    if len(snapshot["timeframe_summaries"]) != len(timeframe_rows):
        return fail("timeframe_summaries length mismatch")

    for key, value in ANALYSIS_INVARIANTS.items():
        if key == "source_v1_archive_frozen":
            if snapshot.get("source_v1_archive_frozen") is not value:
                return fail("source_v1_archive_frozen invariant mismatch")
        elif key == "v2_scope_state":
            if snapshot.get("v2_scope_state") != value:
                return fail("v2_scope_state invariant mismatch")
        elif key == "project_mode":
            if snapshot.get("project_mode") != value:
                return fail("project_mode invariant mismatch")

    block_reasons = snapshot.get("analysis_block_reasons")
    if not isinstance(block_reasons, list):
        return fail("analysis_block_reasons must be a list")
    if set(DEFAULT_ANALYSIS_BLOCK_REASONS) - set(block_reasons):
        return fail("missing required analysis_block_reasons")

    allowed_labels = set(ALLOWED_CONTEXT_LABELS)
    for row in timeframe_rows:
        summary = MarketTimeframeSummary(**row)
        if not 0.0 <= summary.context_score <= 1.0:
            return fail(f"{summary.timeframe} context_score out of bounds")
        if summary.context_label not in allowed_labels:
            return fail(f"{summary.timeframe} context_label invalid: {summary.context_label}")
        if any(token == summary.context_label for token in FORBIDDEN_DIRECTIONAL_TOKENS):
            return fail(f"{summary.timeframe} context_label is forbidden")

    if not 0.0 <= float(snapshot.get("market_context_score", -1.0)) <= 1.0:
        return fail("market_context_score out of bounds")

    lot21_scope = load_json(ROOT / LOT21_OUTPUT_PATH)
    if not isinstance(lot21_scope, dict):
        return fail("Lot 21 product scope must remain a JSON object")
    lot20_closure = load_json(ROOT / LOT20_OUTPUT_PATH)
    if not isinstance(lot20_closure, dict):
        return fail("Lot 20 closure snapshot must remain a JSON object")
    observed_archive_checksum = sha256_file(archive_path)
    if lot21_scope.get("source_v1_archive_sha256") != observed_archive_checksum:
        return fail("Lot 22 modified the frozen archive checksum")
    if lot20_closure.get("archive_sha256") != observed_archive_checksum:
        return fail("Lot 22 modified the Lot 20 archive checksum")
    if lot21_scope.get("source_v1_archive_size_bytes") != archive_path.stat().st_size:
        return fail("Lot 22 modified the frozen archive size")

    for path in [
        registry_path,
        timeframes_path,
        report_path,
        ROOT / LOT22_OVERVIEW_DOC_PATH,
        ROOT / LOT22_ACCEPTANCE_DOC_PATH,
    ]:
        message = validate_output_text(path)
        if message:
            return fail(message)

    wrapper_text = read_text_limited(ROOT / "scripts/validate_all_until_lot22.py")
    chain_text = read_text_limited(ROOT / "scripts/run_required_chain_until_lot22.sh")
    exact_text = read_text_limited(ROOT / "scripts/diagnose_exact_chain_until_lot22.py")
    legacy_lot20_step = "run_lot20_" + "v1_closure.py"
    if legacy_lot20_step in wrapper_text or legacy_lot20_step in chain_text or legacy_lot20_step in exact_text:
        return fail(f"Lot 22 chains must not replay {legacy_lot20_step}")

    catalog_records = DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 22 entries")

    snapshot_object = MarketContextSnapshot(
        **{
            **snapshot,
            "timeframe_summaries": [MarketTimeframeSummary(**row) for row in timeframe_rows],
            "analysis_checks": snapshot.get("analysis_checks", []),
        }
    )
    write_validation_report(validation_report_path, snapshot=snapshot_object)
    validation_message = validate_output_text(validation_report_path)
    if validation_message:
        return fail(validation_message)

    print("LOT 22 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
