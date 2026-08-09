#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine import (
    write_lot38_artifacts,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Run Lot 38 offline L2 snapshot engine")
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--code-commit", required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    state, audit = write_lot38_artifacts(args.root.resolve(), args.code_commit)
    print(
        json.dumps(
            {
                "status": "PASS",
                "validation_state": state.validation_state,
                "state_output_checksum": state.output_checksum,
                "audit_checksum": audit.audit_checksum,
                "snapshot_checksum": state.snapshot.snapshot_checksum,
                "health_checksum": state.book_health.health_checksum,
                "published_bid_depth": state.snapshot.published_bid_depth,
                "published_ask_depth": state.snapshot.published_ask_depth,
                "trade_allowed": state.safety["trade_allowed"],
                "execution_allowed": state.safety["execution_allowed"],
                "approved_size": state.safety["approved_size"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
