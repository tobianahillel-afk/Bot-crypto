import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot4_outputs_exist_and_are_valid_without_rebuilding():
    paths = [
        Path("data/gold/btc_eur_5m_volume_profile_lot4.jsonl"),
        Path("data/gold/btc_eur_15m_volume_profile_lot4.jsonl"),
        Path("data/gold/btc_eur_5m_volume_profile_summary_lot4.jsonl"),
        Path("data/gold/btc_eur_15m_volume_profile_summary_lot4.jsonl"),
        Path("data/gold/btc_eur_5m_vwap_lot4.jsonl"),
        Path("data/gold/btc_eur_15m_vwap_lot4.jsonl"),
        Path("data/gold/btc_eur_5m_anchor_points_lot4.jsonl"),
        Path("data/gold/btc_eur_15m_anchor_points_lot4.jsonl"),
        Path("data/gold/btc_eur_5m_anchored_vwap_lot4.jsonl"),
        Path("data/gold/btc_eur_15m_anchored_vwap_lot4.jsonl"),
    ]
    for path in paths:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert '"LONG"' not in text
        assert '"SHORT"' not in text
        assert "future_" not in text
        assert '"target"' not in text
        assert '"label"' not in text
        assert all(row["used_for_decision"] is False for row in read_jsonl(path))

    assert len(read_jsonl(Path("data/gold/btc_eur_5m_vwap_lot4.jsonl"))) == 36
    assert len(read_jsonl(Path("data/gold/btc_eur_15m_vwap_lot4.jsonl"))) == 12
    assert Path("reports/lot_04_volume_profile_report.md").exists()
    assert Path("reports/lot_04_vwap_report.md").exists()
