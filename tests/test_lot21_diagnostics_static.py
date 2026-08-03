from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = "subprocess"
LOT21_PYTHON_SCRIPTS = [
    ROOT / "scripts" / "validate_v1_archive_frozen.py",
    ROOT / "scripts" / "run_lot21_product_scope.py",
    ROOT / "scripts" / "validate_lot21.py",
    ROOT / "scripts" / "validate_all_until_lot21.py",
    ROOT / "scripts" / "diagnose_lot21_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot21.py",
]
DIAGNOSTICS = [
    ROOT / "scripts" / "diagnose_lot21_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot21.py",
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


def test_lot21_python_scripts_avoid_forbidden_process_hacks():
    for path in LOT21_PYTHON_SCRIPTS:
        text = path.read_text(encoding="utf-8")
        for token in _forbidden_tokens():
            assert token not in text, f"{path.name} contains forbidden token: {token}"


def test_lot21_diagnostics_use_subprocess_run_only():
    for path in DIAGNOSTICS:
        text = path.read_text(encoding="utf-8")
        for token in _forbidden_tokens():
            assert token not in text, f"{path.name} contains forbidden token: {token}"
        assert SUB + "." + "run" in text
        assert "timeout=" in text
        assert "raise SystemExit(main())" in text


def test_lot21_exact_chain_covers_lot20_lot21_and_pytest():
    text = (ROOT / "scripts" / "diagnose_exact_chain_until_lot21.py").read_text(encoding="utf-8")
    required_steps = [
        "python scripts/validate_lot20.py &&",
        "python scripts/validate_lot20_archive_extracted.py &&",
        "python scripts/validate_v1_archive_frozen.py &&",
        "python scripts/run_lot21_product_scope.py &&",
        "python scripts/validate_lot21.py &&",
        "python -m pytest -q &&",
        "echo EXACT_CHAIN_LOT21_DONE",
    ]
    for step in required_steps:
        assert step in text
    assert "run_lot20_v1_closure.py" not in text
