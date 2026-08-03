from tests.test_lot8_validate_all_terminates import run_lot8_smoke


def test_lot8_orchestrator_smoke_mode_is_lightweight():
    code, output = run_lot8_smoke()
    assert code == 0, output
    assert "LOT 8 ORCHESTRATOR SMOKE: PASS" in output
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
        "FEATURE REGISTRY AUDIT",
        "NO-LOOKAHEAD AUDIT",
        "pytest",
    ]
    for token in forbidden:
        assert token not in output
