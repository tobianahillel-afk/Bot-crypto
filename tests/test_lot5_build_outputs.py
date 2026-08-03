from pathlib import Path


def test_lot5_required_outputs_exist():
    for path in [
        Path("data/gold/btc_eur_5m_volatility_lot5.jsonl"),
        Path("data/gold/btc_eur_15m_volatility_lot5.jsonl"),
        Path("data/gold/btc_eur_5m_range_state_lot5.jsonl"),
        Path("data/gold/btc_eur_15m_range_state_lot5.jsonl"),
        Path("reports/lot_05_volatility_report.md"),
        Path("reports/lot_05_range_state_report.md"),
        Path("scripts/build_lot5_volatility.py"),
        Path("scripts/validate_lot5.py"),
    ]:
        assert path.exists(), path


def test_lot5_catalog_contains_outputs():
    text = Path("data/audit/dataset_catalog.json").read_text(encoding="utf-8")
    for dataset_id in [
        "btc_eur_5m_volatility_lot5",
        "btc_eur_15m_volatility_lot5",
        "btc_eur_5m_range_state_lot5",
        "btc_eur_15m_range_state_lot5",
    ]:
        assert dataset_id in text
