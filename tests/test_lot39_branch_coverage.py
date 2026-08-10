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
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_models import (
    BLOCKED_STATE,
    SUCCESS_STATE,
    Lot39MetricsV1,
    OrderBookDeltaSequenceReconstructorAuditV1,
    OrderBookDeltaSequenceReconstructorStateV1,
    OrderBookDeltaV1,
    ReconstructedOrderBookV1,
    SequenceGapEventV1,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
    decimal_from_text,
    decimal_text,
    duration_us,
    lot39_safety,
    parse_utc_timestamp,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_lot39_safety,
    validate_reason_codes,
    validate_runtime_mode,
    validate_sync_state,
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


@pytest.mark.parametrize(
    ("call", "pattern"),
    [
        (lambda: require_text("", "x"), "non-empty"),
        (lambda: require_integer(True, "x"), "integer"),
        (lambda: require_integer(-1, "x"), "integer"),
        (lambda: require_git_sha("A" * 40, "x"), "git SHA"),
        (lambda: require_sha256("x", "x"), "sha256"),
        (lambda: parse_utc_timestamp("2026-01-01", "x"), "UTC Z"),
        (lambda: parse_utc_timestamp("not-a-dateZ", "x"), "ISO timestamp"),
        (
            lambda: duration_us(
                parse_utc_timestamp("2026-01-02T00:00:00Z", "a"),
                parse_utc_timestamp("2026-01-01T00:00:00Z", "b"),
            ),
            "backwards",
        ),
        (
            lambda: validate_causal_times(
                "2026-01-02T00:00:00Z",
                "2026-01-01T00:00:00Z",
                "2026-01-03T00:00:00Z",
            ),
            "causal",
        ),
        (lambda: decimal_from_text(1, "x", allow_zero=True), "decimal text"),
        (lambda: decimal_from_text("bad", "x", allow_zero=True), "invalid decimal"),
        (lambda: decimal_from_text("NaN", "x", allow_zero=True), "finite"),
        (lambda: decimal_from_text("-1", "x", allow_zero=True), "non-negative"),
        (lambda: decimal_from_text("0", "x", allow_zero=False), "positive"),
        (lambda: decimal_text(Decimal("NaN")), "finite"),
        (lambda: validate_reason_codes(()), "requires reason"),
        (lambda: validate_reason_codes(("A", "A")), "unique"),
        (lambda: validate_reason_codes(("bad-code",)), "invalid reason"),
        (lambda: validate_runtime_mode("LIVE"), "runtime"),
        (lambda: validate_sync_state("UNKNOWN"), "synchronization"),
        (lambda: validate_lot39_safety({}), "safety"),
    ],
)
def test_validation_fail_closed_branches(call, pattern: str) -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match=pattern):
        call()


def test_validation_happy_helpers() -> None:
    assert require_text("x", "x") == "x"
    assert require_integer(2, "x", 1) == 2
    require_git_sha("a" * 40, "x")
    require_sha256("b" * 64, "x")
    assert decimal_from_text("0", "x", allow_zero=True) == Decimal("0")
    assert decimal_text(Decimal("1.2300")) == "1.23"
    validate_reason_codes(("LOT39_OK",))
    validate_runtime_mode("OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY")
    validate_sync_state("SYNCED")
    validate_sync_state("RESYNC_REQUIRED")
    validate_lot39_safety(lot39_safety())


def test_model_state_and_audit_reject_inconsistent_outcomes() -> None:
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state.reconstructed_book is not None
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="SYNCED Lot 39 state"):
        replace(state, validation_state=BLOCKED_STATE)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="cannot carry gap"):
        gap = SequenceGapEventV1(
            True,
            "RESYNC_REQUIRED",
            1004,
            1005,
            1004,
            "2026-08-06T19:18:40.075000Z",
            ("LOT39_SEQUENCE_GAP_DETECTED",),
            ZERO,
        )
        replace(state, sequence_gap_event=gap)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="validated book checksum"):
        replace(audit, reconstructed_book_checksum=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="cannot carry gap checksum"):
        replace(audit, sequence_gap_event_checksum=ZERO)


def test_blocked_state_and_audit_are_valid_only_with_gap_evidence() -> None:
    snapshot, deltas = _inputs()
    damaged = replace(deltas[0], sequence_id=1003)
    outcome = reconstruct_sequence(snapshot, (damaged,))
    assert outcome.sequence_gap_event is not None
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    blocked = OrderBookDeltaSequenceReconstructorStateV1(
        state.run_context,
        state.lineage,
        damaged.event_time,
        damaged.receive_time,
        state.generated_at,
        BLOCKED_STATE,
        "RESYNC_REQUIRED",
        state.base_snapshot_checksum,
        state.delta_fixture_checksum,
        None,
        outcome.sequence_gap_event,
        outcome.metrics,
        outcome.reason_codes,
        state.safety,
        ZERO,
    )
    assert blocked.reconstructed_book is None
    blocked_audit = OrderBookDeltaSequenceReconstructorAuditV1(
        audit.code_commit,
        audit.config_checksum,
        audit.entry_gate_checksum,
        audit.lot38_state_checksum,
        audit.lot38_snapshot_checksum,
        audit.delta_fixture_checksum,
        ZERO,
        None,
        outcome.sequence_gap_event.event_checksum,
        BLOCKED_STATE,
        "RESYNC_REQUIRED",
        audit.safety,
        ZERO,
    )
    assert blocked_audit.sequence_gap_event_checksum == outcome.sequence_gap_event.event_checksum
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="blocked without book"):
        replace(blocked, reconstructed_book=state.reconstructed_book)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="requires gap evidence"):
        replace(blocked, sequence_gap_event=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="blocked without book checksum"):
        replace(blocked_audit, reconstructed_book_checksum=ZERO)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="requires gap checksum"):
        replace(blocked_audit, sequence_gap_event_checksum=None)


def test_reconstructed_book_model_rejects_invalid_identity_sequence_and_book() -> None:
    state, _ = build_lot39_artifacts(ROOT, CODE_COMMIT)
    book = state.reconstructed_book
    assert book is not None
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="market_type"):
        replace(book, market_type="FUTURES")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="must advance"):
        replace(book, sequence_id=book.base_sequence_id)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="only SYNCED"):
        replace(book, synchronization_state="RESYNC_REQUIRED")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="non-empty"):
        replace(book, bids=())
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="descending"):
        replace(book, bids=tuple(reversed(book.bids)))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="ascending"):
        replace(book, asks=tuple(reversed(book.asks)))
    crossed = (
        OrderBookLevelV1(Decimal("60000"), Decimal("1")),
    )
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="crossed or locked"):
        replace(book, bids=crossed)


def test_delta_and_gap_models_reject_invalid_shapes() -> None:
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
    assert gap.gap_detected is True
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="resync and observed"):
        replace(gap, synchronization_state="SYNCED")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="no-gap"):
        replace(gap, gap_detected=False)


def test_metrics_reject_impossible_counts_and_accept_latency() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="exceed"):
        Lot39MetricsV1(1, 2, 0, 0, 0, 1001)
    metrics = Lot39MetricsV1(2, 2, 1, 4, 0, 1003, processing_latency_us=1)
    assert metrics.processing_latency_us == 1


def test_engine_identity_and_checksum_paths() -> None:
    snapshot, deltas = _inputs()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="identity"):
        reconstruct_sequence(snapshot, (replace(deltas[0], instrument_id="ETH-EUR-SPOT"),))

    mismatch = replace(deltas[0], expected_book_checksum=ZERO)
    outcome = reconstruct_sequence(snapshot, (mismatch,))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.sequence_gap_event is not None
    assert "LOT39_BOOK_CHECKSUM_MISMATCH" in outcome.reason_codes


def test_delete_last_side_level_requires_resync() -> None:
    snapshot, _ = _inputs()
    deletes = tuple(OrderBookLevelV1(level.price, Decimal("0")) for level in snapshot.bids)
    delta = OrderBookDeltaV1(
        snapshot.source_id,
        snapshot.venue,
        snapshot.instrument_id,
        snapshot.market_type,
        "2026-08-06T19:18:40.055000Z",
        "2026-08-06T19:18:40.060000Z",
        1002,
        1001,
        deletes,
        (),
        None,
        False,
    )
    outcome = reconstruct_sequence(snapshot, (delta,))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert "LOT39_EMPTY_BOOK_AFTER_DELTA" in outcome.reason_codes
