import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_analysis import (
    ALLOWED_COMBINED_CONTEXT_STATES,
    ALLOWED_MOMENTUM_STATES,
    ALLOWED_RANGE_STATES,
    ALLOWED_TREND_STATES,
)

SNAPSHOT_PATH = ROOT / "data" / "audit" / "trend_range_momentum_lot24.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "trend_range_momentum_timeframes_lot24.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_24_trend_range_momentum_report.md"
VALIDATION_REPORT_PATH = ROOT / "reports" / "lot_24_validation_report.md"
DOC_PATHS = [
    ROOT / "docs" / "LOT_24_TREND_RANGE_MOMENTUM.md",
    ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_24.md",
]


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot24_artifacts_are_present():
    for path in [SNAPSHOT_PATH, TIMEFRAMES_PATH, REPORT_PATH, VALIDATION_REPORT_PATH, *DOC_PATHS]:
        assert path.exists(), f"missing Lot 24 artifact: {path}"


def test_lot24_snapshot_core_fields_are_locked():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["project_name"] == "Crypto Quant Bot V3.1-Ops"
    assert snapshot["project_mode"] == "EDUCATIONAL_AUDIT_ONLY"
    assert snapshot["trend_engine_mode"] == "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
    assert snapshot["analysis_mode"] == "LOCAL_OFFLINE_ANALYSIS_ONLY"
    assert snapshot["indicator_mode"] == "LOCAL_OFFLINE_INDICATORS_ONLY"
    assert snapshot["execution_allowed"] is False
    assert snapshot["trade_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["live_execution"] == "DISABLED"
    assert snapshot["leverage"] == "FORBIDDEN"
    assert snapshot["source_v1_archive_frozen"] is True
    assert snapshot["v2_scope_state"] == "OPENED_AS_PLANNING_ONLY"
    assert snapshot["dataset_timeframes"] == ["5m", "15m"]
    assert snapshot["trend_timeframes"] == ["5m", "15m"]
    assert snapshot["trend_state"] in ALLOWED_TREND_STATES
    assert snapshot["range_state"] in ALLOWED_RANGE_STATES
    assert snapshot["momentum_state"] in ALLOWED_MOMENTUM_STATES
    assert snapshot["combined_context_state"] in ALLOWED_COMBINED_CONTEXT_STATES
    assert isinstance(snapshot["trend_checksum"], str)
    assert len(snapshot["trend_checksum"]) == 64


def test_lot24_timeframes_file_contains_5m_and_15m():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    observed = [row["timeframe"] for row in rows]
    assert observed == ["5m", "15m"]
