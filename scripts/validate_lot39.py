#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor import (
    AUDIT_PATH,
    BOOK_PATH,
    GAP_EVENT_PATH,
    STATE_PATH,
    build_lot39_artifacts,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
    lot39_safety,
)

EXPECTED_BIDS = [
    {"price": "50024.9", "quantity": "0.9"},
    {"price": "50024.7", "quantity": "0.5"},
]
EXPECTED_ASKS = [
    {"price": "50025.1", "quantity": "0.65"},
    {"price": "50025.2", "quantity": "1.1"},
    {"price": "50025.3", "quantity": "0.4"},
]
LOT40_FORBIDDEN_PATHS = (
    "src/crypto_quant_bot/microstructure/book_integrity_and_desynchronization_detector.py",
    "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector.py",
    "scripts/run_lot40_book_integrity_and_desynchronization_detector.py",
    "scripts/validate_lot40.py",
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Validate Lot 39 deterministic reconstruction")
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--expected-code-commit", required=True)
    value.add_argument("--require-persisted", action="store_true")
    return value


def _verify_canonical_reference(root: Path, code_commit: str) -> tuple[dict[str, Any], dict[str, Any]]:
    state, audit = build_lot39_artifacts(root, code_commit)
    state_payload = state.to_dict()
    audit_payload = audit.to_dict()

    if state.validation_state != "VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY":
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 validation state changed")
    if state.synchronization_state != "SYNCED":
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 fixture is not SYNCED")
    if state.reconstructed_book is None or state.sequence_gap_event is not None:
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 output pair changed")
    book = state.reconstructed_book.to_dict()
    if book["bids"] != EXPECTED_BIDS:
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 bids changed")
    if book["asks"] != EXPECTED_ASKS:
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 asks changed")
    if book["base_sequence_id"] != 1001 or book["sequence_id"] != 1003:
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 sequence changed")
    if book["applied_delta_count"] != 2:
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 applied delta count changed")
    metrics = state.metrics.to_dict()
    expected_metrics = {
        "lot_39_deltas_received_total": 2,
        "lot_39_deltas_applied_total": 2,
        "lot_39_levels_deleted_total": 1,
        "lot_39_levels_upserted_total": 4,
        "lot_39_sequence_gap_events_total": 0,
        "lot_39_final_sequence_id": 1003,
    }
    for field, expected in expected_metrics.items():
        if metrics[field] != expected:
            raise OrderBookDeltaSequenceValidationError(f"canonical Lot 39 metric changed: {field}")
    if state.safety != lot39_safety() or audit.safety != lot39_safety():
        raise OrderBookDeltaSequenceValidationError("Lot 39 safety boundary changed")
    if "LOT40_REMAINS_LOCKED" not in state.reason_codes:
        raise OrderBookDeltaSequenceValidationError("Lot 40 lock reason missing")
    if audit.state_output_checksum != state.output_checksum:
        raise OrderBookDeltaSequenceValidationError("Lot 39 state/audit checksum link changed")
    if audit.reconstructed_book_checksum != state.reconstructed_book.book_checksum:
        raise OrderBookDeltaSequenceValidationError("Lot 39 book/audit checksum link changed")
    if audit.sequence_gap_event_checksum is not None:
        raise OrderBookDeltaSequenceValidationError("healthy Lot 39 audit unexpectedly has gap checksum")
    return state_payload, audit_payload


def _verify_deterministic(root: Path, code_commit: str) -> tuple[dict[str, Any], dict[str, Any]]:
    state1, audit1 = _verify_canonical_reference(root, code_commit)
    state2, audit2 = _verify_canonical_reference(root, code_commit)
    if state1 != state2 or audit1 != audit2:
        raise OrderBookDeltaSequenceValidationError("Lot 39 replay is non-deterministic")
    return state1, audit1


def _verify_persisted(root: Path, state: dict[str, Any], audit: dict[str, Any]) -> None:
    paths = {
        "state": root / STATE_PATH,
        "audit": root / AUDIT_PATH,
        "book": root / BOOK_PATH,
    }
    for label, path in paths.items():
        if not path.exists():
            raise OrderBookDeltaSequenceValidationError(f"persisted Lot 39 {label} missing")
    if (root / GAP_EVENT_PATH).exists():
        raise OrderBookDeltaSequenceValidationError("healthy Lot 39 replay must not persist gap event")
    persisted_state = load_json_object(paths["state"])
    persisted_audit = load_json_object(paths["audit"])
    persisted_book = load_json_object(paths["book"])
    if persisted_state != state:
        raise OrderBookDeltaSequenceValidationError("persisted Lot 39 state differs from replay")
    if persisted_audit != audit:
        raise OrderBookDeltaSequenceValidationError("persisted Lot 39 audit differs from replay")
    if persisted_book != state["reconstructed_book"]:
        raise OrderBookDeltaSequenceValidationError("persisted Lot 39 book differs from replay")
    state_body = dict(persisted_state)
    state_checksum = state_body.pop("output_checksum")
    if canonical_checksum(state_body) != state_checksum:
        raise OrderBookDeltaSequenceValidationError("persisted Lot 39 state checksum invalid")
    audit_body = dict(persisted_audit)
    audit_checksum = audit_body.pop("audit_checksum")
    if canonical_checksum(audit_body) != audit_checksum:
        raise OrderBookDeltaSequenceValidationError("persisted Lot 39 audit checksum invalid")
    book_body = dict(persisted_book)
    book_checksum = book_body.pop("book_checksum")
    if canonical_checksum(book_body) != book_checksum:
        raise OrderBookDeltaSequenceValidationError("persisted Lot 39 book checksum invalid")


def _verify_lot40_absent(root: Path) -> None:
    for relative in LOT40_FORBIDDEN_PATHS:
        if (root / relative).exists():
            raise OrderBookDeltaSequenceValidationError(f"Lot 40 implementation detected: {relative}")


def validate(root: Path, code_commit: str, require_persisted: bool) -> dict[str, Any]:
    state, audit = _verify_deterministic(root, code_commit)
    _verify_lot40_absent(root)
    if require_persisted:
        _verify_persisted(root, state, audit)
    book = state["reconstructed_book"]
    if not isinstance(book, dict):
        raise OrderBookDeltaSequenceValidationError("canonical Lot 39 book missing")
    result: dict[str, Any] = {
        "schema_version": "lot39-validation-result-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "synchronization_state": state["synchronization_state"],
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "reconstructed_book_checksum": book["book_checksum"],
        "sequence_gap_event_checksum": None,
        "final_sequence_id": 1003,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "lot40_status": "PLANNED_LOCKED",
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = validate(args.root.resolve(), args.expected_code_commit, args.require_persisted)
        print(json.dumps(result, sort_keys=True))
    except (OrderBookDeltaSequenceValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT39 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
