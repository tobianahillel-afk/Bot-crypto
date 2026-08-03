from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot23_required_chain_shell_is_simple_and_linear():
    text = (ROOT / "scripts" / "run_required_chain_until_lot23.sh").read_text(encoding="utf-8")
    assert "PIPE" not in text
    assert "DEVNULL" not in text
    assert "pytest" not in text
    assert "run_required_chain_until_lot22.sh" in text
    assert "python scripts/validate_v1_archive_frozen.py" in text
    assert "python scripts/run_lot23_technical_indicators.py" in text
    assert "python scripts/validate_lot23.py" in text
    assert "run_lot20_" + "v1_closure.py" not in text
    assert "LOT 23 REQUIRED CHAIN: PASS" in text


def test_lot23_orchestrated_validation_wraps_lot22_then_lot23():
    text = (ROOT / "scripts" / "validate_all_until_lot23.py").read_text(encoding="utf-8")
    assert '["python", "scripts/validate_all_until_lot22.py"]' in text
    assert '["python", "scripts/validate_v1_archive_frozen.py"]' in text
    assert '["python", "scripts/run_lot23_technical_indicators.py"]' in text
    assert '["python", "scripts/validate_lot23.py"]' in text
    assert "run_lot20_" + "v1_closure.py" not in text
    assert "LOT 23 ORCHESTRATED VALIDATION: PASS" in text
