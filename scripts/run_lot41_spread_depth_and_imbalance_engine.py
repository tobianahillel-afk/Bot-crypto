#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine import (  # noqa: E402
    write_lot41_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic offline Lot 41 book features")
    parser.add_argument("--code-commit", required=True)
    arguments = parser.parse_args()
    try:
        state, audit, feature = write_lot41_artifacts(ROOT, arguments.code_commit)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"LOT41 RUN: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "state_output_checksum": state["output_checksum"],
                "audit_checksum": audit["audit_checksum"],
                "feature_checksum": feature["feature_checksum"],
                "spread_bps": feature["spread_bps"],
                "trade_allowed": state["safety"]["trade_allowed"],
                "execution_allowed": state["safety"]["execution_allowed"],
                "approved_size": state["safety"]["approved_size"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
