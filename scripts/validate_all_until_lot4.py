#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    return int(subprocess.call(["bash", "scripts/validate_all_until_lot4.sh"], cwd=ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
