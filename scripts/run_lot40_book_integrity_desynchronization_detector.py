#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector import (
    write_lot40_artifacts,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Run Lot 40 offline Book Integrity / Desynchronization Detector"
    )
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--code-commit", required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    state, audit = write_lot40_artifacts(args.root.resolve(), args.code_commit)
    integrity = state.book_integrity
    veto = state.book_health_veto
    print(
        json.dumps(
            {
                "status": "PASS",
                "validation_state": state.validation_state,
                "health_status": integrity.health_status,
                "book_health_score": str(integrity.book_health_score),
                "consequence": veto.consequence,
                "state_output_checksum": state.output_checksum,
                "audit_checksum": audit.audit_checksum,
                "integrity_checksum": integrity.integrity_checksum,
                "veto_checksum": veto.veto_checksum,
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
