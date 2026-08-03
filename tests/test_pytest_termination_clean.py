from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pytest_conftest_has_no_forced_termination_logic():
    text = (ROOT / "tests/conftest.py").read_text(encoding="utf-8")
    forbidden = [
        "os." + "_exit",
        "signal." + "alarm",
        "CQB_DISABLE" + "_PYTEST_FORCE_EXIT",
        "pytest_" + "sessionfinish",
        "pytest_" + "terminal_summary",
        "pytest_" + "unconfigure",
        "SIGALRM",
    ]
    for token in forbidden:
        assert token not in text


def test_ci_scripts_do_not_disable_pytest_force_exit():
    for rel in [
        "scripts/run_required_chain_until_lot9.sh",
        "scripts/diagnose_pytest_after_chain.py",
        "scripts/run_required_chain_until_lot10.sh",
        "scripts/diagnose_lot10_chain.py",
        "scripts/diagnose_lot10_lingering_processes.py",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "CQB_DISABLE" + "_PYTEST_FORCE_EXIT" not in text
