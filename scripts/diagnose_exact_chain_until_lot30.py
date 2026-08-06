from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from run_lot30_v2_market_analysis_closure import run as run_lot30  # noqa: E402
from validate_lot30 import validate as validate_lot30  # noqa: E402


def _git_commit(root: Path) -> str:
    completed = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def diagnose(root: Path, code_commit: str) -> dict[str, Any]:
    first = run_lot30(root, code_commit)
    first_state = json.dumps(first["state"], sort_keys=True, separators=(",", ":"))
    second = run_lot30(root, code_commit)
    second_state = json.dumps(second["state"], sort_keys=True, separators=(",", ":"))
    validation = validate_lot30(root)
    if first_state != second_state:
        raise RuntimeError("LOT30_EXACT_CHAIN_REPLAY_DIVERGED")
    return {
        "schema_version": "lot30-exact-chain-diagnostic-v1",
        "status": "PASS",
        "code_commit": code_commit,
        "replay_match": True,
        "covered_lot_count": validation["covered_lot_count"],
        "negative_control_count": validation["negative_control_count"],
        "final_chain_checksum": validation["final_chain_checksum"],
        "output_checksum": validation["output_checksum"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose the exact chain through Lot 30")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    root = args.root.resolve()
    result = diagnose(root, args.code_commit or _git_commit(root))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
