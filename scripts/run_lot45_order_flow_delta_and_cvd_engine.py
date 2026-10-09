#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (  # noqa: E402
    write_lot45_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic offline Lot45 order-flow, delta and CVD engine"
    )
    parser.add_argument("--code-commit", required=True)
    arguments = parser.parse_args()
    try:
        state, audit, order_flow, cvd = write_lot45_artifacts(
            ROOT,
            arguments.code_commit,
        )
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"LOT45 RUN: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "state_output_checksum": state["output_checksum"],
                "audit_checksum": audit["audit_checksum"],
                "order_flow_checksum": order_flow["order_flow_checksum"],
                "cvd_checksum": cvd["cvd_checksum"],
                "trades_total": order_flow["trades_total"],
                "signed_delta": order_flow["signed_delta"],
                "unknown_volume": order_flow["unknown_volume"],
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
