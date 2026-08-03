from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ingest_ohlcvt_fixture_script_exists():
    assert (ROOT / "scripts/ingest_ohlcvt_fixture.py").is_file()


def test_validate_lot1_covers_required_fixtures_and_is_direct():
    script = ROOT / "scripts/validate_lot1.py"
    text = script.read_text(encoding="utf-8")
    assert "btc_eur_ohlcvt_sample.csv" in text
    assert "btc_eur_ohlcvt_invalid.csv" in text
    assert "LOT 1 VALIDATION: PASS" in text
    assert "subprocess.run" not in text
    assert "ingest_ohlcvt_fixture.py" not in text
