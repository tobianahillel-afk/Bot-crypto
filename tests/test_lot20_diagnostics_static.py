from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = "subprocess"
LOT20_PYTHON_SCRIPTS = [
    ROOT / "scripts" / "run_lot20_v1_closure.py",
    ROOT / "scripts" / "validate_lot20.py",
    ROOT / "scripts" / "validate_lot20_archive_extracted.py",
    ROOT / "scripts" / "validate_all_until_lot20.py",
    ROOT / "scripts" / "diagnose_lot20_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot20.py",
]
DIAGNOSTICS = [
    ROOT / "scripts" / "diagnose_lot20_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot20.py",
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


def test_lot20_python_scripts_avoid_forbidden_process_hacks():
    for path in LOT20_PYTHON_SCRIPTS:
        text = path.read_text(encoding="utf-8")
        for token in _forbidden_tokens():
            assert token not in text, f"{path.name} contains forbidden token: {token}"


def test_lot20_diagnostics_use_subprocess_run_only():
    for path in DIAGNOSTICS:
        text = path.read_text(encoding="utf-8")
        for token in _forbidden_tokens():
            assert token not in text, f"{path.name} contains forbidden token: {token}"
        assert SUB + "." + "run" in text
        assert "timeout=" in text
        assert "raise SystemExit(main())" in text


def test_lot20_exact_chain_covers_lot19_lot20_and_pytest():
    text = (ROOT / "scripts" / "diagnose_exact_chain_until_lot20.py").read_text(encoding="utf-8")
    required_steps = [
        "python scripts/run_lot19_release_candidate.py &&",
        "python scripts/validate_lot19.py &&",
        "python scripts/run_lot20_v1_closure.py &&",
        "python scripts/validate_lot20.py &&",
        "python scripts/validate_lot20_archive_extracted.py &&",
        "python -m pytest -q &&",
        "echo EXACT_CHAIN_LOT20_DONE",
    ]
    for step in required_steps:
        assert step in text
