from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_market_state_available_at_respects_components_and_usable_from():
    rows = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl")
    for row in rows:
        available_at = row["available_at"]
        assert all(value <= available_at for value in row["component_available_at"].values())
        assert all(pivot["usable_from"] <= available_at for pivot in row["nearest_pivots"] if pivot.get("usable_from"))
        assert all(zone["usable_from"] <= available_at for zone in row["nearest_zones"] if zone.get("usable_from"))
