from tests.test_lot6_validate_all_terminates import run_lot6_smoke


def test_lot6_smoke_mode_does_not_run_heavy_validation_or_builds():
    code, output = run_lot6_smoke()
    assert code == 0, output
    assert "LOT 6 ORCHESTRATOR SMOKE: PASS" in output
    forbidden = [
        "LOT 0 VALIDATION",
        "LOT 1 VALIDATION",
        "LOT 2 VALIDATION",
        "LOT 3 VALIDATION",
        "LOT 4 VALIDATION",
        "LOT 5 VALIDATION",
        "LOT 6 VALIDATION",
        "LOT 2 DATASET BUILD",
        "LOT 3 PIVOT BUILD",
        "LOT 4 VOLUME/VWAP BUILD",
        "LOT 5 VOLATILITY BUILD",
        "LOT 6 REGIME BUILD",
        "pytest",
    ]
    for token in forbidden:
        assert token not in output
