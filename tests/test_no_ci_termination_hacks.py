from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = [ROOT / "scripts", ROOT / "src", ROOT / "tests"]
FORBIDDEN = [
    "os." + "_exit",
    "signal." + "alarm",
    "CQB_DISABLE_" + "PYTEST_FORCE_EXIT",
]


def _active_python_files():
    for directory in CODE_DIRS:
        for path in directory.rglob("*.py"):
            if any(part == "__pycache__" for part in path.parts):
                continue
            yield path


def test_no_ci_termination_hacks_in_active_code():
    for path in _active_python_files():
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, f"{path.relative_to(ROOT)} contains forbidden CI termination hack token"


def test_no_local_pytest_shadowing_file():
    assert not (ROOT / ("pytest" + ".py")).exists()
