from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "diagnose_lot4_fd_lingering_owner.py"
SUB = "subprocess"


def test_lot4_fd_lingering_owner_uses_run_timeout_and_system_exit() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert SUB + ".run" in text
    assert "timeout=" in text
    assert "raise SystemExit(main())" in text


def test_lot4_fd_lingering_owner_has_no_capture_or_fd_hacks() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "capture_output" + "=True",
        "stdout=" + SUB + "." + "PIPE",
        "stderr=" + SUB + "." + "PIPE",
        "stdout=" + SUB + "." + "DEV" + "NULL",
        "stderr=" + SUB + "." + "DEV" + "NULL",
        "stdin=" + SUB + "." + "DEV" + "NULL",
        "os." + "_exit",
        "signal." + "alarm",
        "close_standard" + "_streams",
        "os." + "dup2",
    ]
    offenders = [token for token in forbidden if token in text]
    assert offenders == []
