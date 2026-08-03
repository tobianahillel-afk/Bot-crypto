from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot20_required_chain_shell_is_simple_and_linear():
    text = (ROOT / "scripts" / "run_required_chain_until_lot20.sh").read_text(encoding="utf-8")
    assert "PIPE" not in text
    assert "DEVNULL" not in text
    assert "pytest" not in text
    assert "run_required_chain_until_lot19.sh" in text
    assert "python scripts/run_lot20_v1_closure.py" in text
    assert "python scripts/validate_lot20.py" in text
    assert "python scripts/validate_lot20_archive_extracted.py" in text
    assert "LOT 20 REQUIRED CHAIN: PASS" in text


def test_lot20_orchestrated_validation_wraps_lot19_then_lot20():
    text = (ROOT / "scripts" / "validate_all_until_lot20.py").read_text(encoding="utf-8")
    assert '["python", "scripts/validate_all_until_lot19.py"]' in text
    assert '["python", "scripts/run_lot20_v1_closure.py"]' in text
    assert '["python", "scripts/validate_lot20.py"]' in text
    assert '["python", "scripts/validate_lot20_archive_extracted.py"]' in text
    assert "LOT 20 ORCHESTRATED VALIDATION: PASS" in text
