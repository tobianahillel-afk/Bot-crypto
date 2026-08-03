from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "diagnose_lot5_validate_after_chain.py"


def test_lot5_diagnostic_uses_run_timeout_and_system_exit() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "subprocess." + "run" in text
    assert "timeout=" in text
    assert "raise SystemExit(main())" in text


def test_lot5_diagnostic_has_no_manual_process_management() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "subprocess." + "Popen",
        "start_new" + "_session=True",
        "os." + "killpg",
        "signal." + "SIG" + "TERM",
        "signal." + "SIG" + "KILL",
        "process." + "wait(",
        "stdout=subprocess." + "PIPE",
        "stderr=subprocess." + "PIPE",
        "stdout=subprocess." + "DEV" + "NULL",
        "stderr=subprocess." + "DEV" + "NULL",
        "stdin=subprocess." + "DEV" + "NULL",
    ]
    offenders = [token for token in forbidden if token in text]
    assert offenders == []
