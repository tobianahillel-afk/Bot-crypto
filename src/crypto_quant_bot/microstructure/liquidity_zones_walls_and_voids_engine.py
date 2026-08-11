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

from .liquidity_zones_walls_and_voids_analysis import (
    LiquidityAnalysisPolicy,
    analyze_observations,
    reconstruct_observation_history,
)
from .liquidity_zones_walls_and_voids_engine_models import (
    LiquidityZoneSetV1,
    LiquidityZonesWallsVoidsEngineAuditV1,
    LiquidityZonesWallsVoidsEngineStateV1,
    Lot42LineageEnvelopeV1,
    Lot42MetricsV1,
    Lot42RunContextV1,
)
from .liquidity_zones_walls_and_voids_engine_validation import (
    DISPLAYED_WALL,
    LOW_CONFIDENCE,
    PERSISTENT_ZONE,
    Lot42ValidationError,
    age_us,
    lot42_safety,
    nonnegative_decimal_text,
    positive_decimal_text,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_ratio,
)
from .order_book_delta_and_sequence_reconstructor import reconstruct_sequence
from .order_book_delta_and_sequence_reconstructor_models import OrderBookDeltaV1
from .order_book_l2_snapshot_engine_models import OrderBookLevelV1, OrderBookSnapshotV1

CONFIG_PATH = Path("config/microstructure/liquidity_zones_walls_and_voids_engine_v1.json")
STATE_PATH = Path("data/audit/liquidity_zones_walls_and_voids_engine_lot42.json")
AUDIT_PATH = Path("data/audit/liquidity_zones_walls_and_voids_engine_audit_lot42.json")
ZONE_SET_PATH = Path("data/audit/liquidity_zone_set_lot42.json")
EXPECTED_GATE = "7ab3b17a74d30866fbec4ec15acfe608a9545e8831d80dcb39db2d059e293924"
EXPECTED_GATE_MERGE = "7456c5b80b609ee5958d8b6da0effd489faa308c"
EXPECTED_LOT41_STATE = "23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573"
EXPECTED_LOT41_AUDIT = "af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd"
EXPECTED_LOT41_FEATURE = "77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5"
EXPECTED_LOT38_STATE = "7610fc6ea73e49075a1b8611f8344c7b9c8fcf8ab02f55612d914eeac0ccda9b"
EXPECTED_LOT38_SNAPSHOT = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
EXPECTED_LOT39_STATE = "d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_DELTA_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"
ZERO_SHA256 = "0" * 64


def _verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    if actual != expected or canonical_checksum(body) != actual:
        raise Lot42ValidationError(f"{label} checksum changed")


def _validate_config(config: dict[str, Any]) -> LiquidityAnalysisPolicy:
    if set(config) != _config_fields():
        raise Lot42ValidationError("Lot 42 config fields differ from contract")
    expected_version = "lot42-liquidity-zones-walls-voids-config-v1"
    if config.get("schema_version") != expected_version or config.get("config_version") != expected_version:
        raise Lot42ValidationError("Lot 42 config version changed")
    precision = require_integer(config.get("calculation_decimal_precision"), "decimal precision", 1)
    if precision != 50:
        raise Lot42ValidationError("Lot 42 decimal precision changed")
    policy = _policy_from_config(config, precision)
    _validate_policy(policy)
    return policy


def _config_fields() -> set[str]:
    return {
        "schema_version", "config_version", "run_id", "correlation_id", "lineage_id",
        "generated_at", "decision_time", "calculation_decimal_precision", "cluster_distance_bps",
        "history_match_distance_bps", "wall_min_notional", "persistent_min_observations",
        "persistent_min_ratio", "void_min_gap_bps", "wall_high_confidence_max_cancellation_rate",
        "max_input_age_us", "entry_gate_path", "lot41_lifecycle_overlay_path", "lot41_state_path",
        "lot41_audit_path", "lot41_feature_path", "lot38_state_path", "lot39_state_path",
        "lot39_reconstructed_book_path", "lot39_delta_fixture_path",
    }


def _policy_from_config(config: dict[str, Any], precision: int) -> LiquidityAnalysisPolicy:
    return LiquidityAnalysisPolicy(
        precision,
        positive_decimal_text(config.get("cluster_distance_bps"), "cluster_distance_bps"),
        positive_decimal_text(config.get("history_match_distance_bps"), "history_match_distance_bps"),
        positive_decimal_text(config.get("wall_min_notional"), "wall_min_notional"),
        require_integer(config.get("persistent_min_observations"), "persistent_min_observations", 1),
        nonnegative_decimal_text(config.get("persistent_min_ratio"), "persistent_min_ratio"),
        positive_decimal_text(config.get("void_min_gap_bps"), "void_min_gap_bps"),
        nonnegative_decimal_text(
            config.get("wall_high_confidence_max_cancellation_rate"),
            "wall_high_confidence_max_cancellation_rate",
        ),
    )


def _validate_policy(policy: LiquidityAnalysisPolicy) -> None:
    validate_ratio(policy.persistent_min_ratio, "persistent_min_ratio")
    validate_ratio(
        policy.wall_high_confidence_max_cancellation_rate,
        "wall_high_confidence_max_cancellation_rate",
    )
    if policy.history_match_distance_bps < policy.cluster_distance_bps:
        raise Lot42ValidationError("history match distance cannot be below cluster distance")


def _verify_gate(root: Path, config: dict[str, Any]) -> None:
    path = root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    gate = load_json_object(path)
    _verify_checksum(gate, "output_checksum", EXPECTED_GATE, "Lot 42 entry gate")
    expected = {
        "target_lot": 42,
        "gate_status": "GO_LOT42_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT42",
        "implementation_started": False,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "next_lot": 43,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise Lot42ValidationError("Lot 42 entry gate authorization changed")
    if gate.get("safety") != lot42_safety():
        raise Lot42ValidationError("Lot 42 entry gate safety changed")


def _verify_lifecycle(root: Path, config: dict[str, Any]) -> None:
    path = root / require_text(config.get("lot41_lifecycle_overlay_path"), "lifecycle path")
    overlay = load_json_object(path)
    if overlay.get("latest_implemented_lot") != 41:
        raise Lot42ValidationError("Lot 42 requires audited lifecycle latest lot 41")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise Lot42ValidationError("Lot 41 lifecycle lots missing")
    expected41 = "IMPLEMENTED_VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY"
    if not isinstance(lots.get("41"), dict) or lots["41"].get("status") != expected41:
        raise Lot42ValidationError("Lot 41 lifecycle status changed")
    expected42 = {"implementation_started": False, "status": "PLANNED_LOCKED"}
    if lots.get("42") != expected42:
        raise Lot42ValidationError("historical Lot 42 gate lifecycle changed")


def _verify_lot41(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    state = load_json_object(root / require_text(config.get("lot41_state_path"), "lot41_state_path"))
    audit = load_json_object(root / require_text(config.get("lot41_audit_path"), "lot41_audit_path"))
    feature = load_json_object(root / require_text(config.get("lot41_feature_path"), "lot41_feature_path"))
    _verify_checksum(state, "output_checksum", EXPECTED_LOT41_STATE, "Lot 41 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_LOT41_AUDIT, "Lot 41 audit")
    _verify_checksum(feature, "feature_checksum", EXPECTED_LOT41_FEATURE, "Lot 41 feature")
    if state.get("book_features") != feature:
        raise Lot42ValidationError("Lot 41 state/feature linkage changed")
    if audit.get("state_output_checksum") != EXPECTED_LOT41_STATE:
        raise Lot42ValidationError("Lot 41 audit/state linkage changed")
    if audit.get("feature_checksum") != EXPECTED_LOT41_FEATURE:
        raise Lot42ValidationError("Lot 41 audit/feature linkage changed")
    _verify_feature_safety(feature, state)
    return feature


def _verify_feature_safety(feature: dict[str, Any], state: dict[str, Any]) -> None:
    quality = feature.get("book_quality")
    if not isinstance(quality, dict):
        raise Lot42ValidationError("Lot 41 feature book quality missing")
    if quality.get("health_status") != "HEALTHY" or quality.get("book_health_score") != "100":
        raise Lot42ValidationError("Lot 42 requires healthy Lot 41 book feature")
    if quality.get("consequence") != "NONE":
        raise Lot42ValidationError("Lot 42 refuses active upstream consequence")
    if feature.get("observed_depth_only") is not True or feature.get("extrapolated") is not False:
        raise Lot42ValidationError("Lot 42 requires observed non-extrapolated depth")
    if state.get("safety") != lot42_safety():
        raise Lot42ValidationError("Lot 41 safety boundary changed")


def _verify_lot38_snapshot(root: Path, config: dict[str, Any]) -> OrderBookSnapshotV1:
    path = root / require_text(config.get("lot38_state_path"), "lot38_state_path")
    state = load_json_object(path)
    _verify_checksum(state, "output_checksum", EXPECTED_LOT38_STATE, "Lot 38 state")
    raw = state.get("snapshot")
    if not isinstance(raw, dict):
        raise Lot42ValidationError("Lot 38 canonical snapshot missing")
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
        raise Lot42ValidationError(f"{field} must be a non-empty list")
    output: list[OrderBookLevelV1] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) != {"price", "quantity"}:
            raise Lot42ValidationError(f"{field}[{index}] fields changed")
        price = positive_decimal_text(item.get("price"), f"{field}[{index}].price")
        parser = nonnegative_decimal_text if allow_zero else positive_decimal_text
        quantity = parser(item.get("quantity"), f"{field}[{index}].quantity")
        output.append(OrderBookLevelV1(price, quantity))
    return tuple(output)


def _load_deltas(root: Path, config: dict[str, Any]) -> tuple[OrderBookDeltaV1, ...]:
    path = root / require_text(config.get("lot39_delta_fixture_path"), "delta fixture path")
    if file_checksum(path) != EXPECTED_DELTA_FIXTURE:
        raise Lot42ValidationError("Lot 39 delta fixture file checksum changed")
    fixture = load_json_object(path)
    if fixture.get("schema_version") != "lot39-order-book-delta-sequence-fixture-v1":
        raise Lot42ValidationError("Lot 39 delta fixture schema changed")
    if fixture.get("fixture_only") is not True or fixture.get("used_for_decision") is not False:
        raise Lot42ValidationError("Lot 39 delta fixture boundary changed")
    raw_deltas = fixture.get("deltas")
    if not isinstance(raw_deltas, list) or not raw_deltas:
        raise Lot42ValidationError("Lot 39 delta fixture is empty")
    return tuple(_delta_from_payload(item, index) for index, item in enumerate(raw_deltas))


def _delta_from_payload(raw: Any, index: int) -> OrderBookDeltaV1:
    if not isinstance(raw, dict):
        raise Lot42ValidationError(f"delta[{index}] must be an object")
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
        if raw.get("bids") else (),
        _levels_from_payload(raw.get("asks"), f"delta[{index}].asks", allow_zero=True)
        if raw.get("asks") else (),
        expected_checksum,
        False,
    )


def _verify_lot39(
    root: Path,
    config: dict[str, Any],
    snapshot: OrderBookSnapshotV1,
    deltas: tuple[OrderBookDeltaV1, ...],
) -> dict[str, Any]:
    state = load_json_object(root / require_text(config.get("lot39_state_path"), "lot39_state_path"))
    book = load_json_object(
        root / require_text(config.get("lot39_reconstructed_book_path"), "lot39_reconstructed_book_path")
    )
    _verify_checksum(state, "output_checksum", EXPECTED_LOT39_STATE, "Lot 39 state")
    _verify_checksum(book, "book_checksum", EXPECTED_LOT39_BOOK, "Lot 39 reconstructed book")
    if state.get("reconstructed_book") != book or state.get("synchronization_state") != "SYNCED":
        raise Lot42ValidationError("Lot 39 state/book linkage changed")
    outcome = reconstruct_sequence(snapshot, deltas)
    if outcome.reconstructed_book is None or outcome.reconstructed_book.to_dict() != book:
        raise Lot42ValidationError("canonical Lot 39 replay diverges from frozen book")
    return book


def _verify_current_identity(feature: dict[str, Any], book: dict[str, Any], config: dict[str, Any]) -> Decimal:
    fields = ("source_id", "venue", "instrument_id", "market_type", "event_time", "receive_time", "sequence_id")
    if any(feature.get(field) != book.get(field) for field in fields):
        raise Lot42ValidationError("Lot 41 feature/Lot 39 book identity changed")
    mid = positive_decimal_text(feature.get("mid_price"), "mid_price")
    decision = require_text(config.get("decision_time"), "decision_time")
    generated = require_text(config.get("generated_at"), "generated_at")
    validate_causal_times(
        require_text(feature.get("event_time"), "event_time"),
        require_text(feature.get("receive_time"), "receive_time"),
        decision,
        generated,
    )
    max_age = require_integer(config.get("max_input_age_us"), "max_input_age_us", 1)
    if age_us(require_text(feature.get("receive_time"), "receive_time"), decision) > max_age:
        raise Lot42ValidationError("Lot 41 feature is stale for Lot 42")
    return mid


def _build_lineage(config: dict[str, Any], available_at: str) -> Lot42LineageEnvelopeV1:
    return Lot42LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE,
        EXPECTED_LOT41_STATE,
        EXPECTED_LOT41_AUDIT,
        EXPECTED_LOT41_FEATURE,
        EXPECTED_LOT39_BOOK,
        EXPECTED_DELTA_FIXTURE,
        EXPECTED_LOT38_SNAPSHOT,
        canonical_checksum(config),
        available_at,
    )


def _build_zone_set(
    feature: dict[str, Any],
    config: dict[str, Any],
    mid: Decimal,
    analysis: Any,
) -> LiquidityZoneSetV1:
    sequence_ids = tuple(item.sequence_id for item in analysis.observations)
    zone_set = LiquidityZoneSetV1(
        require_text(feature.get("source_id"), "source_id"),
        require_text(feature.get("venue"), "venue"),
        require_text(feature.get("instrument_id"), "instrument_id"),
        require_text(feature.get("market_type"), "market_type"),
        require_text(feature.get("event_time"), "event_time"),
        require_text(feature.get("receive_time"), "receive_time"),
        require_text(config.get("decision_time"), "decision_time"),
        require_integer(feature.get("sequence_id"), "sequence_id", 1),
        mid,
        sequence_ids,
        analysis.zones,
        analysis.voids,
        analysis.expired_candidates_total,
        (
            "LOT42_LIQUIDITY_STRUCTURE_COMPUTED",
            "LOT42_OBSERVED_HISTORY_ONLY",
            "LOT42_PARTICIPANT_INTENT_NOT_INFERRED",
            "LOT43_REMAINS_LOCKED",
        ),
        ZERO_SHA256,
    )
    return replace(zone_set, zone_set_checksum=canonical_checksum(zone_set.payload_without_checksum()))


def _build_metrics(zone_set: LiquidityZoneSetV1) -> Lot42MetricsV1:
    return Lot42MetricsV1(
        len(zone_set.history_sequence_ids),
        len(zone_set.zones),
        sum(DISPLAYED_WALL in zone.classifications for zone in zone_set.zones),
        sum(PERSISTENT_ZONE in zone.classifications for zone in zone_set.zones),
        sum(zone.confidence_status == LOW_CONFIDENCE for zone in zone_set.zones),
        len(zone_set.voids),
        zone_set.expired_candidates_total,
    )


def build_lot42_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[LiquidityZonesWallsVoidsEngineStateV1, LiquidityZonesWallsVoidsEngineAuditV1, LiquidityZoneSetV1]:
    config = load_json_object(root / CONFIG_PATH)
    policy = _validate_config(config)
    _verify_gate(root, config)
    _verify_lifecycle(root, config)
    feature = _verify_lot41(root, config)
    snapshot = _verify_lot38_snapshot(root, config)
    deltas = _load_deltas(root, config)
    book = _verify_lot39(root, config, snapshot, deltas)
    mid = _verify_current_identity(feature, book, config)
    observations = reconstruct_observation_history(snapshot, deltas)
    analysis = analyze_observations(observations, policy)
    if observations[-1].sequence_id != require_integer(book.get("sequence_id"), "book sequence_id", 1):
        raise Lot42ValidationError("Lot 42 history does not end on frozen Lot 39 book")
    zone_set = _build_zone_set(feature, config, mid, analysis)
    run_context = Lot42RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )
    lineage = _build_lineage(config, require_text(feature.get("receive_time"), "receive_time"))
    state = _build_state(config, run_context, lineage, zone_set)
    audit = _build_audit(run_context, lineage, state, zone_set)
    return state, audit, zone_set


def _build_state(
    config: dict[str, Any],
    run_context: Lot42RunContextV1,
    lineage: Lot42LineageEnvelopeV1,
    zone_set: LiquidityZoneSetV1,
) -> LiquidityZonesWallsVoidsEngineStateV1:
    state = LiquidityZonesWallsVoidsEngineStateV1(
        run_context,
        lineage,
        require_text(config.get("generated_at"), "generated_at"),
        zone_set,
        _build_metrics(zone_set),
        (
            "LOT42_OFFLINE_LIQUIDITY_ZONES_VALIDATED",
            "LOT42_CANONICAL_LOT39_REPLAY_BOUND",
            "LOT42_NO_PARTICIPANT_INTENT_AUTHORITY",
            "LOT43_REMAINS_LOCKED",
        ),
        lot42_safety(),
        ZERO_SHA256,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    run_context: Lot42RunContextV1,
    lineage: Lot42LineageEnvelopeV1,
    state: LiquidityZonesWallsVoidsEngineStateV1,
    zone_set: LiquidityZoneSetV1,
) -> LiquidityZonesWallsVoidsEngineAuditV1:
    audit = LiquidityZonesWallsVoidsEngineAuditV1(
        run_context,
        state.output_checksum,
        zone_set.zone_set_checksum,
        lineage,
        (
            "entry_gate_verified",
            "lot41_frozen_lineage_verified",
            "lot39_canonical_prefix_replay_verified",
            "versioned_bps_clustering_verified",
            "persistence_replenishment_cancellation_measured",
            "bilateral_void_scan_verified",
            "participant_intent_not_inferred",
            "lot43_lock_preserved",
        ),
        (
            "LOT42_AUDIT_COMPLETE",
            "LOT42_ANALYSIS_ONLY",
            "LOT42_NO_EXECUTION_AUTHORITY",
            "LOT43_REMAINS_LOCKED",
        ),
        lot42_safety(),
        ZERO_SHA256,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def write_lot42_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state, audit, zone_set = build_lot42_artifacts(root, code_commit)
    payloads = state.to_dict(), audit.to_dict(), zone_set.to_dict()
    atomic_write_json(root / STATE_PATH, payloads[0])
    atomic_write_json(root / AUDIT_PATH, payloads[1])
    atomic_write_json(root / ZONE_SET_PATH, payloads[2])
    return payloads
