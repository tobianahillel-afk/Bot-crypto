from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [ROOT / "scripts", ROOT / "src", ROOT / "tests"]


def forbidden_tokens() -> list[str]:
    return [
        "multi" + "processing",
        "threading." + "Thread",
        "daemon" + "=False",
        "atexit." + "register",
        "subprocess." + "Popen",
        "os." + "fork",
        "asyncio." + "create_task",
        "os." + "system",
        "os." + "spawn",
        "os." + "posix_spawn",
    ]


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCAN_DIRS:
        files.extend(sorted(directory.glob("**/*.py")))
    return files


def test_no_background_process_or_fd_hacks_in_active_code() -> None:
    offenders: list[str] = []
    for path in iter_python_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in forbidden_tokens():
            if token in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()} contains {token}")
        pty_token = "p" + "ty"
        if re.search(r"(?<![A-Za-z0-9_])" + pty_token + r"(?![A-Za-z0-9_])", text):
            offenders.append(f"{path.relative_to(ROOT).as_posix()} contains {pty_token}")
    assert offenders == []
