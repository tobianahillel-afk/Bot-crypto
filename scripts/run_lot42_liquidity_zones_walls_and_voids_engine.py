#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine import (  # noqa: E402
    write_lot42_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic offline Lot 42 liquidity zones, walls and voids"
    )
    parser.add_argument("--code-commit", required=True)
    arguments = parser.parse_args()
    try:
        state, audit, zone_set = write_lot42_artifacts(ROOT, arguments.code_commit)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"LOT42 RUN: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "state_output_checksum": state["output_checksum"],
                "audit_checksum": audit["audit_checksum"],
                "zone_set_checksum": zone_set["zone_set_checksum"],
                "active_zones_total": len(zone_set["zones"]),
                "liquidity_voids_total": len(zone_set["voids"]),
                "participant_intent_inferred": zone_set["participant_intent_inferred"],
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
