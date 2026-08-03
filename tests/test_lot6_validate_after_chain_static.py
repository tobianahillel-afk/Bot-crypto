from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "scripts" / "diagnose_lot6_validate_after_chain.py",
    ROOT / "scripts" / "build_lot6_regime.py",
    ROOT / "scripts" / "validate_lot6.py",
]
SUB = "subprocess"
OS_NAME = "os"
SIGNAL_NAME = "signal"


def _forbidden_tokens() -> list[str]:
    return [
        "capture_" + "output=True",
        "stdout=" + SUB + "." + "PIPE",
        "stderr=" + SUB + "." + "PIPE",
        "stdout=" + SUB + "." + "DEVNULL",
        "stderr=" + SUB + "." + "DEVNULL",
        "stdin=" + SUB + "." + "DEVNULL",
        OS_NAME + "." + "_exit",
        SIGNAL_NAME + "." + "alarm",
        "close_standard" + "_streams",
        OS_NAME + "." + "dup2",
        "multi" + "processing",
        "threading." + "Thread",
        "daemon=" + "False",
        "atexit." + "register",
        SUB + "." + "Popen",
        OS_NAME + "." + "fork",
        "p" + "ty",
        "asyncio." + "create_task",
        OS_NAME + "." + "system",
        OS_NAME + "." + "spawn",
        OS_NAME + "." + "posix_spawn",
        "while " + "True",
        OS_NAME + "." + "walk",
        "r" + "glob",
    ]


def test_lot6_scripts_have_no_forbidden_termination_tokens():
    for script in SCRIPTS:
        text = script.read_text(encoding="utf-8")
        for token in _forbidden_tokens():
            assert token not in text, f"{script.name} contains forbidden token: {token}"


def test_lot6_scripts_use_clean_main_exit_pattern():
    for script in SCRIPTS:
        text = script.read_text(encoding="utf-8")
        assert "raise SystemExit(main())" in text, f"{script.name} must end with raise SystemExit(main())"
