from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [ROOT / "scripts", ROOT / "src", ROOT / "tests"]
SUB = "subprocess"


def _forbidden_tokens() -> list[str]:
    return [
        "close_standard" + "_streams",
        "os.open(os." + "devnull",
        "os." + "dup2(",
        "devnull" + "_fd",
        "stdout=" + SUB + "." + "DEVNULL",
        "stderr=" + SUB + "." + "DEVNULL",
        "stdin=" + SUB + "." + "DEVNULL",
        "os." + "_exit",
        "signal." + "alarm",
        "CQB_DISABLE_" + "PYTEST_FORCE_EXIT",
    ]


def _iter_code_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".sh"}:
                files.append(path)
    return sorted(files)


def test_active_code_has_no_stdout_stderr_detach_hacks():
    offenders: list[str] = []
    forbidden = _forbidden_tokens()
    for path in _iter_code_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()} contains {token}")
    assert offenders == []


def test_no_local_pytest_shadowing_file_exists():
    assert not (ROOT / ("pytest" + ".py")).exists()
