from pathlib import Path

VALIDATE_SCRIPTS = [
    Path("scripts/validate_lot1.py"),
    Path("scripts/validate_lot2.py"),
    Path("scripts/validate_lot3.py"),
    Path("scripts/validate_lot4.py"),
    Path("scripts/validate_lot5.py"),
    Path("scripts/validate_lot6.py"),
    Path("scripts/validate_lot7.py"),
    Path("scripts/validate_lot8.py"),
    Path("scripts/validate_lot9.py"),
    Path("scripts/validate_lot10.py"),
]

FORBIDDEN_TOKENS = [
    "subprocess.run",
    "subprocess.call",
    "Popen",
    "capture_" + "output=True",
    "validate_lot0.py",
    "validate_lot1.py",
    "validate_lot2.py",
    "validate_lot3.py",
    "validate_lot4.py",
    "validate_lot5.py",
    "build_lot2_datasets.py",
    "build_lot3_pivots.py",
    "build_lot4_volume_vwap.py",
    "build_lot5_volatility.py",
    "build_lot6_regime.py",
    "build_lot7_market_state.py",
    "validate_lot6.py",
    "validate_lot7.py",
    "ingest_ohlcvt_fixture.py",
]


def test_validate_scripts_have_no_nested_subprocess_or_build_calls():
    for path in VALIDATE_SCRIPTS:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            if token == path.name:
                continue
            assert token not in text, f"{path} contains forbidden token: {token}"
