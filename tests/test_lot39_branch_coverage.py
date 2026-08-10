from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor as engine
from crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor_models import (
    Lot39MetricsV1,
    OrderBookDeltaV1,
    SequenceGapEventV1,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "c" * 40
ZERO = "0" * 64


def _inputs():
    config = json.loads((ROOT / engine.CONFIG_PATH).read_text(encoding="utf-8"))
    snapshot = engine._verify_lot38(ROOT, config)
    deltas, _ = engine._load_deltas(ROOT, config)
    return snapshot, deltas


def test_reconstructed_book_model_rejects_invalid_states() -> None:
    state, _ = engine.build_lot39_artifacts(ROOT, CODE_COMMIT)
    book = state.reconstructed_book
    assert book is not None
    cases = [
        (replace, {"market_type": "FUTURES"}, "market_type"),
        (replace, {"sequence_id": book.base_sequence_id}, "must advance"),
        (replace, {"synchronization_state": "RESYNC_REQUIRED"}, "only SYNCED"),
        (replace, {"bids": ()}, "non-empty"),
        (replace, {"bids": tuple(reversed(book.bids))}, "descending"),
        (replace, {"asks": tuple(reversed(book.asks))}, "ascending"),
    ]
    for operation, changes, message in cases:
        with pytest.raises(OrderBookDeltaSequenceValidationError, match=message):
            operation(book, **changes)
    crossed = (OrderBookLevelV1(Decimal("60000"), Decimal("1")),)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="crossed or locked"):
        replace(book, bids=crossed)


def test_delta_and_gap_model_edges() -> None:
    _, deltas = _inputs()
    delta = deltas[0]
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="market_type"):
        replace(delta, market_type="FUTURES")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="at least one side"):
        replace(delta, bids=(), asks=())
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="decision data"):
        replace(delta, used_for_decision=True)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(delta, expected_book_checksum="bad")

    gap = SequenceGapEventV1(
        True,
        "RESYNC_REQUIRED",
        1002,
        1003,
        1001,
        delta.event_time,
        ("LOT39_SEQUENCE_GAP_DETECTED",),
        ZERO,
    )
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="resync and observed"):
        replace(gap, synchronization_state="SYNCED")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="no-gap"):
        replace(gap, gap_detected=False)


def test_metrics_impossible_count_and_latency_branch() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="exceed"):
        Lot39MetricsV1(1, 2, 0, 0, 0, 1001)
    assert Lot39MetricsV1(2, 2, 1, 4, 0, 1003, processing_latency_us=1).processing_latency_us == 1


def test_identity_mismatch_raises_before_sequence_processing() -> None:
    snapshot, deltas = _inputs()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="identity"):
        engine.reconstruct_sequence(
            snapshot,
            (replace(deltas[0], instrument_id="ETH-EUR-SPOT"),),
        )


@pytest.mark.parametrize(
    ("sequence_id", "prev_sequence", "reason"),
    [
        (1001, 1001, "LOT39_DUPLICATE_OR_REORDERED_SEQUENCE"),
        (1002, 1000, "LOT39_DUPLICATE_OR_REORDERED_SEQUENCE"),
        (1003, 1001, "LOT39_SEQUENCE_GAP_DETECTED"),
        (1003, 1002, "LOT39_SEQUENCE_GAP_DETECTED"),
    ],
)
def test_sequence_failures_require_resync(
    sequence_id: int, prev_sequence: int, reason: str
) -> None:
    snapshot, deltas = _inputs()
    outcome = engine.reconstruct_sequence(
        snapshot,
        (replace(deltas[0], sequence_id=sequence_id, prev_sequence=prev_sequence),),
    )
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert outcome.sequence_gap_event is not None
    assert reason in outcome.reason_codes


def test_reordered_time_checksum_and_missing_delete_fail_closed() -> None:
    snapshot, deltas = _inputs()
    earlier = replace(
        deltas[0],
        event_time="2026-08-06T19:18:39.999999Z",
        receive_time=deltas[0].receive_time,
    )
    assert "LOT39_REORDERED_EVENT_TIME" in engine.reconstruct_sequence(snapshot, (earlier,)).reason_codes

    mismatch = replace(deltas[0], expected_book_checksum=ZERO)
    assert "LOT39_BOOK_CHECKSUM_MISMATCH" in engine.reconstruct_sequence(snapshot, (mismatch,)).reason_codes

    missing = replace(
        deltas[0],
        bids=(OrderBookLevelV1(Decimal("49900"), Decimal("0")),),
        asks=(),
    )
    result = engine.reconstruct_sequence(snapshot, (missing,))
    assert "LOT39_DELETE_MISSING_LEVEL_RESYNC_REQUIRED" in result.reason_codes


def test_empty_and_crossed_books_fail_closed() -> None:
    snapshot, deltas = _inputs()
    deletes = tuple(OrderBookLevelV1(level.price, Decimal("0")) for level in snapshot.bids)
    empty = OrderBookDeltaV1(
        snapshot.source_id,
        snapshot.venue,
        snapshot.instrument_id,
        snapshot.market_type,
        deltas[0].event_time,
        deltas[0].receive_time,
        1002,
        1001,
        deletes,
        (),
        None,
        False,
    )
    assert "LOT39_EMPTY_BOOK_AFTER_DELTA" in engine.reconstruct_sequence(snapshot, (empty,)).reason_codes

    crossed = replace(
        deltas[0],
        bids=(OrderBookLevelV1(Decimal("50025.1"), Decimal("1")),),
        asks=(),
    )
    assert "LOT39_CROSSED_OR_LOCKED_BOOK_AFTER_DELTA" in engine.reconstruct_sequence(
        snapshot, (crossed,)
    ).reason_codes


def test_empty_sequence_is_rejected() -> None:
    snapshot, _ = _inputs()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="at least one delta"):
        engine.reconstruct_sequence(snapshot, ())


def test_exact_checksum_match_is_accepted() -> None:
    snapshot, deltas = _inputs()
    first = engine.reconstruct_sequence(snapshot, (deltas[0],))
    assert first.reconstructed_book is not None
    exact = replace(deltas[0], expected_book_checksum=first.reconstructed_book.book_checksum)
    replay = engine.reconstruct_sequence(snapshot, (exact,))
    assert replay.reconstructed_book is not None
    assert replay.reconstructed_book.book_checksum == first.reconstructed_book.book_checksum
