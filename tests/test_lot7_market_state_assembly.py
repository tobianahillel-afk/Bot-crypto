from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_market_state_rows_have_required_components():
    rows = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl")
    assert rows
    row = rows[0]
    assert row["candle"]
    assert row["volatility_state"]
    assert row["range_state"]
    assert row["regime_state"]
    assert isinstance(row["nearest_pivots"], list)
    assert isinstance(row["nearest_zones"], list)
    assert row["used_for_decision"] is False
