from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor import (
    build_lot39_artifacts,
)
from crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor_models import (
    BLOCKED_STATE,
    Lot39MetricsV1,
    OrderBookDeltaSequenceReconstructorAuditV1,
    OrderBookDeltaSequenceReconstructorStateV1,
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

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "a" * 40
ZERO = "0" * 64


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: require_text("", "x"), "non-empty"),
        (lambda: require_integer(True, "x"), "integer"),
        (lambda: require_integer(-1, "x"), "integer"),
        (lambda: require_git_sha("BAD", "x"), "git SHA"),
        (lambda: require_sha256("BAD", "x"), "sha256"),
        (lambda: parse_utc_timestamp("2026-01-01", "x"), "UTC Z"),
        (lambda: parse_utc_timestamp("badZ", "x"), "ISO timestamp"),
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
def test_validation_rejects_invalid_contracts(call, message: str) -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match=message):
        call()


def test_time_contract_rejects_backwards_and_noncausal_order() -> None:
    late = parse_utc_timestamp("2026-01-02T00:00:00Z", "late")
    early = parse_utc_timestamp("2026-01-01T00:00:00Z", "early")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="backwards"):
        duration_us(late, early)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="causal"):
        validate_causal_times(
            "2026-01-02T00:00:00Z",
            "2026-01-01T00:00:00Z",
            "2026-01-03T00:00:00Z",
        )


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


def _blocked_pair() -> tuple[
    OrderBookDeltaSequenceReconstructorStateV1,
    OrderBookDeltaSequenceReconstructorAuditV1,
]:
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    event = SequenceGapEventV1(
        True,
        "RESYNC_REQUIRED",
        1004,
        1005,
        1004,
        "2026-08-06T19:18:40.075000Z",
        ("LOT39_SEQUENCE_GAP_DETECTED",),
        ZERO,
    )
    metrics = Lot39MetricsV1(2, 1, 0, 1, 1, 1003)
    blocked = OrderBookDeltaSequenceReconstructorStateV1(
        state.run_context,
        state.lineage,
        event.event_time,
        event.event_time,
        state.generated_at,
        BLOCKED_STATE,
        "RESYNC_REQUIRED",
        state.base_snapshot_checksum,
        state.delta_fixture_checksum,
        None,
        event,
        metrics,
        ("LOT39_SEQUENCE_GAP_DETECTED", "LOT40_REMAINS_LOCKED"),
        state.safety,
        ZERO,
    )
    blocked_audit = OrderBookDeltaSequenceReconstructorAuditV1(
        audit.code_commit,
        audit.config_checksum,
        audit.entry_gate_checksum,
        audit.lot38_state_checksum,
        audit.lot38_snapshot_checksum,
        audit.delta_fixture_checksum,
        ZERO,
        None,
        event.event_checksum,
        BLOCKED_STATE,
        "RESYNC_REQUIRED",
        audit.safety,
        ZERO,
    )
    return blocked, blocked_audit


def test_state_outcome_contracts_are_mutually_exclusive() -> None:
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state.reconstructed_book is not None
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="validated reconstructed book"):
        replace(state, validation_state=BLOCKED_STATE)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="gap event"):
        blocked, _ = _blocked_pair()
        replace(state, sequence_gap_event=blocked.sequence_gap_event)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="book checksum"):
        replace(audit, reconstructed_book_checksum=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="gap checksum"):
        replace(audit, sequence_gap_event_checksum=ZERO)


def test_blocked_state_requires_gap_and_forbids_book() -> None:
    blocked, audit = _blocked_pair()
    assert blocked.reconstructed_book is None
    assert blocked.sequence_gap_event is not None
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="blocked without book"):
        healthy, _ = build_lot39_artifacts(ROOT, CODE_COMMIT)
        replace(blocked, reconstructed_book=healthy.reconstructed_book)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="gap evidence"):
        replace(blocked, sequence_gap_event=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="without book checksum"):
        replace(audit, reconstructed_book_checksum=ZERO)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="requires gap checksum"):
        replace(audit, sequence_gap_event_checksum=None)
