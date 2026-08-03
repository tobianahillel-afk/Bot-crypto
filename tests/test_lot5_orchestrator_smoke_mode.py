from tests.test_lot5_validate_all_terminates import run_lot5_smoke


def test_lot5_smoke_mode_does_not_run_heavy_validation_or_builds():
    code, output = run_lot5_smoke()
    assert code == 0, output
    assert "LOT 5-ter ORCHESTRATOR SMOKE: PASS" in output
    forbidden_output = [
        "LOT 0 VALIDATION",
        "LOT 1 VALIDATION",
        "LOT 2 VALIDATION",
        "LOT 3 VALIDATION",
        "LOT 4 VALIDATION",
        "LOT 5 VALIDATION",
        "pytest",
        "LOT 2 DATASET BUILD",
        "LOT 3 PIVOT BUILD",
        "LOT 4 VOLUME/VWAP BUILD",
        "LOT 5 VOLATILITY BUILD",
    ]
    for token in forbidden_output:
        assert token not in output
