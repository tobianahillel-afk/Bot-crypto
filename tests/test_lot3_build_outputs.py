import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot3_outputs_exist_and_are_valid_without_rebuilding():
    silver_5m = Path("data/silver/btc_eur_5m_ohlcvt_lot3.jsonl")
    silver_15m = Path("data/silver/btc_eur_15m_ohlcvt_lot3.jsonl")
    pivots_5m = Path("data/gold/btc_eur_5m_pivots_lot3.jsonl")
    pivots_15m = Path("data/gold/btc_eur_15m_pivots_lot3.jsonl")
    zones_5m = Path("data/gold/btc_eur_5m_price_zones_lot3.jsonl")
    zones_15m = Path("data/gold/btc_eur_15m_price_zones_lot3.jsonl")
    for path in [silver_5m, silver_15m, pivots_5m, pivots_15m, zones_5m, zones_15m]:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert '"LONG"' not in text
        assert '"SHORT"' not in text

    assert len(read_jsonl(silver_5m)) == 36
    assert len(read_jsonl(silver_15m)) == 12
    pivots = read_jsonl(pivots_5m) + read_jsonl(pivots_15m)
    zones = read_jsonl(zones_5m) + read_jsonl(zones_15m)
    assert pivots
    assert zones
    assert all(row["used_for_decision"] is False for row in pivots)
    assert all(row["used_for_decision"] is False for row in zones)
    assert Path("reports/lot_03_pivot_report.md").exists()
    assert Path("reports/lot_03_zone_report.md").exists()
