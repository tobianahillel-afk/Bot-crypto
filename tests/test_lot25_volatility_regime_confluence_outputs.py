import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_analysis import (
    ALLOWED_CONFLUENCE_STATES,
    ALLOWED_REGIME_STATES,
    ALLOWED_VOLATILITY_STATES,
    ALLOWED_VRC_COMBINED_STATES,
)

SNAPSHOT_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_lot25.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_timeframes_lot25.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_25_volatility_regime_confluence_report.md"
VALIDATION_REPORT_PATH = ROOT / "reports" / "lot_25_validation_report.md"
DOC_PATHS = [
    ROOT / "docs" / "LOT_25_VOLATILITY_REGIME_CONFLUENCE.md",
    ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_25.md",
]


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot25_artifacts_are_present():
    for path in [SNAPSHOT_PATH, TIMEFRAMES_PATH, REPORT_PATH, VALIDATION_REPORT_PATH, *DOC_PATHS]:
        assert path.exists(), f"missing Lot 25 artifact: {path}"


def test_lot25_snapshot_core_fields_are_locked():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["project_name"] == "Crypto Quant Bot V3.1-Ops"
    assert snapshot["project_mode"] == "EDUCATIONAL_AUDIT_ONLY"
    assert snapshot["vrc_engine_mode"] == "LOCAL_OFFLINE_VOLATILITY_REGIME_CONFLUENCE_ONLY"
    assert snapshot["analysis_mode"] == "LOCAL_OFFLINE_ANALYSIS_ONLY"
    assert snapshot["indicator_mode"] == "LOCAL_OFFLINE_INDICATORS_ONLY"
    assert snapshot["trend_engine_mode"] == "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
    assert snapshot["execution_allowed"] is False
    assert snapshot["trade_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["live_execution"] == "DISABLED"
    assert snapshot["leverage"] == "FORBIDDEN"
    assert snapshot["source_v1_archive_frozen"] is True
    assert snapshot["v2_scope_state"] == "OPENED_AS_PLANNING_ONLY"
    assert snapshot["dataset_timeframes"] == ["5m", "15m"]
    assert snapshot["vrc_timeframes"] == ["5m", "15m"]
    assert snapshot["volatility_state"] in ALLOWED_VOLATILITY_STATES
    assert snapshot["regime_state"] in ALLOWED_REGIME_STATES
    assert snapshot["confluence_state"] in ALLOWED_CONFLUENCE_STATES
    assert snapshot["combined_context_state"] in ALLOWED_VRC_COMBINED_STATES
    assert isinstance(snapshot["vrc_checksum"], str)
    assert len(snapshot["vrc_checksum"]) == 64


def test_lot25_timeframes_file_contains_5m_and_15m():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    observed = [row["timeframe"] for row in rows]
    assert observed == ["5m", "15m"]
