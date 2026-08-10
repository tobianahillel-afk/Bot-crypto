from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor import (
    build_lot39_artifacts,
    reconstruct_sequence,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_models import (
    OrderBookDeltaV1,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
    lot39_safety,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "f" * 40


def _reference():
    config = json.loads((ROOT / engine.CONFIG_PATH).read_text(encoding="utf-8"))
    snapshot = engine._verify_lot38(ROOT, config)
    deltas, fixture_checksum = engine._load_deltas(ROOT, config)
    return config, snapshot, deltas, fixture_checksum


def test_reference_exact_checksums_recompute() -> None:
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    state_body = state.to_dict()
    state_checksum = state_body.pop("output_checksum")
    assert canonical_checksum(state_body) == state_checksum
    audit_body = audit.to_dict()
    audit_checksum = audit_body.pop("audit_checksum")
    assert canonical_checksum(audit_body) == audit_checksum
    assert state.reconstructed_book is not None
    book_body = state.reconstructed_book.to_dict()
    book_checksum = book_body.pop("book_checksum")
    assert canonical_checksum(book_body) == book_checksum


def test_reference_exact_counts_and_final_levels() -> None:
    state, _ = build_lot39_artifacts(ROOT, CODE_COMMIT)
    book = state.reconstructed_book
    assert book is not None
    assert book.base_sequence_id == 1001
    assert book.sequence_id == 1003
    assert book.applied_delta_count == 2
    assert [(str(x.price), str(x.quantity)) for x in book.bids] == [
        ("50024.9", "0.9"),
        ("50024.7", "0.5"),
    ]
    assert [(str(x.price), str(x.quantity)) for x in book.asks] == [
        ("50025.1", "0.65"),
        ("50025.2", "1.1"),
        ("50025.3", "0.4"),
    ]
    assert state.metrics.deltas_received_total == 2
    assert state.metrics.deltas_applied_total == 2
    assert state.metrics.levels_deleted_total == 1
    assert state.metrics.levels_upserted_total == 4
    assert state.metrics.sequence_gap_events_total == 0
    assert state.metrics.final_sequence_id == 1003


@pytest.mark.parametrize(
    ("sequence_id", "prev_sequence", "reason"),
    [
        (1002, 1000, "LOT39_DUPLICATE_OR_REORDERED_SEQUENCE"),
        (1001, 1001, "LOT39_DUPLICATE_OR_REORDERED_SEQUENCE"),
        (1003, 1001, "LOT39_SEQUENCE_GAP_DETECTED"),
        (1003, 1002, "LOT39_SEQUENCE_GAP_DETECTED"),
    ],
)
def test_sequence_policy_exact_boundaries(sequence_id: int, prev_sequence: int, reason: str) -> None:
    _, snapshot, deltas, _ = _reference()
    delta = replace(deltas[0], sequence_id=sequence_id, prev_sequence=prev_sequence)
    outcome = reconstruct_sequence(snapshot, (delta,))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert outcome.sequence_gap_event is not None
    assert reason in outcome.reason_codes
    assert outcome.metrics.deltas_applied_total == 0
    assert outcome.metrics.final_sequence_id == 1001


def test_event_time_equal_is_allowed_but_earlier_is_blocked() -> None:
    _, snapshot, deltas, _ = _reference()
    equal = replace(deltas[0], event_time=snapshot.event_time, receive_time=deltas[0].receive_time)
    okay = reconstruct_sequence(snapshot, (equal,))
    assert okay.synchronization_state == "SYNCED"

    earlier = replace(
        deltas[0],
        event_time="2026-08-06T19:18:40.049999Z",
        receive_time=deltas[0].receive_time,
    )
    blocked = reconstruct_sequence(snapshot, (earlier,))
    assert blocked.synchronization_state == "RESYNC_REQUIRED"
    assert "LOT39_REORDERED_EVENT_TIME" in blocked.reason_codes


def test_zero_quantity_delete_requires_existing_price() -> None:
    _, snapshot, deltas, _ = _reference()
    delete_existing = replace(
        deltas[0],
        bids=(OrderBookLevelV1(Decimal("50024.8"), Decimal("0")),),
        asks=(),
    )
    okay = reconstruct_sequence(snapshot, (delete_existing,))
    assert okay.synchronization_state == "SYNCED"
    assert okay.reconstructed_book is not None
    assert all(level.price != Decimal("50024.8") for level in okay.reconstructed_book.bids)
    assert okay.metrics.levels_deleted_total == 1
    assert okay.metrics.levels_upserted_total == 0

    delete_missing = replace(
        deltas[0],
        bids=(OrderBookLevelV1(Decimal("49900"), Decimal("0")),),
        asks=(),
    )
    blocked = reconstruct_sequence(snapshot, (delete_missing,))
    assert blocked.synchronization_state == "RESYNC_REQUIRED"
    assert "LOT39_DELETE_MISSING_LEVEL_RESYNC_REQUIRED" in blocked.reason_codes


def test_positive_quantity_is_absolute_upsert_not_additive() -> None:
    _, snapshot, deltas, _ = _reference()
    delta = replace(
        deltas[0],
        bids=(OrderBookLevelV1(Decimal("50024.9"), Decimal("1.0")),),
        asks=(),
    )
    outcome = reconstruct_sequence(snapshot, (delta,))
    assert outcome.reconstructed_book is not None
    quantity = next(
        level.quantity for level in outcome.reconstructed_book.bids if level.price == Decimal("50024.9")
    )
    assert quantity == Decimal("1.0")
    assert quantity != Decimal("1.8")


def test_cross_and_lock_are_both_fail_closed() -> None:
    _, snapshot, deltas, _ = _reference()
    for price in (Decimal("50025.1"), Decimal("50025.2")):
        delta = replace(
            deltas[0],
            bids=(OrderBookLevelV1(price, Decimal("1")),),
            asks=(),
        )
        outcome = reconstruct_sequence(snapshot, (delta,))
        assert outcome.synchronization_state == "RESYNC_REQUIRED"
        assert outcome.reconstructed_book is None
        assert "LOT39_CROSSED_OR_LOCKED_BOOK_AFTER_DELTA" in outcome.reason_codes


def test_expected_checksum_exact_match_is_accepted() -> None:
    _, snapshot, deltas, _ = _reference()
    first = reconstruct_sequence(snapshot, (deltas[0],))
    assert first.reconstructed_book is not None
    exact = replace(deltas[0], expected_book_checksum=first.reconstructed_book.book_checksum)
    replay = reconstruct_sequence(snapshot, (exact,))
    assert replay.synchronization_state == "SYNCED"
    assert replay.reconstructed_book is not None
    assert replay.reconstructed_book.book_checksum == first.reconstructed_book.book_checksum


def test_safety_is_exact_and_never_permissive() -> None:
    safety = lot39_safety()
    assert safety == {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "participant_behavior_inference_explicitly_labeled": True,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "scenario_score_is_signal": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }


def test_contract_rejects_negative_quantity_before_engine() -> None:
    with pytest.raises(Exception, match="quantity"):
        OrderBookLevelV1(Decimal("50000"), Decimal("-0.0001"))


def test_delta_contract_requires_at_least_one_side() -> None:
    _, _, deltas, _ = _reference()
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="at least one side"):
        OrderBookDeltaV1(
            deltas[0].source_id,
            deltas[0].venue,
            deltas[0].instrument_id,
            deltas[0].market_type,
            deltas[0].event_time,
            deltas[0].receive_time,
            deltas[0].sequence_id,
            deltas[0].prev_sequence,
            (),
            (),
            None,
            False,
        )
