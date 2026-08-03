from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAIN_SCRIPTS = [
    Path("scripts/validate_lot0.py"),
    Path("scripts/ingest_ohlcvt_fixture.py"),
    Path("scripts/validate_lot1.py"),
    Path("scripts/build_lot2_datasets.py"),
    Path("scripts/validate_lot2.py"),
    Path("scripts/build_lot3_pivots.py"),
    Path("scripts/validate_lot3.py"),
    Path("scripts/build_lot4_volume_vwap.py"),
    Path("scripts/validate_lot4.py"),
    Path("scripts/build_lot5_volatility.py"),
    Path("scripts/validate_lot5.py"),
    Path("scripts/build_lot6_regime.py"),
    Path("scripts/validate_lot6.py"),
    Path("scripts/build_lot7_market_state.py"),
    Path("scripts/validate_lot7.py"),
    Path("scripts/audit_lot8_feature_registry.py"),
    Path("scripts/audit_lot8_no_lookahead.py"),
    Path("scripts/validate_lot8.py"),
    Path("scripts/run_lot9_backtest_replay.py"),
    Path("scripts/validate_lot9.py"),
    Path("scripts/run_lot10_transaction_costs.py"),
    Path("scripts/validate_lot10.py"),
]
FORBIDDEN_TOKENS = [
    "capture_" + "output=True",
    "stdout=subprocess." + "PIPE",
    "stderr=subprocess." + "PIPE",
    "os." + "_exit",
    "os.exec",
    "signal." + "alarm",
]


def test_exact_chain_scripts_use_clean_exit_pattern():
    for relative_path in CHAIN_SCRIPTS:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "def main(" in text, f"{relative_path} has no main function"
        assert "raise SystemExit(main())" in text, f"{relative_path} does not exit through main()"


def test_exact_chain_scripts_do_not_use_non_terminating_patterns():
    for relative_path in CHAIN_SCRIPTS:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{relative_path} contains forbidden token: {token}"
