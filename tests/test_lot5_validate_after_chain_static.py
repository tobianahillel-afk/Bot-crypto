from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_lot5.py"
SUB = "subprocess"


def _forbidden_tokens() -> list[str]:
    return [
        SUB + ".run",
        SUB + ".Popen",
        "capture_" + "output=True",
        "stdout=" + SUB + ".PIPE",
        "stderr=" + SUB + ".PIPE",
        "os." + "_exit",
        "os.exec",
        "signal." + "alarm",
        "close_standard" + "_streams",
        "os." + "dup2",
        SUB + ".DEVNULL",
        "while " + "True",
        "os.walk",
        "rglob",
    ]


def test_validate_lot5_has_no_non_terminating_patterns():
    text = SCRIPT.read_text(encoding="utf-8")
    for token in _forbidden_tokens():
        assert token not in text, f"validate_lot5.py contains forbidden token: {token}"


def test_validate_lot5_uses_clean_pass_and_exit_pattern():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'print("LOT 5 VALIDATION: PASS", flush=True)' in text
    assert "raise SystemExit(main())" in text
