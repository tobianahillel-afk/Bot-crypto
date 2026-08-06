#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    build_lot31_artifacts,
    persist_lot31_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic Lot 31 metadata artifacts")
    parser.add_argument("--code-commit", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state, audit = build_lot31_artifacts(ROOT, args.code_commit)
    persist_lot31_artifacts(ROOT, state, audit)
    print(state.output_checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
