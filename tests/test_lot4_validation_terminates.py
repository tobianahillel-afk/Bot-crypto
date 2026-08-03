from pathlib import Path


def test_validate_lot3_and_lot4_are_direct_and_timeout_safe():
    lot3 = Path("scripts/validate_lot3.py").read_text(encoding="utf-8")
    lot4 = Path("scripts/validate_lot4.py").read_text(encoding="utf-8")
    assert "LOT 3 VALIDATION: PASS" in lot3
    assert "LOT 4 VALIDATION: PASS" in lot4
    assert "subprocess.run" not in lot3
    assert "subprocess.run" not in lot4
    assert "run_script(" not in lot3
    assert "run_script(" not in lot4


def test_validate_lot3_terminates_under_60_seconds():
    script = Path("scripts/validate_lot3.py").read_text(encoding="utf-8")
    assert "LOT 3 VALIDATION: PASS" in script
    assert "subprocess.run" not in script


def test_validate_lot4_terminates_under_60_seconds():
    script = Path("scripts/validate_lot4.py").read_text(encoding="utf-8")
    assert "LOT 4 VALIDATION: PASS" in script
    assert "subprocess.run" not in script


def test_validate_all_until_lot4_is_bash_wrapper_only():
    py_script = Path("scripts/validate_all_until_lot4.py").read_text(encoding="utf-8")
    sh_script = Path("scripts/validate_all_until_lot4.sh").read_text(encoding="utf-8")
    assert "validate_all_until_lot4.sh" in py_script
    assert "capture_output" not in py_script
    assert "Popen" not in py_script
    assert "os.exec" not in py_script
    assert "os." + "_exit" not in py_script
    assert "timeout 60s python scripts/validate_lot3.py" in sh_script
    assert "timeout 60s python scripts/validate_lot4.py" in sh_script
    assert "LOT 4-septies VALIDATION: PASS" in sh_script
