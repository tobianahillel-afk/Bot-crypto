#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "src" / "crypto_quant_bot" / "release" / "candidate.py"
FOUNDATION_TEST = ROOT / "tests" / "test_p06_market_foundation_complete.py"
VRC_TEST = ROOT / "tests" / "test_p06_vrc_complete.py"
CHANGED = [
    CANDIDATE,
    ROOT / "tests" / "test_p06_closure_archive_complete.py",
    ROOT / "tests" / "test_p06_closure_io_and_release_helpers.py",
    FOUNDATION_TEST,
    ROOT / "tests" / "test_p06_trend_range_momentum_complete.py",
    VRC_TEST,
]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected source not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        CANDIDATE,
        "import json\nfrom dataclasses import replace\n",
        "import json\nfrom dataclasses import replace\nfrom datetime import UTC, datetime\n",
    )
    replace_once(
        CANDIDATE,
        "datetime.datetime.now(datetime.timezone.utc).isoformat()",
        "datetime.now(UTC).isoformat()",
    )
    replace_once(
        FOUNDATION_TEST,
        '    assert {"a", "b", "m"}.issubset(artifacts)\n',
        '    assert {"a", "b", "m"}.issubset(set(artifacts))\n',
    )
    replace_once(
        VRC_TEST,
        '        "source_v1_archive_size_bytes": size,\n',
        '        "source_v1_archive_size_bytes": size,\n',
    )
    subprocess.run(
        ["ruff", "check", "--fix", *[str(path.relative_to(ROOT)) for path in CHANGED]],
        cwd=ROOT,
        check=True,
    )
    print("P0.6 Ruff cleanup applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
