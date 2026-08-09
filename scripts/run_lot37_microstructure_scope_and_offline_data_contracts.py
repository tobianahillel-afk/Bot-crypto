#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.microstructure import write_lot37_artifacts  # noqa: E402


def current_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Lot 37 offline microstructure scope and contract registry"
    )
    parser.add_argument("--code-commit", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code_commit = args.code_commit or current_commit(ROOT)
    outputs = write_lot37_artifacts(ROOT, code_commit)
    print(json.dumps({"status": "PASS", "code_commit": code_commit, "outputs": outputs}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
