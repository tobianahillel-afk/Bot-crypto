from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_local_test_runner_or_stdlib_shadowing_at_project_root():
    forbidden = [
        "pytest" + ".py",
        "pytest",
        "unittest.py",
        "subprocess.py",
        "signal.py",
        "os.py",
    ]
    for name in forbidden:
        assert not (ROOT / name).exists(), f"forbidden root shadowing path exists: {name}"
