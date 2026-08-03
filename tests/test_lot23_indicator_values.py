import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_analysis import REQUIRED_INDICATOR_SET

TIMEFRAMES_PATH = ROOT / "data" / "audit" / "technical_indicators_timeframes_lot23.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot23_required_indicators_are_present_for_each_timeframe():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    for row in rows:
        indicator_values = row["indicator_values"]
        observed = [value["indicator_id"] for value in indicator_values]
        assert observed == REQUIRED_INDICATOR_SET


def test_lot23_indicator_values_are_materialized_and_row_counts_are_positive():
    rows = _load_jsonl(TIMEFRAMES_PATH)
    for row in rows:
        assert int(row["row_count"]) > 0
        for value in row["indicator_values"]:
            assert value["value"] is not None, value["indicator_id"]
