from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "scripts" / "diagnose_lot8_no_lookahead_after_chain.py"
FORBIDDEN_TOKENS = [
    "capture_" + "output=True",
    "stdout=subprocess." + "PIPE",
    "stderr=subprocess." + "PIPE",
    "os." + "_exit",
    "signal." + "alarm",
]


def test_lot8_no_lookahead_after_chain_diagnostic_exists():
    assert DIAG.exists()


def test_lot8_no_lookahead_after_chain_diagnostic_has_no_pipe_capture_or_exit_hack():
    text = DIAG.read_text(encoding="utf-8")
    for token in FORBIDDEN_TOKENS:
        assert token not in text, f"diagnostic contains forbidden token: {token}"
    assert "DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS" in text
    assert "audit_lot8_no_lookahead.py" in text
