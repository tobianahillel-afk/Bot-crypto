from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_lot7_market_state.py"
FORBIDDEN = [
    "subprocess.run",
    "subprocess." + "Popen",
    "capture_" + "output=True",
    "stdout=subprocess." + "PIPE",
    "stderr=subprocess." + "PIPE",
    "os." + "_exit",
    "os.exec",
    "signal." + "alarm",
    "while True",
    "os.walk",
    "rglob",
]


def test_lot7_build_has_no_non_terminating_patterns() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for marker in FORBIDDEN:
        assert marker not in text


def test_lot7_build_uses_normal_exit_pattern() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'print("LOT 7 MARKET STATE BUILD: PASS", flush=True)' in text
    assert "raise SystemExit(main())" in text
    forbidden_sequence = "sys.stdout.flush()" + "\n" + "    sys.stderr.flush()" + "\n" + "    raise SystemExit(main())"
    assert forbidden_sequence not in text
