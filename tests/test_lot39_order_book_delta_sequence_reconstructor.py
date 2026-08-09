from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor as engine
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor import (
    build_lot39_artifacts,
    reconstruct_sequence,
    write_lot39_artifacts,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_models import (
    BLOCKED_STATE,
    SUCCESS_STATE,
    OrderBookDeltaV1,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "d" * 40


def _reference_inputs() -> tuple[object, tuple[OrderBookDeltaV1, ...], str]:
    config = json.loads((ROOT / engine.CONFIG_PATH).read_text(encoding="utf-8"))
    snapshot = engine._verify_lot38(ROOT, config)
    deltas, fixture_checksum = engine._load_deltas(ROOT, config)
    return snapshot, deltas, fixture_checksum


def _gap_delta(delta: OrderBookDeltaV1) -> OrderBookDeltaV1:
    return replace(delta, sequence_id=delta.sequence_id + 1)


def _missing_delete(delta: OrderBookDeltaV1) -> OrderBookDeltaV1:
    return replace(
        delta,
        bids=(OrderBookLevelV1(Decimal("49999"), Decimal("0")),),
        asks=(),
    )


def _crossing_delta(delta: OrderBookDeltaV1) -> OrderBookDeltaV1:
    return replace(
        delta,
        bids=(OrderBookLevelV1(Decimal("60000"), Decimal("1")),),
        asks=(),
    )


def test_canonical_reference_is_synced_deterministic_and_non_decisional() -> None:
    state1, audit1 = build_lot39_artifacts(ROOT, CODE_COMMIT)
    state2, audit2 = build_lot39_artifacts(ROOT, CODE_COMMIT)

    assert state1.to_dict() == state2.to_dict()
    assert audit1.to_dict() == audit2.to_dict()
    assert state1.validation_state == SUCCESS_STATE
    assert state1.synchronization_state == "SYNCED"
    assert state1.reconstructed_book is not None
    assert state1.sequence_gap_event is None
    assert state1.reconstructed_book.sequence_id == 1003
    assert state1.reconstructed_book.applied_delta_count == 2
    assert [level.price for level in state1.reconstructed_book.bids] == [
        Decimal("50024.9"),
        Decimal("50024.7"),
    ]
    assert [level.quantity for level in state1.reconstructed_book.bids] == [
        Decimal("0.9"),
        Decimal("0.5"),
    ]
    assert state1.safety["used_for_decision"] is False
    assert state1.safety["trade_allowed"] is False
    assert state1.safety["execution_allowed"] is False
    assert state1.safety["approved_size"] == 0
    assert audit1.reconstructed_book_checksum == state1.reconstructed_book.book_checksum
    assert audit1.sequence_gap_event_checksum is None


def test_zero_quantity_deletes_existing_level_exactly() -> None:
    snapshot, deltas, _ = _reference_inputs()
    outcome = reconstruct_sequence(snapshot, deltas)
    assert outcome.synchronization_state == "SYNCED"
    assert outcome.reconstructed_book is not None
    prices = {level.price for level in outcome.reconstructed_book.bids}
    assert Decimal("50024.8") not in prices
    assert outcome.metrics.levels_deleted_total == 1
    assert outcome.metrics.levels_upserted_total == 4


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (_gap_delta, "LOT39_SEQUENCE_GAP_DETECTED"),
        (_missing_delete, "LOT39_DELETE_MISSING_LEVEL_RESYNC_REQUIRED"),
        (_crossing_delta, "LOT39_CROSSED_OR_LOCKED_BOOK_AFTER_DELTA"),
    ],
)
def test_integrity_failures_require_resync_without_published_book(mutator, reason) -> None:
    snapshot, deltas, _ = _reference_inputs()
    damaged = (mutator(deltas[0]),)
    outcome = reconstruct_sequence(snapshot, damaged)
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert outcome.sequence_gap_event is not None
    assert outcome.sequence_gap_event.gap_detected is True
    assert outcome.sequence_gap_event.synchronization_state == "RESYNC_REQUIRED"
    assert reason in outcome.reason_codes
    assert "LOT40_REMAINS_LOCKED" in outcome.reason_codes


def test_duplicate_or_reordered_sequence_requires_resync() -> None:
    snapshot, deltas, _ = _reference_inputs()
    duplicate = replace(deltas[1], sequence_id=1002, prev_sequence=1001)
    outcome = reconstruct_sequence(snapshot, (deltas[0], duplicate))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert "LOT39_DUPLICATE_OR_REORDERED_SEQUENCE" in outcome.reason_codes


def test_reordered_event_time_requires_resync() -> None:
    snapshot, deltas, _ = _reference_inputs()
    reordered = replace(
        deltas[1],
        event_time="2026-08-06T19:18:39.990000Z",
        receive_time="2026-08-06T19:18:40.070000Z",
    )
    outcome = reconstruct_sequence(snapshot, (deltas[0], reordered))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert "LOT39_REORDERED_EVENT_TIME" in outcome.reason_codes


def test_expected_checksum_mismatch_requires_resync() -> None:
    snapshot, deltas, _ = _reference_inputs()
    mismatch = replace(deltas[0], expected_book_checksum="0" * 64)
    outcome = reconstruct_sequence(snapshot, (mismatch,))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert "LOT39_BOOK_CHECKSUM_MISMATCH" in outcome.reason_codes


def test_negative_quantity_is_rejected_at_level_boundary() -> None:
    with pytest.raises(Exception, match="quantity"):
        OrderBookLevelV1(Decimal("50000"), Decimal("-0.1"))


def test_build_artifacts_persists_blocked_resync_state_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, deltas, fixture_checksum = _reference_inputs()
    damaged = (_gap_delta(deltas[0]),)
    monkeypatch.setattr(
        engine,
        "_load_deltas",
        lambda root, config: (damaged, fixture_checksum),
    )
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state.validation_state == BLOCKED_STATE
    assert state.synchronization_state == "RESYNC_REQUIRED"
    assert state.reconstructed_book is None
    assert state.sequence_gap_event is not None
    assert audit.validation_state == BLOCKED_STATE
    assert audit.synchronization_state == "RESYNC_REQUIRED"
    assert audit.reconstructed_book_checksum is None
    assert audit.sequence_gap_event_checksum == state.sequence_gap_event.event_checksum


def test_write_artifacts_publishes_exactly_one_outcome_surface(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    audit_path = tmp_path / "audit.json"
    book_path = tmp_path / "book.json"
    gap_path = tmp_path / "gap.json"
    monkeypatch.setattr(engine, "STATE_PATH", state_path)
    monkeypatch.setattr(engine, "AUDIT_PATH", audit_path)
    monkeypatch.setattr(engine, "BOOK_PATH", book_path)
    monkeypatch.setattr(engine, "GAP_EVENT_PATH", gap_path)

    write_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state_path.exists() and audit_path.exists() and book_path.exists()
    assert not gap_path.exists()

    _, deltas, fixture_checksum = _reference_inputs()
    damaged = (_gap_delta(deltas[0]),)
    monkeypatch.setattr(
        engine,
        "_load_deltas",
        lambda root, config: (damaged, fixture_checksum),
    )
    write_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state_path.exists() and audit_path.exists() and gap_path.exists()
    assert not book_path.exists()


def test_empty_delta_sequence_is_rejected() -> None:
    snapshot, _, _ = _reference_inputs()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="at least one delta"):
        reconstruct_sequence(snapshot, ())
