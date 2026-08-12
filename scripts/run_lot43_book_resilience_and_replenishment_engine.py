#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine import (  # noqa: E402
    write_lot43_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic offline Lot 43 book resilience and replenishment"
    )
    parser.add_argument("--code-commit", required=True)
    arguments = parser.parse_args()
    try:
        state, audit, resilience = write_lot43_artifacts(ROOT, arguments.code_commit)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"LOT43 RUN: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "state_output_checksum": state["output_checksum"],
                "audit_checksum": audit["audit_checksum"],
                "resilience_checksum": resilience["resilience_checksum"],
                "depletion_events_total": len(resilience["depletion_events"]),
                "volatility_regime": resilience["volatility_regime"],
                "participant_intent_inferred": resilience["participant_intent_inferred"],
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
