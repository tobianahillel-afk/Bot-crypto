#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_TEST = ROOT / "tests" / "test_p06_market_foundation_complete.py"
CHANGED = [
    ROOT / "tests" / "test_p06_closure_archive_complete.py",
    ROOT / "tests" / "test_p06_closure_io_and_release_helpers.py",
    FOUNDATION_TEST,
    ROOT / "tests" / "test_p06_trend_range_momentum_complete.py",
    ROOT / "tests" / "test_p06_vrc_complete.py",
]


def main() -> int:
    text = FOUNDATION_TEST.read_text(encoding="utf-8")
    text = text.replace(
        '    assert {"a", "b", "m"}.issubset(artifacts)\n',
        '    assert {"a", "b", "m"}.issubset(set(artifacts))\n',
        1,
    )
    FOUNDATION_TEST.write_text(text, encoding="utf-8")
    subprocess.run(
        ["ruff", "check", "--fix", *[str(path.relative_to(ROOT)) for path in CHANGED]],
        cwd=ROOT,
        check=True,
    )
    print("P0.6 Ruff cleanup applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
