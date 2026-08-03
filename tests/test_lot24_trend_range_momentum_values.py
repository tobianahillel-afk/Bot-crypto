import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "trend_range_momentum_timeframes_lot24.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot24_row_counts_and_required_numeric_fields_are_materialized():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    for row in rows:
        assert int(row["row_count"]) > 0
        for key in [
            "close_first",
            "close_last",
            "close_change_percent",
            "trend_slope_5",
            "range_high_5",
            "range_low_5",
            "range_width_5",
            "range_width_percent",
            "range_position_percent",
            "momentum_3",
            "rate_of_change_3",
            "rsi_5",
            "macd_histogram",
            "bollinger_width_5",
            "atr_5",
        ]:
            assert isinstance(row[key], (int, float)), key


def test_lot24_scores_are_bounded_between_zero_and_one():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    for row in rows:
        for key in [
            "trend_context_score",
            "range_context_score",
            "momentum_context_score",
            "combined_context_score",
        ]:
            assert 0.0 <= float(row[key]) <= 1.0, key
