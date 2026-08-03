from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validate_all_until_lot4_executes_without_nested_pytest():
    py_script = Path("scripts/validate_all_until_lot4.py").read_text(encoding="utf-8")
    sh_script = Path("scripts/validate_all_until_lot4.sh").read_text(encoding="utf-8")
    assert "validate_all_until_lot4.sh" in py_script
    assert "capture_output" not in py_script
    assert "Popen" not in py_script
    assert "CQB_SKIP_NESTED_PYTEST" in sh_script
    assert "LOT 4-septies VALIDATION: PASS" in sh_script

def test_validate_all_orchestrator_is_fast_by_default_and_wrapper_is_minimal():
    py_script = Path("scripts/validate_all_until_lot4.py").read_text(encoding="utf-8")
    sh_script = Path("scripts/validate_all_until_lot4.sh").read_text(encoding="utf-8")
    assert "validate_all_until_lot4.sh" in py_script
    assert "capture_output" not in py_script
    assert "os.exec" not in py_script
    assert "os." + "_exit" not in py_script
    assert "Popen" not in py_script
    assert "for " not in py_script
    assert "MODE=\"${CQB_ORCHESTRATOR_MODE:-fast}\"" in sh_script
    assert "FAST mode: skip rebuild steps" in sh_script
    assert "FULL rebuild mode" in sh_script
    assert "timeout 60s python scripts/validate_lot3.py" in sh_script
    assert "timeout 60s python scripts/validate_lot4.py" in sh_script
    assert "SKIP pytest in fast/nested mode" in sh_script
    assert "timeout 180s python -m pytest -q" in sh_script
    assert "LOT 4-septies VALIDATION: PASS" in sh_script
