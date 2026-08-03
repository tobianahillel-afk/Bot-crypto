import json
from pathlib import Path

ALLOWED = {"unknown", "compressed", "normal", "expanding"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot5_range_outputs_exist_and_counts():
    range5 = read_jsonl(Path("data/gold/btc_eur_5m_range_state_lot5.jsonl"))
    range15 = read_jsonl(Path("data/gold/btc_eur_15m_range_state_lot5.jsonl"))
    assert len(range5) == 36
    assert len(range15) == 12
    assert all(row["used_for_decision"] is False for row in range5 + range15)


def test_lot5_range_first_values_insufficient_are_null():
    rows = read_jsonl(Path("data/gold/btc_eur_5m_range_state_lot5.jsonl"))
    for row in rows[:5]:
        assert row["rolling_range_6"] is None
        assert row["range_state"] == "unknown"
    assert rows[5]["rolling_range_6"] is not None


def test_lot5_range_scores_and_states_are_valid():
    rows = read_jsonl(Path("data/gold/btc_eur_5m_range_state_lot5.jsonl"))
    for row in rows:
        assert row["range_state"] in ALLOWED
        for key in ["compression_score", "expansion_score"]:
            value = row[key]
            assert value is None or 0 <= value <= 1


def test_lot5_range_has_no_forbidden_fields():
    text = Path("data/gold/btc_eur_5m_range_state_lot5.jsonl").read_text(encoding="utf-8")
    text += Path("data/gold/btc_eur_15m_range_state_lot5.jsonl").read_text(encoding="utf-8")
    assert "future_" not in text
    assert '"target"' not in text
    assert '"label"' not in text
