from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor import (
    build_lot39_artifacts,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_models import (
    BLOCKED_STATE,
    SUCCESS_STATE,
    Lot39LineageEnvelopeV1,
    Lot39MetricsV1,
    Lot39RunContextV1,
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
    validate_run_context,
    validate_runtime_mode,
    validate_sync_state,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "e" * 40
ZERO = "0" * 64


def _valid_state_and_audit() -> tuple[
    OrderBookDeltaSequenceReconstructorStateV1,
    OrderBookDeltaSequenceReconstructorAuditV1,
]:
    return build_lot39_artifacts(ROOT, CODE_COMMIT)


def _valid_book() -> ReconstructedOrderBookV1:
    state, _ = _valid_state_and_audit()
    assert state.reconstructed_book is not None
    return state.reconstructed_book


def _valid_gap() -> SequenceGapEventV1:
    event = SequenceGapEventV1(
        True,
        "RESYNC_REQUIRED",
        1002,
        1004,
        1003,
        "2026-08-06T19:18:40.060000Z",
        ("LOT39_SEQUENCE_GAP_DETECTED",),
        ZERO,
    )
    from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
        canonical_checksum,
    )

    return replace(event, event_checksum=canonical_checksum(event.payload_without_checksum()))


@pytest.mark.parametrize("value", [None, "", "   ", 7])
def test_require_text_rejects_non_text_or_blank(value: object) -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="non-empty text"):
        require_text(value, "field")


@pytest.mark.parametrize("value", [True, "1", -1])
def test_require_integer_rejects_non_integer_or_below_minimum(value: object) -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="integer"):
        require_integer(value, "field")


def test_hash_validators_reject_malformed_values() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="git SHA"):
        require_git_sha("A" * 40, "sha")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        require_sha256("g" * 64, "digest")


def test_timestamp_and_duration_validation_fail_closed() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="UTC Z"):
        parse_utc_timestamp("2026-08-06T19:18:40+00:00", "time")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="ISO timestamp"):
        parse_utc_timestamp("not-a-dateZ", "time")
    now = datetime(2026, 8, 6, tzinfo=UTC)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="backwards"):
        duration_us(now, now - timedelta(microseconds=1))
    assert duration_us(now, now + timedelta(days=1, seconds=2, microseconds=3)) == 86_402_000_003
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="causal"):
        validate_causal_times(
            "2026-08-06T19:18:40.100000Z",
            "2026-08-06T19:18:40.050000Z",
            "2026-08-06T19:18:40.200000Z",
        )


def test_decimal_validation_covers_all_rejection_classes() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="decimal text"):
        decimal_from_text(1, "price", allow_zero=False)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="invalid decimal"):
        decimal_from_text("not-decimal", "price", allow_zero=False)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="finite"):
        decimal_from_text("NaN", "price", allow_zero=False)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="positive"):
        decimal_from_text("0", "price", allow_zero=False)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="non-negative"):
        decimal_from_text("-1", "quantity", allow_zero=True)
    assert decimal_from_text("0", "quantity", allow_zero=True) == Decimal("0")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="finite"):
        decimal_text(Decimal("Infinity"))
    assert decimal_text(Decimal("1.2300")) == "1.23"


def test_reason_runtime_sync_and_safety_validation() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="requires reason codes"):
        validate_reason_codes(())
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="unique"):
        validate_reason_codes(("A", "A"))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="invalid reason code"):
        validate_reason_codes(("bad-code",))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="runtime"):
        validate_runtime_mode("LIVE")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="synchronization"):
        validate_sync_state("UNKNOWN")
    unsafe = lot39_safety()
    unsafe["trade_allowed"] = True
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="safety"):
        validate_lot39_safety(unsafe)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="run_id"):
        validate_run_context("", "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY", "v1", "e" * 40, "c")


def test_run_context_and_lineage_models_validate_their_contracts() -> None:
    context = Lot39RunContextV1(
        "run",
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "v1",
        "e" * 40,
        "correlation",
    )
    assert context.to_dict()["schema_version"] == "lot39-run-context-v1"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="runtime"):
        replace(context, runtime_mode="LIVE")

    state, _ = _valid_state_and_audit()
    lineage = state.lineage
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(lineage, lot38_state_checksum="x")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="UTC Z"):
        replace(lineage, available_at="2026-08-06T19:18:40")
    assert Lot39LineageEnvelopeV1(**{
        "lineage_id": lineage.lineage_id,
        "entry_gate_checksum": lineage.entry_gate_checksum,
        "lot38_state_checksum": lineage.lot38_state_checksum,
        "lot38_audit_checksum": lineage.lot38_audit_checksum,
        "lot38_snapshot_checksum": lineage.lot38_snapshot_checksum,
        "lot38_health_checksum": lineage.lot38_health_checksum,
        "delta_fixture_checksum": lineage.delta_fixture_checksum,
        "available_at": lineage.available_at,
    }).to_dict() == lineage.to_dict()


def test_delta_model_rejects_invalid_identity_shape_and_permissions() -> None:
    state, _ = _valid_state_and_audit()
    assert state.reconstructed_book is not None
    level = state.reconstructed_book.bids[0]
    delta = OrderBookDeltaV1(
        state.reconstructed_book.source_id,
        state.reconstructed_book.venue,
        state.reconstructed_book.instrument_id,
        "SPOT",
        state.event_time,
        state.receive_time,
        1004,
        1003,
        (level,),
        (),
        None,
        False,
    )
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="SPOT"):
        replace(delta, market_type="PERP")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="change at least one side"):
        replace(delta, bids=(), asks=())
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(delta, expected_book_checksum="x")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="decision data"):
        replace(delta, used_for_decision=True)


def test_reconstructed_book_rejects_invalid_identity_sequence_and_levels() -> None:
    book = _valid_book()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="SPOT"):
        replace(book, market_type="PERP")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="advance"):
        replace(book, sequence_id=book.base_sequence_id)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="only SYNCED"):
        replace(book, synchronization_state="RESYNC_REQUIRED")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="non-empty"):
        replace(book, bids=())
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="descending"):
        replace(book, bids=tuple(reversed(book.bids)))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="ascending"):
        replace(book, asks=tuple(reversed(book.asks)))
    crossed_bid = OrderBookLevelV1(book.asks[0].price, Decimal("1"))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="crossed or locked"):
        replace(book, bids=(crossed_bid,))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="applied_delta_count"):
        replace(book, applied_delta_count=0)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(book, book_checksum="x")


def test_gap_event_rejects_inconsistent_evidence() -> None:
    gap = _valid_gap()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="boolean"):
        replace(gap, gap_detected=1)  # type: ignore[arg-type]
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="synchronization"):
        replace(gap, synchronization_state="UNKNOWN")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="resync and observed"):
        replace(gap, synchronization_state="SYNCED")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="resync and observed"):
        replace(gap, observed_sequence=None)
    no_gap = replace(
        gap,
        gap_detected=False,
        synchronization_state="SYNCED",
        observed_sequence=None,
        observed_prev_sequence=None,
    )
    assert no_gap.gap_detected is False
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="no-gap"):
        replace(no_gap, observed_sequence=1002)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(gap, event_checksum="x")


def test_metrics_reject_inconsistent_counts_and_metadata() -> None:
    metrics = Lot39MetricsV1(2, 2, 1, 4, 0, 1003)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="integer"):
        replace(metrics, deltas_received_total=-1)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="exceed"):
        replace(metrics, deltas_applied_total=3)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="processing_latency_us"):
        replace(metrics, processing_latency_us=-1)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="non-empty"):
        replace(metrics, latency_measurement_status="")


def test_state_outcome_contract_rejects_mixed_publication_states() -> None:
    state, _ = _valid_state_and_audit()
    gap = _valid_gap()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="validated reconstructed book"):
        replace(state, validation_state=BLOCKED_STATE)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="gap event"):
        replace(state, sequence_gap_event=gap)
    assert state.reconstructed_book is not None
    blocked = replace(
        state,
        validation_state=BLOCKED_STATE,
        synchronization_state="RESYNC_REQUIRED",
        reconstructed_book=None,
        sequence_gap_event=gap,
        metrics=replace(state.metrics, sequence_gap_events_total=1),
        reason_codes=("LOT39_RESYNC_REQUIRED",),
    )
    assert blocked.reconstructed_book is None
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="blocked without book"):
        replace(blocked, reconstructed_book=state.reconstructed_book)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="gap evidence"):
        replace(blocked, sequence_gap_event=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(state, output_checksum="x")
    unsafe = dict(state.safety)
    unsafe["execution_allowed"] = True
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="safety"):
        replace(state, safety=unsafe)


def test_audit_outcome_contract_rejects_mixed_checksums() -> None:
    _, audit = _valid_state_and_audit()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="validated book checksum"):
        replace(audit, reconstructed_book_checksum=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="gap checksum"):
        replace(audit, sequence_gap_event_checksum=ZERO)
    blocked = replace(
        audit,
        validation_state=BLOCKED_STATE,
        synchronization_state="RESYNC_REQUIRED",
        reconstructed_book_checksum=None,
        sequence_gap_event_checksum=ZERO,
    )
    assert blocked.synchronization_state == "RESYNC_REQUIRED"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="blocked without book checksum"):
        replace(blocked, reconstructed_book_checksum=ZERO)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="requires gap checksum"):
        replace(blocked, sequence_gap_event_checksum=None)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="sha256"):
        replace(audit, audit_checksum="x")
