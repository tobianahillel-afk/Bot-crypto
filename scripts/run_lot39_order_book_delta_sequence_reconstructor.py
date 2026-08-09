#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor import (
    write_lot39_artifacts,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Run Lot 39 offline order-book delta sequence reconstructor"
    )
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--code-commit", required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    state, audit = write_lot39_artifacts(args.root.resolve(), args.code_commit)
    book_checksum = (
        state.reconstructed_book.book_checksum if state.reconstructed_book is not None else None
    )
    gap_checksum = (
        state.sequence_gap_event.event_checksum if state.sequence_gap_event is not None else None
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "validation_state": state.validation_state,
                "synchronization_state": state.synchronization_state,
                "state_output_checksum": state.output_checksum,
                "audit_checksum": audit.audit_checksum,
                "reconstructed_book_checksum": book_checksum,
                "sequence_gap_event_checksum": gap_checksum,
                "final_sequence_id": state.metrics.final_sequence_id,
                "applied_delta_count": state.metrics.deltas_applied_total,
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
