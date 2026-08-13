#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    write_lot44_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Lot 44 offline aggressor classification")
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    state, audit = write_lot44_artifacts(Path(args.root).resolve(), code_commit=args.code_commit)
    print(json.dumps({
        "status": "PASS",
        "state_output_checksum": state.output_checksum,
        "audit_checksum": audit.audit_checksum,
        "trades_total": state.metrics.trades_total,
        "unknown_volume_ratio": str(state.metrics.unknown_volume_ratio),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
