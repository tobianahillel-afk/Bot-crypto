from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "diagnose_pytest_after_chain.py"


def test_pytest_after_chain_diagnostic_script_exists_and_is_file_scoped():
    assert SCRIPT.exists()
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'glob("test_*.py")' in text
    assert "PER_FILE_TIMEOUT_SECONDS = 30" in text
    assert "subprocess.run" in text
    assert "pytest.main" not in text
    assert "DIAGNOSE PYTEST AFTER CHAIN: PASS" in text
    assert "validate_all_until_lot9.py" not in text
    assert "run_required_chain_until_lot9.sh" not in text
    assert "CQB_DISABLE" + "_PYTEST_FORCE_EXIT" not in text
