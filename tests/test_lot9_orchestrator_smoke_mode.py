from tests.test_lot9_validate_all_terminates import run_lot9_smoke


def test_lot9_orchestrator_smoke_mode_is_lightweight():
    code, output = run_lot9_smoke()
    assert code == 0, output
    assert "LOT 9 ORCHESTRATOR SMOKE: PASS" in output
    forbidden = [
        "LOT 0 VALIDATION",
        "LOT 1 VALIDATION",
        "LOT 2 VALIDATION",
        "LOT 3 VALIDATION",
        "LOT 4 VALIDATION",
        "LOT 5 VALIDATION",
        "LOT 6 VALIDATION",
        "LOT 7 VALIDATION",
        "LOT 8 VALIDATION",
        "LOT 9 VALIDATION",
        "BACKTEST REPLAY",
        "pytest",
    ]
    for token in forbidden:
        assert token not in output


def test_validate_lot9_contains_no_nested_validation_or_process_execution():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts" / "validate_lot9.py").read_text(encoding="utf-8")
    forbidden = [
        "subprocess.run",
        "Popen",
        "validate_lot0.py",
        "validate_lot1.py",
        "validate_lot2.py",
        "validate_lot3.py",
        "validate_lot4.py",
        "validate_lot5.py",
        "validate_lot6.py",
        "validate_lot7.py",
        "validate_lot8.py",
    ]
    for token in forbidden:
        assert token not in text
