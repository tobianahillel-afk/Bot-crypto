import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot6_outputs_exist_and_have_expected_sizes():
    rows_5m = read_jsonl(ROOT / "data/gold/btc_eur_5m_regime_lot6.jsonl")
    rows_15m = read_jsonl(ROOT / "data/gold/btc_eur_15m_regime_lot6.jsonl")
    assert len(rows_5m) == 36
    assert len(rows_15m) == 12
    assert rows_5m[0]["regime_state"] == "unknown"
    assert rows_15m[0]["regime_state"] == "unknown"
    assert all(row["used_for_decision"] is False for row in rows_5m + rows_15m)
