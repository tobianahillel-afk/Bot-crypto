from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = "subprocess"
DIAGNOSTICS = [
    ROOT / "scripts" / "diagnose_lot17_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot17.py",
]


def _forbidden_tokens() -> list[str]:
    return [
        SUB + "." + "Popen",
        "capture_output" + "=True",
        "stdout=" + SUB + "." + "PIPE",
        "stderr=" + SUB + "." + "PIPE",
        "stdout=" + SUB + "." + "DEV" + "NULL",
        "stderr=" + SUB + "." + "DEV" + "NULL",
        "stdin=" + SUB + "." + "DEV" + "NULL",
        "os." + "_exit",
        "signal." + "alarm",
        "os." + "killpg",
        "start_new" + "_session=True",
        "signal." + "SIG" + "TERM",
        "signal." + "SIG" + "KILL",
    ]


def test_lot17_diagnostics_use_subprocess_run_only():
    for path in DIAGNOSTICS:
        text = path.read_text(encoding="utf-8")
        for token in _forbidden_tokens():
            assert token not in text, f"{path.name} contains forbidden token: {token}"
        assert SUB + "." + "run" in text
        assert "timeout=" in text
        assert "raise SystemExit(main())" in text


def test_lot17_exact_chain_covers_lot16_lot17_and_pytest():
    text = (ROOT / "scripts" / "diagnose_exact_chain_until_lot17.py").read_text(encoding="utf-8")
    required_steps = [
        "python scripts/run_lot16_reproducibility_manifest.py &&",
        "python scripts/validate_lot16.py &&",
        "python scripts/run_lot17_health_monitor.py &&",
        "python scripts/validate_lot17.py &&",
        "python -m pytest -q &&",
        "echo EXACT_CHAIN_LOT17_DONE",
    ]
    for step in required_steps:
        assert step in text
