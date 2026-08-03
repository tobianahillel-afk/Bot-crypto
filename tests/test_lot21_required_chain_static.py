from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot21_required_chain_shell_is_simple_and_linear():
    text = (ROOT / "scripts" / "run_required_chain_until_lot21.sh").read_text(encoding="utf-8")
    assert "PIPE" not in text
    assert "DEVNULL" not in text
    assert "pytest" not in text
    assert "run_required_chain_until_lot19.sh" in text
    assert "run_lot20_v1_closure.py" not in text
    assert "python scripts/validate_lot20.py" in text
    assert "python scripts/validate_lot20_archive_extracted.py" in text
    assert "python scripts/validate_v1_archive_frozen.py" in text
    assert "python scripts/run_lot21_product_scope.py" in text
    assert "python scripts/validate_lot21.py" in text
    assert "LOT 21 REQUIRED CHAIN: PASS" in text


def test_lot21_orchestrated_validation_wraps_lot20_then_lot21():
    text = (ROOT / "scripts" / "validate_all_until_lot21.py").read_text(encoding="utf-8")
    assert '["python", "scripts/validate_all_until_lot19.py"]' in text
    assert '["python", "scripts/validate_lot20.py"]' in text
    assert '["python", "scripts/validate_lot20_archive_extracted.py"]' in text
    assert '["python", "scripts/validate_v1_archive_frozen.py"]' in text
    assert "run_lot20_v1_closure.py" not in text
    assert '["python", "scripts/run_lot21_product_scope.py"]' in text
    assert '["python", "scripts/validate_lot21.py"]' in text
    assert "LOT 21 ORCHESTRATED VALIDATION: PASS" in text
