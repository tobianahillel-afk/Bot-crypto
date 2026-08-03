import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot5_atr_windows_are_past_only():
    rows = read_jsonl(Path("data/gold/btc_eur_5m_volatility_lot5.jsonl"))
    assert rows[0]["atr_3"] is None
    assert rows[1]["atr_3"] is None
    expected = (rows[0]["true_range"] + rows[1]["true_range"] + rows[2]["true_range"]) / 3
    assert rows[2]["atr_3"] == expected
    assert rows[5]["atr_6"] is not None
    expected_6 = sum(row["true_range"] for row in rows[:6]) / 6
    assert rows[5]["atr_6"] == expected_6
