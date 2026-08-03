from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = "subprocess"

DIAGNOSTICS = [
    ROOT / "scripts" / "diagnose_lot4_validate_after_chain.py",
    ROOT / "scripts" / "diagnose_lot5_validate_after_chain.py",
    ROOT / "scripts" / "diagnose_lot5_fd_lingering_owner.py",
    ROOT / "scripts" / "diagnose_lot7_build_after_chain.py",
    ROOT / "scripts" / "diagnose_lot8_no_lookahead_after_chain.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot10.py",
    ROOT / "scripts" / "diagnose_lot11_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot11.py",
    ROOT / "scripts" / "diagnose_lot12_required_chain_timing.py",
    ROOT / "scripts" / "diagnose_exact_chain_until_lot12.py",
    ROOT / "scripts" / "diagnose_after_pytest_lingering.py",
    ROOT / "scripts" / "diagnose_exact_chain_return_shell.py",
    ROOT / "scripts" / "diagnose_lingering_processes.py",
]


def _forbidden_tokens() -> list[str]:
    return [
        SUB + "." + "Popen",
        "start_new" + "_session=True",
        "os." + "killpg",
        "signal." + "SIG" + "TERM",
        "signal." + "SIG" + "KILL",
        "process." + "wait(",
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


def test_diagnostics_use_subprocess_run_only_with_timeout():
    offenders: list[str] = []
    for path in DIAGNOSTICS:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in _forbidden_tokens():
            if token in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()} contains {token}")
        if SUB + "." + "run" not in text:
            offenders.append(f"{path.relative_to(ROOT).as_posix()} missing subprocess.run")
        if "timeout=" not in text:
            offenders.append(f"{path.relative_to(ROOT).as_posix()} missing timeout argument")
        if "raise SystemExit(main())" not in text and "raise SystemExit(main(sys.argv[1:]))" not in text:
            offenders.append(f"{path.relative_to(ROOT).as_posix()} missing SystemExit main pattern")
    assert offenders == []
