import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_lot25.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_timeframes_lot25.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot25_scores_are_bounded_and_rows_are_positive():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    rows = _load_jsonl(TIMEFRAMES_PATH)
    assert snapshot["input_rows_by_timeframe"]["5m"] > 0
    assert snapshot["input_rows_by_timeframe"]["15m"] > 0
    for key in [
        "volatility_context_score",
        "regime_context_score",
        "confluence_context_score",
        "combined_context_score",
    ]:
        assert 0.0 <= float(snapshot[key]) <= 1.0
    for row in rows:
        assert int(row["row_count"]) > 0
        assert 0.0 <= float(row["volatility_context_score"]) <= 1.0
        assert 0.0 <= float(row["regime_context_score"]) <= 1.0
        assert 0.0 <= float(row["confluence_context_score"]) <= 1.0
        assert 0.0 <= float(row["combined_context_score"]) <= 1.0
        assert 0.0 <= float(row["confluence_agreement_score"]) <= 1.0
        assert 0.0 <= float(row["confluence_divergence_score"]) <= 1.0
        assert isinstance(row["confluence_components"], dict)


def test_lot25_summary_contains_required_descriptive_fields():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    required = {
        "timeframe",
        "row_count",
        "first_timestamp",
        "last_timestamp",
        "atr_5",
        "true_range_latest",
        "bollinger_width_5",
        "rolling_range_5",
        "range_width_percent",
        "volatility_expansion_score",
        "volatility_compression_score",
        "volatility_state",
        "volatility_context_score",
        "market_regime_source_state",
        "trend_state",
        "range_state",
        "momentum_state",
        "technical_indicator_state",
        "regime_state",
        "regime_context_score",
        "confluence_components",
        "confluence_agreement_score",
        "confluence_divergence_score",
        "confluence_state",
        "confluence_context_score",
        "combined_context_score",
        "combined_context_state",
        "non_executable_summary",
    }
    for row in rows:
        assert required.issubset(row.keys())
