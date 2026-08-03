from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot7_output_files_and_counts():
    rows_5m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl")
    rows_15m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl")
    assert len(rows_5m) == 36
    assert len(rows_15m) == 12
    assert (ROOT / "reports" / "lot_07_market_state_report.md").exists()
