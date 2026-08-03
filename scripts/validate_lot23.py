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
    ALLOWED_INDICATOR_STATES,
    ARCHIVE_OUTPUT_PATH,
    DATASET_CATALOG_PATH,
    DEFAULT_INDICATOR_BLOCK_REASONS,
    INDICATOR_INVARIANTS,
    LOT20_OUTPUT_PATH,
    LOT21_OUTPUT_PATH,
    LOT23_ACCEPTANCE_DOC_PATH,
    LOT23_OUTPUT_PATH,
    LOT23_OVERVIEW_DOC_PATH,
    LOT23_REPORT_OUTPUT_PATH,
    LOT23_TIMEFRAMES_OUTPUT_PATH,
    LOT23_VALIDATION_REPORT_PATH,
    REQUIRED_INDICATOR_SET,
    IndicatorValue,
    TechnicalIndicatorResult,
    TechnicalIndicatorTimeframeSummary,
    build_indicator_checksum,
    load_json,
    load_jsonl,
    read_text_limited,
    write_indicator_validation_report,
)

REQUIRED_FILES = [
    "src/crypto_quant_bot/market_analysis/technical_indicators.py",
    "src/crypto_quant_bot/market_analysis/indicator_models.py",
    "scripts/run_lot23_technical_indicators.py",
    "scripts/validate_lot23.py",
    "scripts/validate_all_until_lot23.py",
    "scripts/run_required_chain_until_lot23.sh",
    "scripts/diagnose_lot23_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot23.py",
    LOT23_OUTPUT_PATH,
    LOT23_TIMEFRAMES_OUTPUT_PATH,
    LOT23_REPORT_OUTPUT_PATH,
    LOT23_OVERVIEW_DOC_PATH,
    LOT23_ACCEPTANCE_DOC_PATH,
]
EXPECTED_CATALOG_IDS = {
    "technical_indicators_lot23",
    "technical_indicators_timeframes_lot23",
}
HEX_DIGITS = set(string.hexdigits)
WS_URL_TOKEN = "ws" + "://"
WSS_URL_TOKEN = "wss" + "://"
HTTP_URL_TOKEN = "http" + "://"
HTTPS_URL_TOKEN = "https" + "://"
FORBIDDEN_DIRECTIONAL_TOKENS = ["B" + "UY", "S" + "ELL", "L" + "ONG", "SH" + "ORT"]
FORBIDDEN_FIELD_FRAGMENTS = ["SIG" + "NAL", "TAR" + "GET", "LA" + "BEL"]
ALLOWED_OUTPUT_EXCEPTIONS = {
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "macd_signal_3",
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
    print("LOT 23 VALIDATION: FAIL", flush=True)
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
    for fragment in FORBIDDEN_FIELD_FRAGMENTS:
        if fragment.lower() in text:
            return f"{path.name} contains forbidden field fragment: {fragment}"
    return None


def _indicator_map(summary: TechnicalIndicatorTimeframeSummary) -> dict[str, IndicatorValue]:
    return {indicator.indicator_id: indicator for indicator in summary.indicator_values}


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 23 artifact: {relative}")

    registry_path = ROOT / LOT23_OUTPUT_PATH
    timeframes_path = ROOT / LOT23_TIMEFRAMES_OUTPUT_PATH
    report_path = ROOT / LOT23_REPORT_OUTPUT_PATH
    validation_report_path = ROOT / LOT23_VALIDATION_REPORT_PATH
    archive_path = ROOT / ARCHIVE_OUTPUT_PATH

    snapshot = load_json(registry_path)
    if not isinstance(snapshot, dict):
        return fail("technical indicators payload must be a JSON object")
    timeframe_rows = load_jsonl(timeframes_path, max_lines=32)

    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "indicator_mode": "LOCAL_OFFLINE_INDICATORS_ONLY",
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
    if snapshot.get("indicator_timeframes") != ["5m", "15m"]:
        return fail("indicator_timeframes must be ['5m', '15m']")
    if snapshot.get("indicator_set") != REQUIRED_INDICATOR_SET:
        return fail("indicator_set mismatch")

    input_rows_by_timeframe = snapshot.get("input_rows_by_timeframe")
    if not isinstance(input_rows_by_timeframe, dict):
        return fail("input_rows_by_timeframe must be a mapping")
    for timeframe in ["5m", "15m"]:
        if int(input_rows_by_timeframe.get(timeframe, 0)) <= 0:
            return fail(f"input_rows_by_timeframe[{timeframe}] must be > 0")

    if not validate_checksum(str(snapshot.get("indicator_checksum", ""))):
        return fail("indicator_checksum missing or invalid")
    if build_indicator_checksum(snapshot) != snapshot.get("indicator_checksum"):
        return fail("indicator_checksum mismatch")

    if not isinstance(snapshot.get("timeframe_summaries"), list) or not snapshot.get("timeframe_summaries"):
        return fail("timeframe_summaries must be non-empty")
    if len(snapshot["timeframe_summaries"]) != len(timeframe_rows):
        return fail("timeframe_summaries length mismatch")

    for key, value in INDICATOR_INVARIANTS.items():
        if key not in snapshot:
            continue
        if snapshot.get(key) != value:
            return fail(f"invariant mismatch for {key}: {snapshot.get(key)}")

    block_reasons = snapshot.get("indicator_block_reasons")
    if not isinstance(block_reasons, list):
        return fail("indicator_block_reasons must be a list")
    if set(DEFAULT_INDICATOR_BLOCK_REASONS) - set(block_reasons):
        return fail("missing required indicator_block_reasons")

    allowed_states = set(ALLOWED_INDICATOR_STATES)
    for row in timeframe_rows:
        summary = TechnicalIndicatorTimeframeSummary(
            **{
                **row,
                "indicator_values": [IndicatorValue(**value) for value in row.get("indicator_values", [])],
            }
        )
        if summary.indicator_state not in allowed_states:
            return fail(f"{summary.timeframe} indicator_state invalid: {summary.indicator_state}")
        if any(token == summary.indicator_state for token in FORBIDDEN_DIRECTIONAL_TOKENS):
            return fail(f"{summary.timeframe} indicator_state is forbidden")
        if not 0.0 <= float(summary.indicator_context_score) <= 1.0:
            return fail(f"{summary.timeframe} indicator_context_score out of bounds")
        indicator_map = _indicator_map(summary)
        if set(REQUIRED_INDICATOR_SET) - set(indicator_map):
            return fail(f"{summary.timeframe} missing required indicators")
        for indicator_id in REQUIRED_INDICATOR_SET:
            if indicator_map[indicator_id].value is None:
                return fail(f"{summary.timeframe} missing value for {indicator_id}")

    if not 0.0 <= float(snapshot.get("indicator_context_score", -1.0)) <= 1.0:
        return fail("indicator_context_score out of bounds")
    if snapshot.get("indicator_state") not in allowed_states:
        return fail("indicator_state invalid")

    lot21_scope = load_json(ROOT / LOT21_OUTPUT_PATH)
    if not isinstance(lot21_scope, dict):
        return fail("Lot 21 product scope must remain a JSON object")
    lot20_closure = load_json(ROOT / LOT20_OUTPUT_PATH)
    if not isinstance(lot20_closure, dict):
        return fail("Lot 20 closure snapshot must remain a JSON object")
    observed_archive_checksum = sha256_file(archive_path)
    if lot21_scope.get("source_v1_archive_sha256") != observed_archive_checksum:
        return fail("Lot 23 modified the frozen archive checksum")
    if lot20_closure.get("archive_sha256") != observed_archive_checksum:
        return fail("Lot 23 modified the Lot 20 archive checksum")
    if lot21_scope.get("source_v1_archive_size_bytes") != archive_path.stat().st_size:
        return fail("Lot 23 modified the frozen archive size")

    for path in [
        registry_path,
        timeframes_path,
        report_path,
        ROOT / LOT23_OVERVIEW_DOC_PATH,
        ROOT / LOT23_ACCEPTANCE_DOC_PATH,
    ]:
        message = validate_output_text(path)
        if message:
            return fail(message)

    wrapper_text = read_text_limited(ROOT / "scripts/validate_all_until_lot23.py")
    chain_text = read_text_limited(ROOT / "scripts/run_required_chain_until_lot23.sh")
    exact_text = read_text_limited(ROOT / "scripts/diagnose_exact_chain_until_lot23.py")
    legacy_lot20_step = "run_lot20_" + "v1_closure.py"
    if legacy_lot20_step in wrapper_text or legacy_lot20_step in chain_text or legacy_lot20_step in exact_text:
        return fail(f"Lot 23 chains must not replay {legacy_lot20_step}")

    catalog_records = DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 23 entries")

    snapshot_object = TechnicalIndicatorResult(
        **{
            **snapshot,
            "timeframe_summaries": [
                TechnicalIndicatorTimeframeSummary(
                    **{
                        **row,
                        "indicator_values": [IndicatorValue(**value) for value in row.get("indicator_values", [])],
                    }
                )
                for row in timeframe_rows
            ],
            "indicator_checks": snapshot.get("indicator_checks", []),
        }
    )
    write_indicator_validation_report(validation_report_path, snapshot=snapshot_object)
    validation_message = validate_output_text(validation_report_path)
    if validation_message:
        return fail(validation_message)

    print("LOT 23 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
