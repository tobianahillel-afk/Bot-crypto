from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)

from .book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
    analyze_book_resilience,
)
from .book_resilience_and_replenishment_engine_models import (
    BookResilienceReplenishmentEngineAuditV1,
    BookResilienceReplenishmentEngineStateV1,
    BookResilienceStateV1,
    Lot43LineageEnvelopeV1,
    Lot43MetricsV1,
    Lot43RunContextV1,
)
from .book_resilience_and_replenishment_engine_validation import (
    REGIME_METHOD,
    Lot43ValidationError,
    age_us,
    lot43_safety,
    nonnegative_decimal_text,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_horizons,
    validate_ratio,
)
from .liquidity_zones_walls_and_voids_analysis import reconstruct_observation_history
from .order_book_delta_and_sequence_reconstructor import reconstruct_sequence
from .order_book_delta_and_sequence_reconstructor_models import OrderBookDeltaV1
from .order_book_l2_snapshot_engine_models import OrderBookLevelV1, OrderBookSnapshotV1

CONFIG_PATH = Path("config/microstructure/book_resilience_and_replenishment_engine_v1.json")
STATE_PATH = Path("data/audit/book_resilience_and_replenishment_engine_lot43.json")
AUDIT_PATH = Path("data/audit/book_resilience_and_replenishment_engine_audit_lot43.json")
RESILIENCE_PATH = Path("data/audit/book_resilience_state_lot43.json")
EXPECTED_GATE = "4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d"
EXPECTED_GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
EXPECTED_LOT42_STATE = "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0"
EXPECTED_LOT42_AUDIT = "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f"
EXPECTED_LOT42_ZONE_SET = "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89"
EXPECTED_LOT42_CONFIG = "81acdd9e6d0a7d3ead9d4d483f71485082f591be8efd8480d70f4525113c47b6"
EXPECTED_LOT38_STATE = "7610fc6ea73e49075a1b8611f8344c7b9c8fcf8ab02f55612d914eeac0ccda9b"
EXPECTED_LOT38_SNAPSHOT = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_DELTA_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"
ZERO_SHA256 = "0" * 64


def _verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    if actual != expected or canonical_checksum(body) != actual:
        raise Lot43ValidationError(f"{label} checksum changed")


def _config_fields() -> set[str]:
    return {
        "schema_version",
        "config_version",
        "run_id",
        "correlation_id",
        "lineage_id",
        "generated_at",
        "decision_time",
        "calculation_decimal_precision",
        "depletion_min_quantity",
        "depletion_min_ratio",
        "replenishment_min_recovery_ratio",
        "adjacent_replenishment_distance_bps",
        "mid_shift_min_bps",
        "resilience_horizons_us",
        "quiet_max_mid_move_bps",
        "stressed_min_mid_move_bps",
        "max_input_age_us",
        "entry_gate_path",
        "lot42_lifecycle_overlay_path",
        "lot42_state_path",
        "lot42_audit_path",
        "lot42_zone_set_path",
        "lot42_config_path",
        "lot38_state_path",
        "lot39_reconstructed_book_path",
        "lot39_delta_fixture_path",
    }


def _validate_config(config: dict[str, Any]) -> BookResiliencePolicy:
    if set(config) != _config_fields():
        raise Lot43ValidationError("Lot 43 config fields differ from contract")
    version = "lot43-book-resilience-replenishment-config-v1"
    if config.get("schema_version") != version or config.get("config_version") != version:
        raise Lot43ValidationError("Lot 43 config version changed")
    precision = require_integer(config.get("calculation_decimal_precision"), "decimal precision", 1)
    raw_horizons = config.get("resilience_horizons_us")
    if not isinstance(raw_horizons, list):
        raise Lot43ValidationError("resilience_horizons_us must be a list")
    horizons = tuple(require_integer(item, "resilience horizon", 1) for item in raw_horizons)
    validate_horizons(horizons)
    policy = BookResiliencePolicy(
        precision,
        nonnegative_decimal_text(config.get("depletion_min_quantity"), "depletion_min_quantity"),
        nonnegative_decimal_text(config.get("depletion_min_ratio"), "depletion_min_ratio"),
        nonnegative_decimal_text(
            config.get("replenishment_min_recovery_ratio"),
            "replenishment_min_recovery_ratio",
        ),
        nonnegative_decimal_text(
            config.get("adjacent_replenishment_distance_bps"),
            "adjacent_replenishment_distance_bps",
        ),
        nonnegative_decimal_text(config.get("mid_shift_min_bps"), "mid_shift_min_bps"),
        horizons,
        nonnegative_decimal_text(config.get("quiet_max_mid_move_bps"), "quiet_max_mid_move_bps"),
        nonnegative_decimal_text(config.get("stressed_min_mid_move_bps"), "stressed_min_mid_move_bps"),
    )
    validate_ratio(policy.depletion_min_ratio, "depletion_min_ratio")
    validate_ratio(policy.replenishment_min_recovery_ratio, "replenishment_min_recovery_ratio")
    if policy.depletion_min_quantity <= 0:
        raise Lot43ValidationError("depletion_min_quantity must be positive")
    if policy.replenishment_min_recovery_ratio <= 0:
        raise Lot43ValidationError("replenishment recovery threshold must be positive")
    return policy


def _verify_gate(root: Path, config: dict[str, Any]) -> None:
    gate = load_json_object(root / require_text(config.get("entry_gate_path"), "entry_gate_path"))
    _verify_checksum(gate, "output_checksum", EXPECTED_GATE, "Lot 43 entry gate")
    expected = {
        "target_lot": 43,
        "base_commit": "2438622734e597cdcbada6b926e3c05d9e4cf8bc",
        "current_version": "0.42.0",
        "gate_status": "GO_LOT43_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT43",
        "implementation_started": False,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "next_lot": 44,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise Lot43ValidationError("Lot 43 entry gate authorization changed")
    if gate.get("safety") != lot43_safety():
        raise Lot43ValidationError("Lot 43 entry gate safety changed")


def _verify_lifecycle(root: Path, config: dict[str, Any]) -> None:
    path = root / require_text(config.get("lot42_lifecycle_overlay_path"), "lifecycle path")
    overlay = load_json_object(path)
    if overlay.get("latest_implemented_lot") != 42:
        raise Lot43ValidationError("Lot 43 requires audited lifecycle latest lot 42")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise Lot43ValidationError("Lot 42 lifecycle lots missing")
    expected42 = "IMPLEMENTED_VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY"
    if not isinstance(lots.get("42"), dict) or lots["42"].get("status") != expected42:
        raise Lot43ValidationError("Lot 42 lifecycle status changed")
    if lots.get("43") != {"implementation_started": False, "status": "PLANNED_LOCKED"}:
        raise Lot43ValidationError("historical Lot 43 gate lifecycle changed")


def _verify_lot42(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    state = load_json_object(root / require_text(config.get("lot42_state_path"), "lot42_state_path"))
    audit = load_json_object(root / require_text(config.get("lot42_audit_path"), "lot42_audit_path"))
    zone_set = load_json_object(
        root / require_text(config.get("lot42_zone_set_path"), "lot42_zone_set_path")
    )
    _verify_checksum(state, "output_checksum", EXPECTED_LOT42_STATE, "Lot 42 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_LOT42_AUDIT, "Lot 42 audit")
    _verify_checksum(zone_set, "zone_set_checksum", EXPECTED_LOT42_ZONE_SET, "Lot 42 zone set")
    if state.get("liquidity_zones") != zone_set:
        raise Lot43ValidationError("Lot 42 state/zone-set linkage changed")
    if audit.get("state_output_checksum") != EXPECTED_LOT42_STATE:
        raise Lot43ValidationError("Lot 42 audit/state linkage changed")
    if audit.get("zone_set_checksum") != EXPECTED_LOT42_ZONE_SET:
        raise Lot43ValidationError("Lot 42 audit/zone linkage changed")
    if state.get("safety") != lot43_safety() or audit.get("safety") != lot43_safety():
        raise Lot43ValidationError("Lot 42 safety boundary changed")
    if zone_set.get("observed_book_only") is not True:
        raise Lot43ValidationError("Lot 43 requires observed-book-only Lot 42 input")
    if zone_set.get("participant_intent_inferred") is not False:
        raise Lot43ValidationError("Lot 42 participant-intent boundary changed")
    config42 = load_json_object(
        root / require_text(config.get("lot42_config_path"), "lot42_config_path")
    )
    if canonical_checksum(config42) != EXPECTED_LOT42_CONFIG:
        raise Lot43ValidationError("Lot 42 config checksum changed")
    return zone_set


def _verify_lot38_snapshot(root: Path, config: dict[str, Any]) -> OrderBookSnapshotV1:
    state = load_json_object(root / require_text(config.get("lot38_state_path"), "lot38_state_path"))
    _verify_checksum(state, "output_checksum", EXPECTED_LOT38_STATE, "Lot 38 state")
    raw = state.get("snapshot")
    if not isinstance(raw, dict):
        raise Lot43ValidationError("Lot 38 canonical snapshot missing")
    _verify_checksum(raw, "snapshot_checksum", EXPECTED_LOT38_SNAPSHOT, "Lot 38 snapshot")
    return _snapshot_from_payload(raw)


def _snapshot_from_payload(raw: dict[str, Any]) -> OrderBookSnapshotV1:
    return OrderBookSnapshotV1(
        require_text(raw.get("source_id"), "snapshot source_id"),
        require_text(raw.get("venue"), "snapshot venue"),
        require_text(raw.get("instrument_id"), "snapshot instrument_id"),
        require_text(raw.get("market_type"), "snapshot market_type"),
        require_text(raw.get("event_time"), "snapshot event_time"),
        require_text(raw.get("receive_time"), "snapshot receive_time"),
        require_integer(raw.get("sequence_id"), "snapshot sequence_id", 1),
        require_text(raw.get("sequence_anchor"), "snapshot sequence_anchor"),
        require_text(raw.get("venue_state"), "snapshot venue_state"),
        _levels_from_payload(raw.get("bids"), "snapshot bids", allow_zero=False),
        _levels_from_payload(raw.get("asks"), "snapshot asks", allow_zero=False),
        require_integer(raw.get("source_bid_depth"), "source_bid_depth", 1),
        require_integer(raw.get("source_ask_depth"), "source_ask_depth", 1),
        require_integer(raw.get("normalized_bid_depth"), "normalized_bid_depth", 1),
        require_integer(raw.get("normalized_ask_depth"), "normalized_ask_depth", 1),
        require_integer(raw.get("published_bid_depth"), "published_bid_depth", 1),
        require_integer(raw.get("published_ask_depth"), "published_ask_depth", 1),
        EXPECTED_LOT38_SNAPSHOT,
    )


def _levels_from_payload(raw: Any, field: str, allow_zero: bool) -> tuple[OrderBookLevelV1, ...]:
    if not isinstance(raw, list) or not raw:
        raise Lot43ValidationError(f"{field} must be a non-empty list")
    output: list[OrderBookLevelV1] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) != {"price", "quantity"}:
            raise Lot43ValidationError(f"{field}[{index}] fields changed")
        price = nonnegative_decimal_text(item.get("price"), f"{field}[{index}].price")
        if price <= 0:
            raise Lot43ValidationError(f"{field}[{index}].price must be positive")
        quantity = nonnegative_decimal_text(item.get("quantity"), f"{field}[{index}].quantity")
        if not allow_zero and quantity <= 0:
            raise Lot43ValidationError(f"{field}[{index}].quantity must be positive")
        output.append(OrderBookLevelV1(price, quantity))
    return tuple(output)


def _load_deltas(root: Path, config: dict[str, Any]) -> tuple[OrderBookDeltaV1, ...]:
    path = root / require_text(config.get("lot39_delta_fixture_path"), "delta fixture path")
    if file_checksum(path) != EXPECTED_DELTA_FIXTURE:
        raise Lot43ValidationError("Lot 39 delta fixture file checksum changed")
    fixture = load_json_object(path)
    raw_deltas = fixture.get("deltas")
    if fixture.get("schema_version") != "lot39-order-book-delta-sequence-fixture-v1":
        raise Lot43ValidationError("Lot 39 delta fixture schema changed")
    if fixture.get("fixture_only") is not True or fixture.get("used_for_decision") is not False:
        raise Lot43ValidationError("Lot 39 delta fixture boundary changed")
    if not isinstance(raw_deltas, list) or not raw_deltas:
        raise Lot43ValidationError("Lot 39 delta fixture is empty")
    return tuple(_delta_from_payload(item, index) for index, item in enumerate(raw_deltas))


def _delta_from_payload(raw: Any, index: int) -> OrderBookDeltaV1:
    if not isinstance(raw, dict):
        raise Lot43ValidationError(f"delta[{index}] must be an object")
    expected_checksum = raw.get("expected_book_checksum")
    if expected_checksum is not None:
        require_sha256(expected_checksum, f"delta[{index}].expected_book_checksum")
    return OrderBookDeltaV1(
        require_text(raw.get("source_id"), f"delta[{index}].source_id"),
        require_text(raw.get("venue"), f"delta[{index}].venue"),
        require_text(raw.get("instrument_id"), f"delta[{index}].instrument_id"),
        require_text(raw.get("market_type"), f"delta[{index}].market_type"),
        require_text(raw.get("event_time"), f"delta[{index}].event_time"),
        require_text(raw.get("receive_time"), f"delta[{index}].receive_time"),
        require_integer(raw.get("sequence_id"), f"delta[{index}].sequence_id", 1),
        require_integer(raw.get("prev_sequence"), f"delta[{index}].prev_sequence", 1),
        _levels_from_payload(raw.get("bids"), f"delta[{index}].bids", allow_zero=True)
        if raw.get("bids")
        else (),
        _levels_from_payload(raw.get("asks"), f"delta[{index}].asks", allow_zero=True)
        if raw.get("asks")
        else (),
        expected_checksum,
        False,
    )


def _verify_lot39_book(
    root: Path,
    config: dict[str, Any],
    snapshot: OrderBookSnapshotV1,
    deltas: tuple[OrderBookDeltaV1, ...],
) -> dict[str, Any]:
    path = root / require_text(config.get("lot39_reconstructed_book_path"), "lot39 book path")
    book = load_json_object(path)
    _verify_checksum(book, "book_checksum", EXPECTED_LOT39_BOOK, "Lot 39 reconstructed book")
    outcome = reconstruct_sequence(snapshot, deltas)
    if outcome.reconstructed_book is None or outcome.reconstructed_book.to_dict() != book:
        raise Lot43ValidationError("canonical Lot 39 replay diverges from frozen book")
    return book


def _verify_identity_and_time(
    zone_set: dict[str, Any],
    book: dict[str, Any],
    config: dict[str, Any],
) -> None:
    fields = (
        "source_id",
        "venue",
        "instrument_id",
        "market_type",
        "event_time",
        "receive_time",
        "sequence_id",
    )
    if any(zone_set.get(field) != book.get(field) for field in fields):
        raise Lot43ValidationError("Lot 42 zone set/Lot 39 book identity changed")
    decision = require_text(config.get("decision_time"), "decision_time")
    generated = require_text(config.get("generated_at"), "generated_at")
    receive = require_text(zone_set.get("receive_time"), "receive_time")
    validate_causal_times(
        require_text(zone_set.get("event_time"), "event_time"),
        receive,
        decision,
        generated,
    )
    max_age = require_integer(config.get("max_input_age_us"), "max_input_age_us", 1)
    if age_us(receive, decision) > max_age:
        raise Lot43ValidationError("Lot 42 input is stale for Lot 43")


def _build_lineage(config: dict[str, Any], available_at: str) -> Lot43LineageEnvelopeV1:
    return Lot43LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE,
        EXPECTED_LOT42_STATE,
        EXPECTED_LOT42_AUDIT,
        EXPECTED_LOT42_ZONE_SET,
        EXPECTED_LOT39_BOOK,
        EXPECTED_DELTA_FIXTURE,
        EXPECTED_LOT38_SNAPSHOT,
        canonical_checksum(config),
        available_at,
    )


def _build_resilience_state(
    zone_set: dict[str, Any],
    config: dict[str, Any],
    analysis: Any,
    policy: BookResiliencePolicy,
) -> BookResilienceStateV1:
    current = analysis.observations[-1]
    state = BookResilienceStateV1(
        require_text(zone_set.get("source_id"), "source_id"),
        require_text(zone_set.get("venue"), "venue"),
        require_text(zone_set.get("instrument_id"), "instrument_id"),
        require_text(zone_set.get("market_type"), "market_type"),
        current.event_time,
        current.receive_time,
        require_text(config.get("decision_time"), "decision_time"),
        current.sequence_id,
        tuple(item.sequence_id for item in analysis.observations),
        analysis.volatility_measure_bps,
        analysis.volatility_regime,
        REGIME_METHOD,
        analysis.depletion_events,
        analysis.resilience_slices,
        (
            "LOT43_BOOK_RESILIENCE_COMPUTED",
            "LOT43_CERTIFIED_OBSERVATION_HISTORY_ONLY",
            "LOT43_PARTICIPANT_INTENT_NOT_INFERRED",
            "LOT44_REMAINS_LOCKED",
        ),
        ZERO_SHA256,
        resilience_horizons_us=policy.resilience_horizons_us,
    )
    return replace(state, resilience_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_metrics(resilience: BookResilienceStateV1) -> Lot43MetricsV1:
    events = resilience.depletion_events
    return Lot43MetricsV1(
        len(resilience.history_sequence_ids),
        len(events),
        sum(item.replenishment_kind == "SAME_PRICE" for item in events),
        sum(item.replenishment_kind == "ADJACENT_PRICE" for item in events),
        sum(item.replenishment_kind == "MID_SHIFT" for item in events),
        sum(item.max_window_status == "EXPIRED_NO_REPLENISHMENT" for item in events),
        sum(item.max_window_status == "PENDING_WINDOW" for item in events),
    )


def build_lot43_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[
    BookResilienceReplenishmentEngineStateV1,
    BookResilienceReplenishmentEngineAuditV1,
    BookResilienceStateV1,
]:
    config = load_json_object(root / CONFIG_PATH)
    policy = _validate_config(config)
    _verify_gate(root, config)
    _verify_lifecycle(root, config)
    zone_set = _verify_lot42(root, config)
    snapshot = _verify_lot38_snapshot(root, config)
    deltas = _load_deltas(root, config)
    book = _verify_lot39_book(root, config, snapshot, deltas)
    _verify_identity_and_time(zone_set, book, config)
    observations = reconstruct_observation_history(snapshot, deltas)
    if observations[-1].sequence_id != require_integer(book.get("sequence_id"), "book sequence", 1):
        raise Lot43ValidationError("Lot 43 history does not end on frozen Lot 39 book")
    analysis = analyze_book_resilience(
        observations,
        policy,
        require_text(config.get("decision_time"), "decision_time"),
    )
    resilience = _build_resilience_state(zone_set, config, analysis, policy)
    run_context = Lot43RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )
    lineage = _build_lineage(config, observations[-1].receive_time)
    state = _build_state(config, run_context, lineage, resilience)
    audit = _build_audit(run_context, lineage, state, resilience)
    return state, audit, resilience


def _build_state(
    config: dict[str, Any],
    run_context: Lot43RunContextV1,
    lineage: Lot43LineageEnvelopeV1,
    resilience: BookResilienceStateV1,
) -> BookResilienceReplenishmentEngineStateV1:
    state = BookResilienceReplenishmentEngineStateV1(
        run_context,
        lineage,
        require_text(config.get("generated_at"), "generated_at"),
        resilience,
        _build_metrics(resilience),
        (
            "LOT43_OFFLINE_BOOK_RESILIENCE_VALIDATED",
            "LOT43_CANONICAL_LOT39_REPLAY_BOUND",
            "LOT43_NO_PARTICIPANT_INTENT_AUTHORITY",
            "LOT44_REMAINS_LOCKED",
        ),
        lot43_safety(),
        ZERO_SHA256,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    run_context: Lot43RunContextV1,
    lineage: Lot43LineageEnvelopeV1,
    state: BookResilienceReplenishmentEngineStateV1,
    resilience: BookResilienceStateV1,
) -> BookResilienceReplenishmentEngineAuditV1:
    audit = BookResilienceReplenishmentEngineAuditV1(
        run_context,
        state.output_checksum,
        resilience.resilience_checksum,
        lineage,
        (
            "entry_gate_verified",
            "lot42_frozen_lineage_verified",
            "lot39_canonical_prefix_replay_verified",
            "depletion_detection_verified",
            "same_and_adjacent_replenishment_verified",
            "directional_mid_shift_verified",
            "horizon_resilience_verified",
            "volatility_conditioning_verified",
            "participant_intent_not_inferred",
            "lot44_lock_preserved",
        ),
        (
            "LOT43_AUDIT_COMPLETE",
            "LOT43_ANALYSIS_ONLY",
            "LOT43_NO_EXECUTION_AUTHORITY",
            "LOT44_REMAINS_LOCKED",
        ),
        lot43_safety(),
        ZERO_SHA256,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def write_lot43_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state, audit, resilience = build_lot43_artifacts(root, code_commit)
    payloads = state.to_dict(), audit.to_dict(), resilience.to_dict()
    atomic_write_json(root / STATE_PATH, payloads[0])
    atomic_write_json(root / AUDIT_PATH, payloads[1])
    atomic_write_json(root / RESILIENCE_PATH, payloads[2])
    return payloads
