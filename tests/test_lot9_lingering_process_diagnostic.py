from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "diagnose_lingering_processes.py"
SUB = "subprocess"


def test_lingering_process_diagnostic_is_natural_and_run_based():
    assert SCRIPT.exists()
    text = SCRIPT.read_text(encoding="utf-8")
    assert "DIAGNOSE LINGERING PROCESSES: PASS" in text
    assert SUB + "." + "run" in text
    assert "timeout=" in text
    assert SUB + "." + "Popen" not in text
    assert "signal." + "SIG" + "TERM" not in text
    assert "signal." + "SIG" + "KILL" not in text
    assert "raise SystemExit(main(sys.argv[1:]))" in text
