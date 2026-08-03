import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot2_silver_and_gold_outputs_exist_without_rebuilding():
    silver_5m = Path("data/silver/btc_eur_5m_ohlcvt_lot2.jsonl")
    silver_15m = Path("data/silver/btc_eur_15m_ohlcvt_lot2.jsonl")
    gold_5m = Path("data/gold/btc_eur_5m_features_lot2.jsonl")
    gold_15m = Path("data/gold/btc_eur_15m_features_lot2.jsonl")
    for path in [silver_5m, silver_15m, gold_5m, gold_15m]:
        assert path.exists()
    assert len(read_jsonl(silver_5m)) == 12
    assert len(read_jsonl(silver_15m)) == 4
    assert len(read_jsonl(gold_5m)) == 12
    assert len(read_jsonl(gold_15m)) == 4
