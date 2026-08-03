#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    forbidden = [
        ROOT / ("pytest" + ".py"),
        ROOT / "pytest",
        ROOT / "unittest.py",
        ROOT / "subprocess.py",
        ROOT / "signal.py",
        ROOT / "os.py",
    ]
    for path in forbidden:
        if path.exists():
            print(f"forbidden local test/module shadowing path exists: {path.relative_to(ROOT)}", flush=True)
            return 1
    import pytest

    pytest_path = Path(pytest.__file__).resolve()
    if pytest_path == ROOT / ("pytest" + ".py") or ROOT in pytest_path.parents:
        print(f"pytest resolves inside project: {pytest_path}", flush=True)
        return 1
    print(f"pytest_path={pytest_path}", flush=True)
    print("DIAGNOSE PYTEST RESOLUTION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
