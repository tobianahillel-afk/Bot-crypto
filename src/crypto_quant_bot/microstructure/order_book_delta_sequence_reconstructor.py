from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)

from .order_book_delta_sequence_reconstructor_models import (
    Lot39LineageEnvelopeV1,
    Lot39MetricsV1,
    Lot39RunContextV1,
    OrderBookDeltaSequenceReconstructorAuditV1,
    OrderBookDeltaSequenceReconstructorStateV1,
    OrderBookDeltaV1,
    ReconstructedOrderBookV1,
    SequenceGapEventV1,
)
from .order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
    decimal_from_text,
    duration_us,
    lot39_safety,
    parse_utc_timestamp,
    require_integer,
    require_text,
    validate_causal_times,
)
from .order_book_l2_snapshot_engine_models import OrderBookLevelV1, OrderBookSnapshotV1

CONFIG_PATH = Path("config/microstructure/order_book_delta_sequence_reconstructor_v1.json")
STATE_PATH = Path("data/audit/order_book_delta_sequence_reconstructor_lot39.json")
AUDIT_PATH = Path("data/audit/order_book_delta_sequence_reconstructor_audit_lot39.json")
BOOK_PATH = Path("data/audit/reconstructed_order_book_lot39.json")
GAP_EVENT_PATH = Path("data/audit/sequence_gap_event_lot39.json")
EXPECTED_GATE_CHECKSUM = "250c67574a8add382915c1b8f0b104f801bd91757c829c3d7d336f8e2e22e0ab"
EXPECTED_LOT38_STATE = "7610fc6ea73e49075a1b8611f8344c7b9c8fcf8ab02f55612d914eeac0ccda9b"
EXPECTED_LOT38_AUDIT = "0290637591e1a8c4cd7a9975868932b65afa28fb75d6843340dbeea67a682d20"
EXPECTED_LOT38_SNAPSHOT = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
EXPECTED_LOT38_HEALTH = "58b56f7cf21aa74dd67620b8dd6e19cad11b77412cdcc3103b6d60bd15703837"
ZERO_SHA256 = "0" * 64
COMMON_REASON_CODES = (
    "LOT39_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTED",
    "LOT39_SEQUENCE_CONTIGUOUS",
    "LOT39_ZERO_QUANTITY_DELETE_APPLIED",
    "LOT39_SYNCED_BOOK_PUBLISHED",
    "LOT40_REMAINS_LOCKED",
)


@dataclass(frozen=True)
class ReconstructionOutcome:
    synchronization_state: str
    reconstructed_book: ReconstructedOrderBookV1 | None
    sequence_gap_event: SequenceGapEventV1 | None
    metrics: Lot39MetricsV1
    reason_codes: tuple[str, ...]


def _validate_config(config: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version",
        "config_version",
        "run_id",
        "correlation_id",
        "lineage_id",
        "generated_at",
        "input_reference_time",
        "max_input_age_us",
        "entry_gate_path",
        "lot38_lifecycle_overlay_path",
        "lot38_state_path",
        "lot38_audit_path",
        "lot38_snapshot_path",
        "lot38_health_path",
        "delta_fixture_path",
    }
    if set(config) != expected_fields:
        raise OrderBookDeltaSequenceValidationError("Lot 39 config fields differ from contract")
    if config.get("schema_version") != "lot39-order-book-delta-sequence-config-v1":
        raise OrderBookDeltaSequenceValidationError("Lot 39 config schema changed")
    if config.get("config_version") != "lot39-order-book-delta-sequence-config-v1":
        raise OrderBookDeltaSequenceValidationError("Lot 39 config version changed")
    generated = require_text(config.get("generated_at"), "generated_at")
    reference = require_text(config.get("input_reference_time"), "input_reference_time")
    validate_causal_times(reference, reference, generated)
    require_integer(config.get("max_input_age_us"), "max_input_age_us", minimum=1)


def _verify_payload_checksum(
    payload: dict[str, Any], field: str, expected: str, label: str
) -> None:
    body = dict(payload)
    checksum = body.pop(field, None)
    if checksum != expected or canonical_checksum(body) != checksum:
        raise OrderBookDeltaSequenceValidationError(f"{label} checksum changed")


def _verify_gate(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    gate = load_json_object(path)
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    if checksum != EXPECTED_GATE_CHECKSUM or canonical_checksum(body) != checksum:
        raise OrderBookDeltaSequenceValidationError("Lot 39 entry gate checksum changed")
    expected = {
        "gate_status": "GO_LOT39_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT39",
        "target_lot": 39,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_started": False,
        "next_lot": 40,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise OrderBookDeltaSequenceValidationError("Lot 39 gate does not authorize this scope")
    if gate.get("safety") != lot39_safety():
        raise OrderBookDeltaSequenceValidationError("Lot 39 gate safety boundary changed")
    return gate


def _verify_lot38(root: Path, config: dict[str, Any]) -> OrderBookSnapshotV1:
    overlay = load_json_object(
        root / require_text(config.get("lot38_lifecycle_overlay_path"), "lifecycle overlay")
    )
    if overlay.get("latest_implemented_lot") != 38:
        raise OrderBookDeltaSequenceValidationError("Lot 39 requires audited lifecycle latest lot 38")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise OrderBookDeltaSequenceValidationError("Lot 38 lifecycle lot map missing")
    if lots.get("39") != {"implementation_started": False, "status": "PLANNED_LOCKED"}:
        raise OrderBookDeltaSequenceValidationError("Lot 39 historical pre-gate lock changed")
    lot38 = lots.get("38")
    if not isinstance(lot38, dict) or lot38.get("status") != (
        "IMPLEMENTED_VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY"
    ):
        raise OrderBookDeltaSequenceValidationError("Lot 38 lifecycle status changed")
    state = load_json_object(root / require_text(config.get("lot38_state_path"), "lot38 state"))
    audit = load_json_object(root / require_text(config.get("lot38_audit_path"), "lot38 audit"))
    snapshot_payload = load_json_object(
        root / require_text(config.get("lot38_snapshot_path"), "lot38 snapshot")
    )
    health = load_json_object(root / require_text(config.get("lot38_health_path"), "lot38 health"))
    _verify_payload_checksum(state, "output_checksum", EXPECTED_LOT38_STATE, "Lot 38 state")
    _verify_payload_checksum(audit, "audit_checksum", EXPECTED_LOT38_AUDIT, "Lot 38 audit")
    _verify_payload_checksum(
        snapshot_payload, "snapshot_checksum", EXPECTED_LOT38_SNAPSHOT, "Lot 38 snapshot"
    )
    _verify_payload_checksum(health, "health_checksum", EXPECTED_LOT38_HEALTH, "Lot 38 health")
    if health.get("health_status") != "HEALTHY" or health.get("sequence_present") is not True:
        raise OrderBookDeltaSequenceValidationError("Lot 39 requires healthy sequenced Lot 38 book")
    if health.get("crossed") is not False or health.get("locked") is not False:
        raise OrderBookDeltaSequenceValidationError("Lot 39 reference book must be open and uncrossed")
    return _snapshot_from_payload(snapshot_payload)


def _levels_from_payload(
    value: Any, side: str, *, allow_empty: bool
) -> tuple[OrderBookLevelV1, ...]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise OrderBookDeltaSequenceValidationError(f"{side} must be a valid level list")
    levels: list[OrderBookLevelV1] = []
    for raw in value:
        if not isinstance(raw, dict) or set(raw) != {"price", "quantity"}:
            raise OrderBookDeltaSequenceValidationError(f"invalid {side} level shape")
        price = decimal_from_text(raw["price"], f"{side} price", allow_zero=False)
        quantity = decimal_from_text(raw["quantity"], f"{side} quantity", allow_zero=True)
        levels.append(OrderBookLevelV1(price, quantity))
    if len({level.price for level in levels}) != len(levels):
        raise OrderBookDeltaSequenceValidationError(f"duplicate price in one {side} delta")
    return tuple(levels)


def _snapshot_from_payload(payload: dict[str, Any]) -> OrderBookSnapshotV1:
    return OrderBookSnapshotV1(
        source_id=require_text(payload.get("source_id"), "source_id"),
        venue=require_text(payload.get("venue"), "venue"),
        instrument_id=require_text(payload.get("instrument_id"), "instrument_id"),
        market_type=require_text(payload.get("market_type"), "market_type"),
        event_time=require_text(payload.get("event_time"), "event_time"),
        receive_time=require_text(payload.get("receive_time"), "receive_time"),
        sequence_id=require_integer(payload.get("sequence_id"), "sequence_id"),
        sequence_anchor=require_text(payload.get("sequence_anchor"), "sequence_anchor"),
        venue_state=require_text(payload.get("venue_state"), "venue_state"),
        bids=_levels_from_payload(payload.get("bids"), "snapshot bids", allow_empty=False),
        asks=_levels_from_payload(payload.get("asks"), "snapshot asks", allow_empty=False),
        source_bid_depth=require_integer(payload.get("source_bid_depth"), "source_bid_depth", 1),
        source_ask_depth=require_integer(payload.get("source_ask_depth"), "source_ask_depth", 1),
        normalized_bid_depth=require_integer(
            payload.get("normalized_bid_depth"), "normalized_bid_depth", 1
        ),
        normalized_ask_depth=require_integer(
            payload.get("normalized_ask_depth"), "normalized_ask_depth", 1
        ),
        published_bid_depth=require_integer(
            payload.get("published_bid_depth"), "published_bid_depth", 1
        ),
        published_ask_depth=require_integer(
            payload.get("published_ask_depth"), "published_ask_depth", 1
        ),
        snapshot_checksum=require_text(payload.get("snapshot_checksum"), "snapshot_checksum"),
    )


def _delta_from_payload(payload: Any) -> OrderBookDeltaV1:
    if not isinstance(payload, dict):
        raise OrderBookDeltaSequenceValidationError("delta record must be an object")
    expected_fields = {
        "schema_version",
        "source_id",
        "venue",
        "instrument_id",
        "market_type",
        "event_time",
        "receive_time",
        "sequence_id",
        "prev_sequence",
        "bids",
        "asks",
        "expected_book_checksum",
        "used_for_decision",
    }
    if set(payload) != expected_fields or payload.get("schema_version") != "order-book-delta-v1":
        raise OrderBookDeltaSequenceValidationError("OrderBookDeltaV1 shape changed")
    expected_checksum = payload.get("expected_book_checksum")
    if expected_checksum is not None:
        expected_checksum = require_text(expected_checksum, "expected_book_checksum")
    return OrderBookDeltaV1(
        source_id=require_text(payload.get("source_id"), "source_id"),
        venue=require_text(payload.get("venue"), "venue"),
        instrument_id=require_text(payload.get("instrument_id"), "instrument_id"),
        market_type=require_text(payload.get("market_type"), "market_type"),
        event_time=require_text(payload.get("event_time"), "event_time"),
        receive_time=require_text(payload.get("receive_time"), "receive_time"),
        sequence_id=require_integer(payload.get("sequence_id"), "sequence_id"),
        prev_sequence=require_integer(payload.get("prev_sequence"), "prev_sequence"),
        bids=_levels_from_payload(payload.get("bids"), "delta bids", allow_empty=True),
        asks=_levels_from_payload(payload.get("asks"), "delta asks", allow_empty=True),
        expected_book_checksum=expected_checksum,
        used_for_decision=payload.get("used_for_decision", True),
    )


def _load_deltas(
    root: Path, config: dict[str, Any]
) -> tuple[tuple[OrderBookDeltaV1, ...], str]:
    path = root / require_text(config.get("delta_fixture_path"), "delta_fixture_path")
    fixture_checksum = file_checksum(path)
    fixture = load_json_object(path)
    expected_fields = {
        "schema_version",
        "fixture_only",
        "canonical_contract_records",
        "used_for_decision",
        "description",
        "deltas",
    }
    if set(fixture) != expected_fields:
        raise OrderBookDeltaSequenceValidationError("Lot 39 fixture fields changed")
    if fixture.get("schema_version") != "lot39-order-book-delta-sequence-fixture-v1":
        raise OrderBookDeltaSequenceValidationError("Lot 39 fixture schema changed")
    if fixture.get("fixture_only") is not True or fixture.get("canonical_contract_records") is not True:
        raise OrderBookDeltaSequenceValidationError("Lot 39 fixture identity changed")
    if fixture.get("used_for_decision") is not False:
        raise OrderBookDeltaSequenceValidationError("Lot 39 fixture cannot be decision data")
    raw_deltas = fixture.get("deltas")
    if not isinstance(raw_deltas, list) or not raw_deltas:
        raise OrderBookDeltaSequenceValidationError("Lot 39 fixture requires deltas")
    deltas = tuple(_delta_from_payload(item) for item in raw_deltas)
    reference = parse_utc_timestamp(
        require_text(config.get("input_reference_time"), "input_reference_time"),
        "input_reference_time",
    )
    max_age = require_integer(config.get("max_input_age_us"), "max_input_age_us", minimum=1)
    for delta in deltas:
        received = parse_utc_timestamp(delta.receive_time, "delta receive_time")
        if received > reference or duration_us(received, reference) > max_age:
            raise OrderBookDeltaSequenceValidationError("Lot 39 delta is stale or future-dated")
    return deltas, fixture_checksum


def _validate_delta_identity(snapshot: OrderBookSnapshotV1, delta: OrderBookDeltaV1) -> None:
    expected = (snapshot.source_id, snapshot.venue, snapshot.instrument_id, snapshot.market_type)
    observed = (delta.source_id, delta.venue, delta.instrument_id, delta.market_type)
    if observed != expected:
        raise OrderBookDeltaSequenceValidationError("Lot 39 delta identity differs from snapshot")


def _sequence_anchor(snapshot: OrderBookSnapshotV1, sequence_id: int, event_time: str) -> str:
    return canonical_checksum(
        {
            "base_snapshot_checksum": snapshot.snapshot_checksum,
            "base_sequence_id": snapshot.sequence_id,
            "final_sequence_id": sequence_id,
            "event_time": event_time,
        }
    )


def _gap_event(
    current_sequence: int,
    delta: OrderBookDeltaV1,
    reason: str,
) -> SequenceGapEventV1:
    event = SequenceGapEventV1(
        True,
        "RESYNC_REQUIRED",
        current_sequence + 1,
        delta.sequence_id,
        delta.prev_sequence,
        delta.event_time,
        (reason, "LOT39_RESYNC_REQUIRED", "LOT40_REMAINS_LOCKED"),
        ZERO_SHA256,
    )
    return replace(event, event_checksum=canonical_checksum(event.payload_without_checksum()))


def _resync_outcome(
    current_sequence: int,
    delta: OrderBookDeltaV1,
    reason: str,
    *,
    received: int,
    applied: int,
    deleted: int,
    upserted: int,
) -> ReconstructionOutcome:
    event = _gap_event(current_sequence, delta, reason)
    return ReconstructionOutcome(
        "RESYNC_REQUIRED",
        None,
        event,
        Lot39MetricsV1(received, applied, deleted, upserted, 1, current_sequence),
        (reason, "LOT39_RESYNC_REQUIRED", "LOT40_REMAINS_LOCKED"),
    )


def _apply_changes(
    side: dict[Decimal, Decimal],
    changes: tuple[OrderBookLevelV1, ...],
) -> tuple[int, int, bool]:
    deleted = 0
    upserted = 0
    for level in changes:
        if level.quantity == 0:
            if level.price not in side:
                return deleted, upserted, False
            del side[level.price]
            deleted += 1
        else:
            side[level.price] = level.quantity
            upserted += 1
    return deleted, upserted, True


def reconstruct_sequence(
    snapshot: OrderBookSnapshotV1,
    deltas: tuple[OrderBookDeltaV1, ...],
) -> ReconstructionOutcome:
    if not deltas:
        raise OrderBookDeltaSequenceValidationError("Lot 39 requires at least one delta")
    bids = {level.price: level.quantity for level in snapshot.bids}
    asks = {level.price: level.quantity for level in snapshot.asks}
    current_sequence = snapshot.sequence_id
    deleted = 0
    upserted = 0
    applied = 0
    previous_event = parse_utc_timestamp(snapshot.event_time, "snapshot event_time")

    for index, delta in enumerate(deltas, start=1):
        _validate_delta_identity(snapshot, delta)
        event_time = parse_utc_timestamp(delta.event_time, "delta event_time")
        if event_time < previous_event:
            return _resync_outcome(
                current_sequence,
                delta,
                "LOT39_REORDERED_EVENT_TIME",
                received=len(deltas),
                applied=applied,
                deleted=deleted,
                upserted=upserted,
            )
        if delta.prev_sequence != current_sequence or delta.sequence_id != current_sequence + 1:
            reason = (
                "LOT39_DUPLICATE_OR_REORDERED_SEQUENCE"
                if delta.sequence_id <= current_sequence or delta.prev_sequence < current_sequence
                else "LOT39_SEQUENCE_GAP_DETECTED"
            )
            return _resync_outcome(
                current_sequence,
                delta,
                reason,
                received=len(deltas),
                applied=applied,
                deleted=deleted,
                upserted=upserted,
            )

        bid_deleted, bid_upserted, bids_ok = _apply_changes(bids, delta.bids)
        ask_deleted, ask_upserted, asks_ok = _apply_changes(asks, delta.asks)
        if not bids_ok or not asks_ok:
            return _resync_outcome(
                current_sequence,
                delta,
                "LOT39_DELETE_MISSING_LEVEL_RESYNC_REQUIRED",
                received=len(deltas),
                applied=applied,
                deleted=deleted,
                upserted=upserted,
            )
        deleted += bid_deleted + ask_deleted
        upserted += bid_upserted + ask_upserted
        if not bids or not asks:
            return _resync_outcome(
                current_sequence,
                delta,
                "LOT39_EMPTY_BOOK_AFTER_DELTA",
                received=len(deltas),
                applied=applied,
                deleted=deleted,
                upserted=upserted,
            )
        sorted_bids = tuple(
            OrderBookLevelV1(price, bids[price]) for price in sorted(bids, reverse=True)
        )
        sorted_asks = tuple(OrderBookLevelV1(price, asks[price]) for price in sorted(asks))
        if sorted_bids[0].price >= sorted_asks[0].price:
            return _resync_outcome(
                current_sequence,
                delta,
                "LOT39_CROSSED_OR_LOCKED_BOOK_AFTER_DELTA",
                received=len(deltas),
                applied=applied,
                deleted=deleted,
                upserted=upserted,
            )
        candidate = ReconstructedOrderBookV1(
            snapshot.source_id,
            snapshot.venue,
            snapshot.instrument_id,
            snapshot.market_type,
            delta.event_time,
            delta.receive_time,
            snapshot.snapshot_checksum,
            snapshot.sequence_id,
            delta.sequence_id,
            _sequence_anchor(snapshot, delta.sequence_id, delta.event_time),
            "SYNCED",
            sorted_bids,
            sorted_asks,
            index,
            ZERO_SHA256,
        )
        candidate = replace(
            candidate,
            book_checksum=canonical_checksum(candidate.payload_without_checksum()),
        )
        if (
            delta.expected_book_checksum is not None
            and delta.expected_book_checksum != candidate.book_checksum
        ):
            return _resync_outcome(
                current_sequence,
                delta,
                "LOT39_BOOK_CHECKSUM_MISMATCH",
                received=len(deltas),
                applied=applied,
                deleted=deleted,
                upserted=upserted,
            )
        current_sequence = delta.sequence_id
        previous_event = event_time
        applied += 1

    final_book = ReconstructedOrderBookV1(
        snapshot.source_id,
        snapshot.venue,
        snapshot.instrument_id,
        snapshot.market_type,
        deltas[-1].event_time,
        deltas[-1].receive_time,
        snapshot.snapshot_checksum,
        snapshot.sequence_id,
        current_sequence,
        _sequence_anchor(snapshot, current_sequence, deltas[-1].event_time),
        "SYNCED",
        tuple(OrderBookLevelV1(price, bids[price]) for price in sorted(bids, reverse=True)),
        tuple(OrderBookLevelV1(price, asks[price]) for price in sorted(asks)),
        applied,
        ZERO_SHA256,
    )
    final_book = replace(
        final_book,
        book_checksum=canonical_checksum(final_book.payload_without_checksum()),
    )
    return ReconstructionOutcome(
        "SYNCED",
        final_book,
        None,
        Lot39MetricsV1(len(deltas), applied, deleted, upserted, 0, current_sequence),
        COMMON_REASON_CODES,
    )


def build_lot39_artifacts(
    root: Path, code_commit: str
) -> tuple[OrderBookDeltaSequenceReconstructorStateV1, OrderBookDeltaSequenceReconstructorAuditV1]:
    config = load_json_object(root / CONFIG_PATH)
    _validate_config(config)
    _verify_gate(root, config)
    snapshot = _verify_lot38(root, config)
    deltas, fixture_checksum = _load_deltas(root, config)
    outcome = reconstruct_sequence(snapshot, deltas)
    generated_at = require_text(config.get("generated_at"), "generated_at")
    run_context = Lot39RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )
    if outcome.reconstructed_book is not None:
        event_time = outcome.reconstructed_book.event_time
        receive_time = outcome.reconstructed_book.receive_time
        available_at = receive_time
        validation_state = "VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY"
    else:
        if outcome.sequence_gap_event is None:
            raise OrderBookDeltaSequenceValidationError("resync outcome missing gap evidence")
        failed_index = min(outcome.metrics.deltas_applied_total, len(deltas) - 1)
        failed_delta = deltas[failed_index]
        event_time = outcome.sequence_gap_event.event_time
        receive_time = failed_delta.receive_time
        available_at = receive_time
        validation_state = "BLOCKED_RESYNC_REQUIRED"
    lineage = Lot39LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT38_STATE,
        EXPECTED_LOT38_AUDIT,
        EXPECTED_LOT38_SNAPSHOT,
        EXPECTED_LOT38_HEALTH,
        fixture_checksum,
        available_at,
    )
    state = OrderBookDeltaSequenceReconstructorStateV1(
        run_context,
        lineage,
        event_time,
        receive_time,
        generated_at,
        validation_state,
        outcome.synchronization_state,
        snapshot.snapshot_checksum,
        fixture_checksum,
        outcome.reconstructed_book,
        outcome.sequence_gap_event,
        outcome.metrics,
        outcome.reason_codes,
        lot39_safety(),
        ZERO_SHA256,
    )
    state = replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))
    audit = OrderBookDeltaSequenceReconstructorAuditV1(
        code_commit,
        file_checksum(root / CONFIG_PATH),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT38_STATE,
        EXPECTED_LOT38_SNAPSHOT,
        fixture_checksum,
        state.output_checksum,
        (
            outcome.reconstructed_book.book_checksum
            if outcome.reconstructed_book is not None
            else None
        ),
        (
            outcome.sequence_gap_event.event_checksum
            if outcome.sequence_gap_event is not None
            else None
        ),
        state.validation_state,
        state.synchronization_state,
        lot39_safety(),
        ZERO_SHA256,
    )
    audit = replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))
    return state, audit


def write_lot39_artifacts(
    root: Path, code_commit: str
) -> tuple[OrderBookDeltaSequenceReconstructorStateV1, OrderBookDeltaSequenceReconstructorAuditV1]:
    state, audit = build_lot39_artifacts(root, code_commit)
    atomic_write_json(root / STATE_PATH, state.to_dict())
    atomic_write_json(root / AUDIT_PATH, audit.to_dict())
    if state.reconstructed_book is not None:
        atomic_write_json(root / BOOK_PATH, state.reconstructed_book.to_dict())
        (root / GAP_EVENT_PATH).unlink(missing_ok=True)
    else:
        if state.sequence_gap_event is None:
            raise OrderBookDeltaSequenceValidationError("resync state missing gap event")
        atomic_write_json(root / GAP_EVENT_PATH, state.sequence_gap_event.to_dict())
        (root / BOOK_PATH).unlink(missing_ok=True)
    return state, audit
