import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "market_analysis_lot22.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "market_analysis_timeframes_lot22.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_22_market_analysis_report.md"
VALIDATION_REPORT_PATH = ROOT / "reports" / "lot_22_validation_report.md"
DOC_PATHS = [
    ROOT / "docs" / "LOT_22_MARKET_ANALYSIS.md",
    ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_22.md",
]


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot22_artifacts_are_present():
    for path in [SNAPSHOT_PATH, TIMEFRAMES_PATH, REPORT_PATH, VALIDATION_REPORT_PATH, *DOC_PATHS]:
        assert path.exists(), f"missing Lot 22 artifact: {path}"


def test_lot22_snapshot_core_fields_are_locked():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["project_name"] == "Crypto Quant Bot V3.1-Ops"
    assert snapshot["project_mode"] == "EDUCATIONAL_AUDIT_ONLY"
    assert snapshot["analysis_mode"] == "LOCAL_OFFLINE_ANALYSIS_ONLY"
    assert snapshot["execution_allowed"] is False
    assert snapshot["trade_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["live_execution"] == "DISABLED"
    assert snapshot["leverage"] == "FORBIDDEN"
    assert snapshot["source_v1_archive_frozen"] is True
    assert snapshot["v2_scope_state"] == "OPENED_AS_PLANNING_ONLY"
    assert snapshot["dataset_timeframes"] == ["5m", "15m"]
    assert snapshot["analysis_timeframes"] == ["5m", "15m"]
    assert isinstance(snapshot["analysis_checksum"], str)
    assert len(snapshot["analysis_checksum"]) == 64


def test_lot22_timeframes_file_contains_5m_and_15m():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    observed = [row["timeframe"] for row in rows]
    assert observed == ["5m", "15m"]
