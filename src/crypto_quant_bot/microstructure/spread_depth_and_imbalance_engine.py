from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    load_json_object,
)

from .book_integrity_desynchronization_detector_validation import require_integer
from .spread_depth_and_imbalance_engine_models import (
    BookFeatureStateV1,
    BookQualityBindingV1,
    CumulativeDepthLevelV1,
    DepthBandV1,
    Lot41LineageEnvelopeV1,
    Lot41MetricsV1,
    Lot41RunContextV1,
    SpreadDepthImbalanceEngineAuditV1,
    SpreadDepthImbalanceEngineStateV1,
    TopOfBookV1,
)
from .spread_depth_and_imbalance_engine_validation import (
    Lot41ValidationError,
    lot41_safety,
    parse_book_levels,
    parse_depth_bands,
    positive_decimal_text,
    require_text,
    symmetric_imbalance,
    validate_book_open,
    validate_reference_identity,
    validate_reference_times,
)

CONFIG_PATH = Path("config/microstructure/spread_depth_and_imbalance_engine_v1.json")
STATE_PATH = Path("data/audit/spread_depth_and_imbalance_engine_lot41.json")
AUDIT_PATH = Path("data/audit/spread_depth_and_imbalance_engine_audit_lot41.json")
FEATURE_PATH = Path("data/audit/book_feature_state_lot41.json")
EXPECTED_GATE = "1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe"
EXPECTED_LOT40_STATE = "e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477"
EXPECTED_LOT40_AUDIT = "978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c"
EXPECTED_INTEGRITY = "35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a"
EXPECTED_VETO = "000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc"
EXPECTED_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
ZERO_SHA256 = "0" * 64


def _verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    if actual != expected or canonical_checksum(body) != actual:
        raise Lot41ValidationError(f"{label} checksum changed")


def _validate_config(config: dict[str, Any]) -> tuple[tuple[Decimal, ...], int]:
    fields = {
        "schema_version", "config_version", "run_id", "correlation_id", "lineage_id",
        "generated_at", "decision_time", "feature_horizon", "calculation_decimal_precision",
        "depth_bands_bps", "required_book_health_status", "required_health_consequence",
        "entry_gate_path", "lot40_lifecycle_overlay_path", "lot40_state_path",
        "lot40_audit_path", "lot40_book_integrity_path", "lot40_book_health_veto_path",
        "reconstructed_book_path",
    }
    if set(config) != fields:
        raise Lot41ValidationError("Lot 41 config fields differ from contract")
    if config.get("schema_version") != "lot41-spread-depth-imbalance-config-v1":
        raise Lot41ValidationError("Lot 41 config schema changed")
    if config.get("config_version") != "lot41-spread-depth-imbalance-config-v1":
        raise Lot41ValidationError("Lot 41 config version changed")
    if config.get("feature_horizon") != "BOOK_SNAPSHOT":
        raise Lot41ValidationError("Lot 41 feature horizon changed")
    precision = require_integer(config.get("calculation_decimal_precision"), "decimal precision", 1)
    if precision != 50:
        raise Lot41ValidationError("Lot 41 decimal precision changed")
    return parse_depth_bands(config.get("depth_bands_bps")), precision


def _verify_gate(root: Path, config: dict[str, Any]) -> None:
    path = root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    gate = load_json_object(path)
    _verify_checksum(gate, "output_checksum", EXPECTED_GATE, "Lot 41 entry gate")
    expected = {
        "target_lot": 41,
        "gate_status": "GO_LOT41_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT41",
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_started": False,
        "next_lot": 42,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise Lot41ValidationError("Lot 41 entry gate authorization changed")
    if gate.get("safety") != lot41_safety():
        raise Lot41ValidationError("Lot 41 entry gate safety changed")


def _verify_lifecycle(root: Path, config: dict[str, Any]) -> None:
    path = root / require_text(config.get("lot40_lifecycle_overlay_path"), "lifecycle path")
    overlay = load_json_object(path)
    if overlay.get("latest_implemented_lot") != 40:
        raise Lot41ValidationError("Lot 41 requires audited lifecycle latest lot 40")
    lots = overlay.get("lots")
    expected40 = "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY"
    if not isinstance(lots, dict) or not isinstance(lots.get("40"), dict):
        raise Lot41ValidationError("Lot 40 lifecycle record missing")
    if lots["40"].get("status") != expected40:
        raise Lot41ValidationError("Lot 40 lifecycle status changed")
    expected41 = {"implementation_started": False, "status": "PLANNED_LOCKED"}
    if lots.get("41") != expected41:
        raise Lot41ValidationError("historical Lot 41 gate lifecycle changed")


def _load_upstream(root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    keys = (
        "lot40_state_path", "lot40_audit_path", "lot40_book_integrity_path",
        "lot40_book_health_veto_path", "reconstructed_book_path",
    )
    return tuple(
        load_json_object(root / require_text(config.get(key), key))
        for key in keys
    )


def _verify_upstream(upstream: tuple[dict[str, Any], ...], config: dict[str, Any]) -> None:
    state, audit, integrity, veto, book = upstream
    _verify_checksum(state, "output_checksum", EXPECTED_LOT40_STATE, "Lot 40 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_LOT40_AUDIT, "Lot 40 audit")
    _verify_checksum(integrity, "integrity_checksum", EXPECTED_INTEGRITY, "Lot 40 integrity")
    _verify_checksum(veto, "veto_checksum", EXPECTED_VETO, "Lot 40 veto")
    _verify_checksum(book, "book_checksum", EXPECTED_BOOK, "reconstructed book")
    if state.get("book_integrity") != integrity or state.get("book_health_veto") != veto:
        raise Lot41ValidationError("Lot 40 embedded health artifacts changed")
    if audit.get("state_output_checksum") != EXPECTED_LOT40_STATE:
        raise Lot41ValidationError("Lot 40 audit/state linkage changed")
    if audit.get("integrity_checksum") != EXPECTED_INTEGRITY or audit.get("veto_checksum") != EXPECTED_VETO:
        raise Lot41ValidationError("Lot 40 audit health linkage changed")
    _verify_health(integrity, veto, config)
    validate_reference_identity(book, integrity)


def _verify_health(integrity: dict[str, Any], veto: dict[str, Any], config: dict[str, Any]) -> None:
    required_health = require_text(config.get("required_book_health_status"), "required health")
    required_consequence = require_text(config.get("required_health_consequence"), "required consequence")
    if integrity.get("health_status") != required_health or integrity.get("book_health_score") != "100":
        raise Lot41ValidationError("Lot 41 requires certified healthy score 100")
    if veto.get("consequence") != required_consequence or veto.get("veto_active") is not False:
        raise Lot41ValidationError("Lot 41 refuses active upstream health veto")
    if veto.get("critical_veto_active") is not False:
        raise Lot41ValidationError("Lot 41 refuses critical upstream veto")
    if integrity.get("crossed") is not False or integrity.get("locked") is not False:
        raise Lot41ValidationError("Lot 41 refuses crossed or locked integrity state")


def _build_cumulative(
    levels: tuple[tuple[Decimal, Decimal], ...], mid: Decimal, side: str
) -> tuple[CumulativeDepthLevelV1, ...]:
    cumulative = Decimal("0")
    output: list[CumulativeDepthLevelV1] = []
    for price, quantity in levels:
        cumulative += quantity
        difference = mid - price if side == "bids" else price - mid
        distance = difference / mid * Decimal("10000")
        output.append(CumulativeDepthLevelV1(price, quantity, cumulative, distance))
    return tuple(output)


def _build_bands(
    bids: tuple[tuple[Decimal, Decimal], ...],
    asks: tuple[tuple[Decimal, Decimal], ...],
    mid: Decimal,
    bands: tuple[Decimal, ...],
) -> tuple[DepthBandV1, ...]:
    output: list[DepthBandV1] = []
    for band in bands:
        selected_bids = tuple(level for level in bids if (mid - level[0]) / mid * Decimal("10000") <= band)
        selected_asks = tuple(level for level in asks if (level[0] - mid) / mid * Decimal("10000") <= band)
        bid_depth = sum((quantity for _, quantity in selected_bids), Decimal("0"))
        ask_depth = sum((quantity for _, quantity in selected_asks), Decimal("0"))
        imbalance, status = symmetric_imbalance(bid_depth, ask_depth)
        output.append(DepthBandV1(band, bid_depth, ask_depth, len(selected_bids), len(selected_asks), imbalance, status))
    return tuple(output)


def _build_feature(
    book: dict[str, Any], integrity: dict[str, Any], veto: dict[str, Any],
    bands: tuple[Decimal, ...], precision: int, decision_time: str,
) -> BookFeatureStateV1:
    bids = parse_book_levels(book.get("bids"), "bids")
    asks = parse_book_levels(book.get("asks"), "asks")
    best_bid, best_ask = bids[0], asks[0]
    validate_book_open(best_bid[0], best_ask[0])
    with localcontext() as context:
        context.prec = precision
        spread = best_ask[0] - best_bid[0]
        mid = (best_ask[0] + best_bid[0]) / Decimal("2")
        spread_bps = spread / mid * Decimal("10000")
        microprice = (best_ask[0] * best_bid[1] + best_bid[0] * best_ask[1]) / (best_bid[1] + best_ask[1])
        depth_bands = _build_bands(bids, asks, mid, bands)
        cumulative_bids = _build_cumulative(bids, mid, "bids")
        cumulative_asks = _build_cumulative(asks, mid, "asks")
    quality = BookQualityBindingV1(
        require_text(integrity.get("health_status"), "health_status"),
        positive_decimal_text(integrity.get("book_health_score"), "book_health_score"),
        require_text(veto.get("consequence"), "consequence"),
        require_integer(book.get("sequence_id"), "sequence_id", 1),
        EXPECTED_INTEGRITY,
        EXPECTED_VETO,
    )
    feature = BookFeatureStateV1(
        require_text(book.get("source_id"), "source_id"), require_text(book.get("venue"), "venue"),
        require_text(book.get("instrument_id"), "instrument_id"), require_text(book.get("market_type"), "market_type"),
        require_text(book.get("event_time"), "event_time"), require_text(book.get("receive_time"), "receive_time"),
        decision_time, quality.sequence_id, "BOOK_SNAPSHOT", spread, spread_bps, mid, microprice,
        TopOfBookV1(best_bid[0], best_bid[1], best_ask[0], best_ask[1]), depth_bands,
        cumulative_bids, cumulative_asks, quality,
        ("LOT41_SPREAD_DEPTH_IMBALANCE_COMPUTED", "LOT41_OBSERVED_DEPTH_ONLY", "LOT42_REMAINS_LOCKED"),
        ZERO_SHA256,
    )
    return replace(feature, feature_checksum=canonical_checksum(feature.payload_without_checksum()))


def _build_lineage(config: dict[str, Any], feature: BookFeatureStateV1) -> Lot41LineageEnvelopeV1:
    return Lot41LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"), EXPECTED_GATE,
        EXPECTED_LOT40_STATE, EXPECTED_LOT40_AUDIT, EXPECTED_INTEGRITY, EXPECTED_VETO,
        EXPECTED_BOOK, canonical_checksum(config), feature.receive_time,
    )


def build_lot41_artifacts(
    root: Path, code_commit: str
) -> tuple[SpreadDepthImbalanceEngineStateV1, SpreadDepthImbalanceEngineAuditV1, BookFeatureStateV1]:
    config = load_json_object(root / CONFIG_PATH)
    bands, precision = _validate_config(config)
    _verify_gate(root, config)
    _verify_lifecycle(root, config)
    upstream = _load_upstream(root, config)
    state40, _audit40, integrity, veto, book = upstream
    _verify_upstream(upstream, config)
    decision = require_text(config.get("decision_time"), "decision_time")
    generated = require_text(config.get("generated_at"), "generated_at")
    validate_reference_times(book, integrity, decision, generated)
    feature = _build_feature(book, integrity, veto, bands, precision, decision)
    run_context = Lot41RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )
    lineage = _build_lineage(config, feature)
    metrics = Lot41MetricsV1(
        len(feature.depth_bands), sum(item.imbalance is None for item in feature.depth_bands),
        len(feature.cumulative_bids), len(feature.cumulative_asks),
    )
    state = SpreadDepthImbalanceEngineStateV1(
        run_context, lineage, generated, feature, metrics,
        ("LOT41_OFFLINE_FEATURES_VALIDATED", "LOT41_BOOK_QUALITY_BOUND", "LOT42_REMAINS_LOCKED"),
        lot41_safety(), ZERO_SHA256,
    )
    state = replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))
    audit = SpreadDepthImbalanceEngineAuditV1(
        run_context, state.output_checksum, feature.feature_checksum, lineage,
        ("entry_gate_verified", "lot40_frozen_lineage_verified", "book_health_veto_none", "deterministic_math_applied", "observed_depth_only"),
        ("LOT41_AUDIT_COMPLETE", "LOT41_NO_EXECUTION_AUTHORITY", "LOT42_REMAINS_LOCKED"),
        lot41_safety(), ZERO_SHA256,
    )
    audit = replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))
    if state40.get("output_checksum") != lineage.lot40_state_checksum:
        raise Lot41ValidationError("Lot 40 state lineage mismatch")
    return state, audit, feature


def write_lot41_artifacts(root: Path, code_commit: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state, audit, feature = build_lot41_artifacts(root, code_commit)
    payloads = state.to_dict(), audit.to_dict(), feature.to_dict()
    atomic_write_json(root / STATE_PATH, payloads[0])
    atomic_write_json(root / AUDIT_PATH, payloads[1])
    atomic_write_json(root / FEATURE_PATH, payloads[2])
    return payloads