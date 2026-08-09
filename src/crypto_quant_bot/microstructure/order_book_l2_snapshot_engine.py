from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)

from .order_book_l2_snapshot_engine_models import (
    BookHealthStateV1,
    Lot38LineageEnvelopeV1,
    Lot38MetricsV1,
    Lot38RunContextV1,
    OrderBookL2SnapshotEngineAuditV1,
    OrderBookL2SnapshotEngineStateV1,
    OrderBookLevelV1,
    OrderBookSnapshotRawV1,
    OrderBookSnapshotV1,
)
from .order_book_l2_snapshot_engine_validation import (
    OrderBookL2SnapshotValidationError,
    decimal_from_text,
    duration_us,
    lot38_safety,
    parse_utc_timestamp,
    require_integer,
    require_text,
    validate_causal_times,
    validate_venue_state,
)

CONFIG_PATH = Path("config/microstructure/order_book_l2_snapshot_engine_v1.json")
STATE_PATH = Path("data/audit/order_book_l2_snapshot_engine_lot38.json")
AUDIT_PATH = Path("data/audit/order_book_l2_snapshot_engine_audit_lot38.json")
SNAPSHOT_PATH = Path("data/audit/order_book_snapshot_lot38.json")
HEALTH_PATH = Path("data/audit/book_health_state_lot38.json")
EXPECTED_GATE_CHECKSUM = "29fe4a5fd14b3bce95e3016fce67e10f94edcca1c2aad60c9fda382f3eb9d6a0"
EXPECTED_LOT37_STATE = "ea960217eb9a2159c4a99c56257a37c43869ffad0da86555fef24eb356e5f8e7"
EXPECTED_LOT37_AUDIT = "aa2df489e636860c119eb2ed54f7a5f03ede09838dfbd056dae0bb5a8a2a482f"
EXPECTED_LOT37_REGISTRY = "129140ffb7e812afd59d0174d318c5e3388d23bc49cc554168bde558bc0bf590"
EXPECTED_LOT37_MATRIX = "f7132fcfdab898af3f733b2715e0836d23e6284f8c0c1f3e7dd92ccf0070f1b4"
ZERO_SHA256 = "0" * 64
COMMON_REASON_CODES = (
    "LOT38_OFFLINE_L2_SNAPSHOT_VALIDATED",
    "CANONICAL_LEVEL_ORDERING_APPLIED",
    "SOURCE_DEPTH_PRESERVED",
    "SEQUENCE_ANCHOR_BOUND",
    "LOT39_REMAINS_LOCKED",
)


def _validate_config(config: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version", "config_version", "run_id", "correlation_id", "lineage_id",
        "generated_at", "input_reference_time", "max_input_age_us", "published_depth_limit",
        "fixture_venue_state", "entry_gate_path", "lot37_lifecycle_overlay_path",
        "lot37_state_path", "lot37_audit_path", "lot37_contract_registry_path",
        "lot37_capability_matrix_path", "offline_l2_fixture_path",
    }
    if set(config) != expected_fields:
        raise OrderBookL2SnapshotValidationError("Lot 38 config fields differ from contract")
    if config.get("schema_version") != "lot38-order-book-l2-snapshot-config-v1":
        raise OrderBookL2SnapshotValidationError("Lot 38 config schema changed")
    if config.get("config_version") != "lot38-order-book-l2-snapshot-config-v1":
        raise OrderBookL2SnapshotValidationError("Lot 38 config version changed")
    generated = require_text(config.get("generated_at"), "generated_at")
    reference = require_text(config.get("input_reference_time"), "input_reference_time")
    validate_causal_times(reference, reference, generated)
    require_integer(config.get("max_input_age_us"), "max_input_age_us", minimum=1)
    require_integer(config.get("published_depth_limit"), "published_depth_limit", minimum=1)
    validate_venue_state(require_text(config.get("fixture_venue_state"), "fixture_venue_state"))


def _verify_gate(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    gate = load_json_object(path)
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    if checksum != EXPECTED_GATE_CHECKSUM or canonical_checksum(body) != checksum:
        raise OrderBookL2SnapshotValidationError("Lot 38 entry gate checksum changed")
    expected = {
        "gate_status": "GO_LOT38_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT38",
        "target_lot": 38,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_started": False,
        "next_lot": 39,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise OrderBookL2SnapshotValidationError("Lot 38 gate does not authorize this scope")
    if gate.get("safety") != lot38_safety():
        raise OrderBookL2SnapshotValidationError("Lot 38 gate safety boundary changed")
    return gate


def _verify_payload_checksum(
    payload: dict[str, Any],
    field: str,
    expected: str,
    label: str,
) -> None:
    body = dict(payload)
    checksum = body.pop(field, None)
    if checksum != expected or canonical_checksum(body) != checksum:
        raise OrderBookL2SnapshotValidationError(f"{label} checksum changed")


def _verify_lot37(root: Path, config: dict[str, Any]) -> None:
    overlay = load_json_object(
        root / require_text(config.get("lot37_lifecycle_overlay_path"), "lifecycle overlay")
    )
    if overlay.get("latest_implemented_lot") != 37:
        raise OrderBookL2SnapshotValidationError("Lot 38 requires audited lifecycle latest lot 37")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise OrderBookL2SnapshotValidationError("Lot 37 lifecycle lot map missing")
    if lots.get("38") != {"implementation_started": False, "status": "PLANNED_LOCKED"}:
        raise OrderBookL2SnapshotValidationError("Lot 38 historical pre-gate lock changed")
    lot37 = lots.get("37")
    if not isinstance(lot37, dict) or lot37.get("status") != (
        "IMPLEMENTED_VALIDATED_OFFLINE_SCOPE_CONTRACTS_ONLY"
    ):
        raise OrderBookL2SnapshotValidationError("Lot 37 lifecycle status changed")
    _verify_lot37_artifacts(root, config)


def _verify_lot37_artifacts(root: Path, config: dict[str, Any]) -> None:
    state = load_json_object(
        root / require_text(config.get("lot37_state_path"), "lot37_state_path")
    )
    audit = load_json_object(
        root / require_text(config.get("lot37_audit_path"), "lot37_audit_path")
    )
    registry = load_json_object(
        root / require_text(config.get("lot37_contract_registry_path"), "lot37 registry path")
    )
    matrix = load_json_object(
        root / require_text(config.get("lot37_capability_matrix_path"), "lot37 matrix path")
    )
    _verify_payload_checksum(state, "output_checksum", EXPECTED_LOT37_STATE, "Lot 37 state")
    _verify_payload_checksum(audit, "audit_checksum", EXPECTED_LOT37_AUDIT, "Lot 37 audit")
    if canonical_checksum(registry) != EXPECTED_LOT37_REGISTRY:
        raise OrderBookL2SnapshotValidationError("Lot 37 contract registry changed")
    if canonical_checksum(matrix) != EXPECTED_LOT37_MATRIX:
        raise OrderBookL2SnapshotValidationError("Lot 37 capability matrix changed")


def _load_raw_snapshot(
    root: Path,
    config: dict[str, Any],
    gate: dict[str, Any],
) -> tuple[OrderBookSnapshotRawV1, str]:
    path_text = require_text(config.get("offline_l2_fixture_path"), "offline_l2_fixture_path")
    prerequisites = gate.get("prerequisites")
    if not isinstance(prerequisites, dict) or prerequisites.get("offline_l2_fixture_path") != path_text:
        raise OrderBookL2SnapshotValidationError("Lot 38 fixture path differs from gate")
    path = root / path_text
    checksum = file_checksum(path)
    if checksum != prerequisites.get("offline_l2_fixture_sha256"):
        raise OrderBookL2SnapshotValidationError("Lot 38 fixture checksum differs from gate")
    fixture = load_json_object(path)
    _validate_fixture_identity(fixture)
    _validate_fixture_freshness(fixture, config)
    raw = _map_fixture_to_raw(fixture, config)
    return raw, checksum


def _validate_fixture_identity(fixture: dict[str, Any]) -> None:
    if fixture.get("fixture_only") is not True:
        raise OrderBookL2SnapshotValidationError("Lot 38 source must remain fixture-only")
    if fixture.get("canonical_contract") is not False:
        raise OrderBookL2SnapshotValidationError("Lot 37 fixture cannot become canonical")
    if fixture.get("used_for_decision") is not False:
        raise OrderBookL2SnapshotValidationError("Lot 38 fixture cannot become decision data")
    if fixture.get("schema_version") != "lot37-offline-l2-availability-fixture-v1":
        raise OrderBookL2SnapshotValidationError("Lot 38 fixture schema changed")


def _validate_fixture_freshness(fixture: dict[str, Any], config: dict[str, Any]) -> None:
    event = parse_utc_timestamp(require_text(fixture.get("event_time"), "event_time"), "event_time")
    received = parse_utc_timestamp(
        require_text(fixture.get("available_at"), "available_at"), "available_at"
    )
    reference = parse_utc_timestamp(
        require_text(config.get("input_reference_time"), "input_reference_time"),
        "input_reference_time",
    )
    if not event <= received <= reference:
        raise OrderBookL2SnapshotValidationError("Lot 38 fixture violates causal availability")
    max_age = require_integer(config.get("max_input_age_us"), "max_input_age_us", minimum=1)
    if duration_us(received, reference) > max_age:
        raise OrderBookL2SnapshotValidationError("Lot 38 fixture is stale")


def _levels(value: Any, side: str) -> tuple[OrderBookLevelV1, ...]:
    if not isinstance(value, list) or not value:
        raise OrderBookL2SnapshotValidationError(f"{side} must be a non-empty level list")
    levels: list[OrderBookLevelV1] = []
    for raw in value:
        if not isinstance(raw, dict) or set(raw) != {"price", "quantity"}:
            raise OrderBookL2SnapshotValidationError(f"invalid {side} level shape")
        levels.append(
            OrderBookLevelV1(
                decimal_from_text(raw["price"], f"{side} price", allow_zero=False),
                decimal_from_text(raw["quantity"], f"{side} quantity", allow_zero=True),
            )
        )
    return tuple(levels)


def _map_fixture_to_raw(
    fixture: dict[str, Any], config: dict[str, Any]
) -> OrderBookSnapshotRawV1:
    return OrderBookSnapshotRawV1(
        source_id=require_text(fixture.get("source_id"), "source_id"),
        venue=require_text(fixture.get("venue"), "venue"),
        instrument_id=require_text(fixture.get("instrument_id"), "instrument_id"),
        market_type=require_text(fixture.get("market_type"), "market_type"),
        event_time=require_text(fixture.get("event_time"), "event_time"),
        receive_time=require_text(fixture.get("available_at"), "available_at"),
        sequence_id=require_integer(fixture.get("sequence_id"), "sequence_id"),
        venue_state=require_text(config.get("fixture_venue_state"), "fixture_venue_state"),
        bids=_levels(fixture.get("bids"), "bids"),
        asks=_levels(fixture.get("asks"), "asks"),
        used_for_decision=False,
    )


def _aggregate_levels(
    levels: tuple[OrderBookLevelV1, ...], *, descending: bool
) -> tuple[OrderBookLevelV1, ...]:
    totals: dict[Decimal, Decimal] = {}
    for level in levels:
        totals[level.price] = totals.get(level.price, Decimal(0)) + level.quantity
    prices = sorted(totals, reverse=descending)
    return tuple(OrderBookLevelV1(price, totals[price]) for price in prices)


def _validate_full_book(
    bids: tuple[OrderBookLevelV1, ...],
    asks: tuple[OrderBookLevelV1, ...],
    venue_state: str,
) -> None:
    best_bid = bids[0].price
    best_ask = asks[0].price
    if best_bid > best_ask:
        raise OrderBookL2SnapshotValidationError("crossed book is forbidden")
    locked = best_bid == best_ask
    if locked != (venue_state == "LOCKED"):
        raise OrderBookL2SnapshotValidationError(
            "locked book requires explicit and exact LOCKED venue state"
        )


def _sequence_anchor(raw: OrderBookSnapshotRawV1) -> str:
    return canonical_checksum(
        {
            "source_id": raw.source_id,
            "venue": raw.venue,
            "instrument_id": raw.instrument_id,
            "sequence_id": raw.sequence_id,
            "event_time": raw.event_time,
            "receive_time": raw.receive_time,
        }
    )


def _build_snapshot(
    raw: OrderBookSnapshotRawV1, depth_limit: int
) -> OrderBookSnapshotV1:
    bids = _aggregate_levels(raw.bids, descending=True)
    asks = _aggregate_levels(raw.asks, descending=False)
    _validate_full_book(bids, asks, raw.venue_state)
    published_bids = bids[:depth_limit]
    published_asks = asks[:depth_limit]
    snapshot = OrderBookSnapshotV1(
        raw.source_id, raw.venue, raw.instrument_id, raw.market_type,
        raw.event_time, raw.receive_time, raw.sequence_id, _sequence_anchor(raw),
        raw.venue_state, published_bids, published_asks, len(raw.bids), len(raw.asks),
        len(bids), len(asks), len(published_bids), len(published_asks), ZERO_SHA256,
    )
    return replace(snapshot, snapshot_checksum=canonical_checksum(snapshot.payload_without_checksum()))


def _build_health(snapshot: OrderBookSnapshotV1) -> BookHealthStateV1:
    locked = snapshot.venue_state == "LOCKED"
    reasons = (
        "LOT38_BOOK_LOCKED_EXPLICIT" if locked else "LOT38_BOOK_OPEN_HEALTHY",
        "LOT38_SEQUENCE_PRESENT",
        "LOT39_REMAINS_LOCKED",
    )
    health = BookHealthStateV1(
        "LOCKED" if locked else "HEALTHY", snapshot.venue_state, False, locked, True,
        snapshot.source_bid_depth, snapshot.source_ask_depth, snapshot.normalized_bid_depth,
        snapshot.normalized_ask_depth, snapshot.published_bid_depth,
        snapshot.published_ask_depth, reasons, ZERO_SHA256,
    )
    return replace(health, health_checksum=canonical_checksum(health.payload_without_checksum()))


def _build_metrics(raw: OrderBookSnapshotRawV1, snapshot: OrderBookSnapshotV1) -> Lot38MetricsV1:
    source_total = len(raw.bids) + len(raw.asks)
    normalized_total = snapshot.normalized_bid_depth + snapshot.normalized_ask_depth
    published_total = snapshot.published_bid_depth + snapshot.published_ask_depth
    return Lot38MetricsV1(
        source_total,
        normalized_total,
        source_total - normalized_total,
        published_total,
    )


def _build_lineage(
    config: dict[str, Any], input_checksum: str, receive_time: str
) -> Lot38LineageEnvelopeV1:
    return Lot38LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT37_STATE,
        EXPECTED_LOT37_AUDIT,
        EXPECTED_LOT37_REGISTRY,
        EXPECTED_LOT37_MATRIX,
        input_checksum,
        receive_time,
    )


def build_lot38_artifacts(
    root: Path, code_commit: str
) -> tuple[OrderBookL2SnapshotEngineStateV1, OrderBookL2SnapshotEngineAuditV1]:
    config_path = root / CONFIG_PATH
    config = load_json_object(config_path)
    _validate_config(config)
    gate = _verify_gate(root, config)
    _verify_lot37(root, config)
    raw, input_checksum = _load_raw_snapshot(root, config, gate)
    depth_limit = require_integer(config.get("published_depth_limit"), "depth", minimum=1)
    snapshot = _build_snapshot(raw, depth_limit)
    health = _build_health(snapshot)
    state = _build_state(config, code_commit, input_checksum, snapshot, health, raw)
    audit = _build_audit(config_path, code_commit, input_checksum, state)
    return state, audit


def _build_state(
    config: dict[str, Any],
    code_commit: str,
    input_checksum: str,
    snapshot: OrderBookSnapshotV1,
    health: BookHealthStateV1,
    raw: OrderBookSnapshotRawV1,
) -> OrderBookL2SnapshotEngineStateV1:
    context = Lot38RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )
    state = OrderBookL2SnapshotEngineStateV1(
        context, _build_lineage(config, input_checksum, raw.receive_time), raw.event_time,
        raw.receive_time, require_text(config.get("generated_at"), "generated_at"),
        "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY", input_checksum, snapshot, health,
        _build_metrics(raw, snapshot), COMMON_REASON_CODES, lot38_safety(), ZERO_SHA256,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    config_path: Path,
    code_commit: str,
    input_checksum: str,
    state: OrderBookL2SnapshotEngineStateV1,
) -> OrderBookL2SnapshotEngineAuditV1:
    audit = OrderBookL2SnapshotEngineAuditV1(
        code_commit, state.output_checksum, file_checksum(config_path), EXPECTED_GATE_CHECKSUM,
        input_checksum, state.snapshot.snapshot_checksum, state.book_health.health_checksum,
        state.validation_state, lot38_safety(), ZERO_SHA256,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def write_lot38_artifacts(
    root: Path, code_commit: str
) -> tuple[OrderBookL2SnapshotEngineStateV1, OrderBookL2SnapshotEngineAuditV1]:
    state, audit = build_lot38_artifacts(root, code_commit)
    for path, payload in (
        (STATE_PATH, state.to_dict()),
        (AUDIT_PATH, audit.to_dict()),
        (SNAPSHOT_PATH, state.snapshot.to_dict()),
        (HEALTH_PATH, state.book_health.to_dict()),
    ):
        atomic_write_json(root / path, payload)
    return state, audit
