import json
from math import isclose
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot5_volatility_outputs_exist_and_counts():
    vol5 = read_jsonl(Path("data/gold/btc_eur_5m_volatility_lot5.jsonl"))
    vol15 = read_jsonl(Path("data/gold/btc_eur_15m_volatility_lot5.jsonl"))
    assert len(vol5) == 36
    assert len(vol15) == 12
    assert all(row["used_for_decision"] is False for row in vol5 + vol15)


def test_lot5_realized_volatility_no_early_window():
    rows = read_jsonl(Path("data/gold/btc_eur_5m_volatility_lot5.jsonl"))
    assert rows[0]["realized_volatility_3"] is None
    assert rows[1]["realized_volatility_3"] is None
    assert rows[2]["realized_volatility_3"] is None
    assert rows[3]["realized_volatility_3"] is not None
    assert rows[0]["realized_volatility_6"] is None
    assert rows[5]["realized_volatility_6"] is None
    assert rows[6]["realized_volatility_6"] is not None


def test_lot5_true_range_first_row_is_high_low():
    rows = read_jsonl(Path("data/gold/btc_eur_5m_volatility_lot5.jsonl"))
    assert rows[0]["true_range"] == rows[0]["hl_range"]
    assert rows[0]["true_range"] is not None


def test_lot5_volatility_has_no_forbidden_fields():
    text = Path("data/gold/btc_eur_5m_volatility_lot5.jsonl").read_text(encoding="utf-8")
    text += Path("data/gold/btc_eur_15m_volatility_lot5.jsonl").read_text(encoding="utf-8")
    assert "future_" not in text
    assert '"target"' not in text
    assert '"label"' not in text
