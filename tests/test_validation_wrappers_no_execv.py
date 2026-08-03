from pathlib import Path

WRAPPERS = [
    Path("scripts/validate_all_until_lot5.py"),
    Path("scripts/validate_all_until_lot6.py"),
    Path("scripts/validate_all_until_lot7.py"),
    Path("scripts/validate_all_until_lot8.py"),
    Path("scripts/validate_all_until_lot9.py"),
    Path("scripts/validate_all_until_lot10.py"),
    Path("scripts/validate_all_until_lot11.py"),
    Path("scripts/validate_all_until_lot12.py"),
]

FORBIDDEN_TOKENS = [
    "os." + "_exit",
    "os.execv",
    "os.execve",
    "os.execvp",
    "os.execvpe",
    "capture_" + "output=True",
    "stdout=subprocess." + "PIPE",
    "stderr=subprocess." + "PIPE",
]


def test_validation_wrappers_do_not_use_execv_or_capture_pipes():
    for path in WRAPPERS:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{path} contains forbidden token: {token}"


def test_validation_wrappers_delegate_to_shell_once():
    for path in WRAPPERS:
        text = path.read_text(encoding="utf-8")
        lot = path.stem.removeprefix("validate_all_until_lot")
        assert "subprocess.run" in text
        assert f"scripts/validate_all_until_lot{lot}.sh" in text
        assert "timeout=300" in text
