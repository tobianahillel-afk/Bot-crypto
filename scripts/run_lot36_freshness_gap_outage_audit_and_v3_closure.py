#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure import (  # noqa: E402
    write_lot36_artifacts,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    load_json_object,
)

STATE_PATH = ROOT / "data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build deterministic Lot 36 V3 closure artifacts"
    )
    parser.add_argument("--code-commit", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_lot36_artifacts(ROOT, args.code_commit)
    state = load_json_object(STATE_PATH)
    print(state["output_checksum"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
