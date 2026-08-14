from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    load_json_object,
)

from .order_flow_delta_and_cvd_engine_models import (
    CVDPointV1,
    CVDSeriesV1,
    Lot45LineageEnvelopeV1,
    Lot45RunContextV1,
    OrderFlowDeltaCVDEngineAuditV1,
    OrderFlowDeltaCVDEngineStateV1,
    OrderFlowStateV1,
    OrderFlowWindowV1,
)
from .order_flow_delta_and_cvd_engine_validation import (
    CONFIG_VERSION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    VALIDATION_STATE,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    decimal_from_text,
    duration_us,
    event_window_bounds,
    lot45_safety,
    parse_utc_timestamp,
    require,
    require_closed_mapping,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    session_id_for_event,
    validate_causal_times,
    validate_ratio,
)
from .trades_and_aggressor_classification_schema_models import (
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

CONFIG_PATH = Path("config/microstructure/order_flow_delta_and_cvd_engine_v1.json")
STATE_PATH = Path("data/audit/order_flow_delta_and_cvd_engine_lot45.json")
AUDIT_PATH = Path("data/audit/order_flow_delta_and_cvd_engine_audit_lot45.json")
ORDER_FLOW_PATH = Path("data/audit/order_flow_state_lot45.json")
CVD_PATH = Path("data/audit/cvd_series_lot45.json")

EXPECTED_GATE_CHECKSUM = "15ca4d69e59a0898f32eb9cbe558571ecf00ae496ec5d41075da1124393d4468"
EXPECTED_GATE_MERGE = "390d0779f2be257fa8134faf8f02193a760a09c3"
EXPECTED_LOT44_STATE = "1a461cef0bedc0e2b34185ff538a64b1b53373b12b0633b749a34cee2b3c5541"
EXPECTED_LOT44_AUDIT = "03ceda1c49746509f95e7f2ed039e8cc321e8e3cb4adbb946f1aef4ed3eba07d"
EXPECTED_LOT44_CONFIDENCE = "7cb11e078d7f0d9ed0858229d8c6fe31a7cf653a238b280b05dbdd84d1250f05"
EXPECTED_LOT44_CONFIG = "dac06cb3235f3a09cbbb9b41098d7cf2593b94171659f50ef840d1633bfa95b7"
EXPECTED_LOT44_POST_MERGE = "b8b531b2fcb09a30728549cc480d54d9be71504356468704c102ff085c39ea9a"
ZERO_SHA256 = "0" * 64


@dataclass(frozen=True, slots=True)
class OrderFlowPolicy:
    decimal_precision: int
    window_size_us: int
    max_input_age_us: int
    max_unknown_volume_ratio: Decimal
    window_policy_version: str
    session_policy_version: str
    policy_version: str

    def __post_init__(self) -> None:
        require_integer(self.decimal_precision, "decimal_precision", 18)
        require_integer(self.window_size_us, "window_size_us", 1)
        require_integer(self.max_input_age_us, "max_input_age_us", 1)
        validate_ratio(self.max_unknown_volume_ratio, "max_unknown_volume_ratio")
        require(
            self.window_policy_version == WINDOW_POLICY_VERSION,
            "Lot45 window policy changed",
        )
        require(
            self.session_policy_version == SESSION_POLICY_VERSION,
            "Lot45 session policy changed",
        )
        require(self.policy_version == POLICY_VERSION, "Lot45 policy version changed")


def _verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    if actual != expected or canonical_checksum(body) != actual:
        raise Lot45ValidationError(f"{label} checksum changed")


def _config_fields() -> set[str]:
    return {
        "schema_version",
        "config_version",
        "policy_version",
        "window_policy_version",
        "session_policy_version",
        "run_id",
        "correlation_id",
        "lineage_id",
        "generated_at",
        "decision_time",
        "calculation_decimal_precision",
        "window_size_us",
        "max_input_age_us",
        "max_unknown_volume_ratio",
        "entry_gate_path",
        "entry_gate_merge_commit",
        "lot44_state_path",
        "lot44_audit_path",
        "lot44_config_path",
    }


def _validate_config(config: dict[str, Any]) -> OrderFlowPolicy:
    if set(config) != _config_fields():
        raise Lot45ValidationError("Lot45 config fields differ from contract")
    if config.get("schema_version") != CONFIG_VERSION or config.get("config_version") != CONFIG_VERSION:
        raise Lot45ValidationError("Lot45 config version changed")
    policy = OrderFlowPolicy(
        require_integer(
            config.get("calculation_decimal_precision"),
            "calculation_decimal_precision",
            18,
        ),
        require_integer(config.get("window_size_us"), "window_size_us", 1),
        require_integer(config.get("max_input_age_us"), "max_input_age_us", 1),
        decimal_from_text(
            config.get("max_unknown_volume_ratio"),
            "max_unknown_volume_ratio",
        ),
        require_text(config.get("window_policy_version"), "window_policy_version"),
        require_text(config.get("session_policy_version"), "session_policy_version"),
        require_text(config.get("policy_version"), "policy_version"),
    )
    require_text(config.get("run_id"), "run_id")
    require_text(config.get("correlation_id"), "correlation_id")
    require_text(config.get("lineage_id"), "lineage_id")
    generated_at = require_text(config.get("generated_at"), "generated_at")
    decision_time = require_text(config.get("decision_time"), "decision_time")
    parse_utc_timestamp(generated_at, "generated_at")
    parse_utc_timestamp(decision_time, "decision_time")
    require(
        generated_at == decision_time,
        "Lot45 generated_at and decision_time must match",
    )
    require(
        config.get("entry_gate_merge_commit") == EXPECTED_GATE_MERGE,
        "Lot45 entry gate merge commit changed",
    )
    return policy


def _verify_gate(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    gate = load_json_object(path)
    _verify_checksum(gate, "gate_checksum", EXPECTED_GATE_CHECKSUM, "Lot45 entry gate")
    expected = {
        "schema_version": "lot45-v4-entry-gate-v1",
        "target_lot": 45,
        "post_merge_verdict": "GO_LOT44_POST_MERGE",
        "post_merge_checksum": EXPECTED_LOT44_POST_MERGE,
        "gate_status": "GO_LOT45_IMPLEMENTATION_ENTRY",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "responsible_component": "MicrostructureDomain",
        "package_boundary": "src/crypto_quant_bot/microstructure",
        "next_lot": 46,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise Lot45ValidationError("Lot45 entry gate authorization changed")
    safety = gate.get("safety")
    if not isinstance(safety, dict):
        raise Lot45ValidationError("Lot45 entry gate safety missing")
    for field in (
        "trade_allowed",
        "execution_allowed",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
    ):
        if safety.get(field) is not False:
            raise Lot45ValidationError(f"Lot45 gate safety changed: {field}")
    if safety.get("approved_size") != 0:
        raise Lot45ValidationError("Lot45 gate approved_size changed")
    return gate


def _trade_from_payload(raw: Any) -> ClassifiedTradeV1:
    item = require_closed_mapping(
        raw,
        {
            "schema_version",
            "trade",
            "aggressor_classification",
            "classification_method",
            "confidence",
            "confidence_version",
            "quote_snapshot_checksum",
            "reason_codes",
        },
        "classified trade",
    )
    require(item.get("schema_version") == "classified-trade-v1", "classified trade schema changed")
    trade_raw = require_closed_mapping(
        item.get("trade"),
        {
            "schema_version",
            "source_id",
            "venue",
            "instrument_id",
            "market_type",
            "trade_id",
            "event_time",
            "receive_time",
            "price",
            "quantity",
            "source_side",
        },
        "timestamped trade",
    )
    require(trade_raw.get("schema_version") == "timestamped-trade-v1", "trade schema changed")
    trade = TimestampedTradeV1(
        require_text(trade_raw.get("source_id"), "source_id"),
        require_text(trade_raw.get("venue"), "venue"),
        require_text(trade_raw.get("instrument_id"), "instrument_id"),
        require_text(trade_raw.get("market_type"), "market_type"),
        require_text(trade_raw.get("trade_id"), "trade_id"),
        require_text(trade_raw.get("event_time"), "event_time"),
        require_text(trade_raw.get("receive_time"), "receive_time"),
        decimal_from_text(trade_raw.get("price"), "price"),
        decimal_from_text(trade_raw.get("quantity"), "quantity"),
        require_text(trade_raw.get("source_side"), "source_side"),
    )
    raw_reasons = item.get("reason_codes")
    if not isinstance(raw_reasons, list) or not raw_reasons:
        raise Lot45ValidationError("classified trade reason_codes invalid")
    reasons = tuple(require_text(value, "reason_code") for value in raw_reasons)
    return ClassifiedTradeV1(
        trade,
        require_text(item.get("aggressor_classification"), "aggressor_classification"),
        require_text(item.get("classification_method"), "classification_method"),
        decimal_from_text(item.get("confidence"), "confidence"),
        require_text(item.get("confidence_version"), "confidence_version"),
        require_sha256(item.get("quote_snapshot_checksum"), "quote_snapshot_checksum"),
        reasons,
    )


def _verify_lot44(
    root: Path,
    config: dict[str, Any],
    policy: OrderFlowPolicy,
) -> tuple[dict[str, Any], tuple[ClassifiedTradeV1, ...]]:
    state = load_json_object(
        root / require_text(config.get("lot44_state_path"), "lot44_state_path")
    )
    audit = load_json_object(
        root / require_text(config.get("lot44_audit_path"), "lot44_audit_path")
    )
    config44 = load_json_object(
        root / require_text(config.get("lot44_config_path"), "lot44_config_path")
    )
    _verify_checksum(state, "output_checksum", EXPECTED_LOT44_STATE, "Lot44 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_LOT44_AUDIT, "Lot44 audit")
    if canonical_checksum(config44) != EXPECTED_LOT44_CONFIG:
        raise Lot45ValidationError("Lot44 config checksum changed")
    if audit.get("state_output_checksum") != EXPECTED_LOT44_STATE:
        raise Lot45ValidationError("Lot44 audit/state linkage changed")
    if audit.get("config_checksum") != EXPECTED_LOT44_CONFIG:
        raise Lot45ValidationError("Lot44 audit/config linkage changed")
    confidence = state.get("confidence_state")
    if not isinstance(confidence, dict):
        raise Lot45ValidationError("Lot44 confidence state missing")
    _verify_checksum(
        confidence,
        "confidence_checksum",
        EXPECTED_LOT44_CONFIDENCE,
        "Lot44 confidence",
    )
    if state.get("validation_state") != "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY":
        raise Lot45ValidationError("Lot44 validation state changed")
    if state.get("safety") != lot45_safety() or audit.get("safety") != lot45_safety():
        raise Lot45ValidationError("Lot44/Lot45 safety boundary changed")
    generated_at = require_text(config.get("generated_at"), "generated_at")
    receive_time = require_text(state.get("receive_time"), "Lot44 receive_time")
    available_at = require_text(
        require_closed_mapping(
            state.get("lineage"),
            {
                "schema_version",
                "lineage_id",
                "entry_gate_checksum",
                "lot43_state_checksum",
                "lot43_audit_checksum",
                "lot43_resilience_checksum",
                "lot43_post_merge_checksum",
                "trade_fixture_checksum",
                "order_book_snapshot_checksum",
                "available_at",
            },
            "Lot44 lineage",
        ).get("available_at"),
        "Lot44 available_at",
    )
    if duration_us(available_at, generated_at) > policy.max_input_age_us:
        raise Lot45ValidationError("Lot44 input is stale for Lot45")
    validate_causal_times(
        require_text(state.get("event_time"), "Lot44 event_time"),
        receive_time,
        generated_at,
    )
    raw_trades = state.get("classified_trades")
    if not isinstance(raw_trades, list) or not raw_trades:
        raise Lot45ValidationError("Lot44 classified trades missing")
    trades = tuple(_trade_from_payload(item) for item in raw_trades)
    require(
        len({item.trade.trade_id for item in trades}) == len(trades),
        "Lot44 trade ids are not unique",
    )
    return state, trades


def _sort_key(item: ClassifiedTradeV1) -> tuple[object, object, str]:
    return (
        parse_utc_timestamp(item.trade.event_time, "trade event_time"),
        parse_utc_timestamp(item.trade.receive_time, "trade receive_time"),
        item.trade.trade_id,
    )


def build_order_flow(
    classified_trades: tuple[ClassifiedTradeV1, ...],
    policy: OrderFlowPolicy,
) -> tuple[OrderFlowStateV1, CVDSeriesV1]:
    frozen_trades = tuple(classified_trades)
    trades = tuple(sorted(frozen_trades, key=_sort_key))
    require(bool(trades), "Lot45 requires classified trades")
    identities = {
        (
            item.trade.source_id,
            item.trade.venue,
            item.trade.instrument_id,
            item.trade.market_type,
        )
        for item in trades
    }
    require(len(identities) == 1, "Lot45 trade identity must be unique")
    groups: dict[tuple[str, str], list[ClassifiedTradeV1]] = {}
    for item in trades:
        start, _ = event_window_bounds(item.trade.event_time, policy.window_size_us)
        session = session_id_for_event(item.trade.event_time, policy.session_policy_version)
        groups.setdefault((session, start), []).append(item)

    windows: list[OrderFlowWindowV1] = []
    previous_delta = Decimal("0")
    previous_session: str | None = None
    with localcontext() as context:
        context.prec = policy.decimal_precision
        for session, start in sorted(groups, key=lambda key: (key[1], key[0])):
            items = tuple(groups[(session, start)])
            _, end = event_window_bounds(items[0].trade.event_time, policy.window_size_us)
            buy = tuple(item for item in items if item.aggressor_classification == "BUY_AGGRESSOR")
            sell = tuple(item for item in items if item.aggressor_classification == "SELL_AGGRESSOR")
            unknown = tuple(item for item in items if item.aggressor_classification == "UNKNOWN")
            total_volume = sum((item.trade.quantity for item in items), Decimal("0"))
            buy_volume = sum((item.trade.quantity for item in buy), Decimal("0"))
            sell_volume = sum((item.trade.quantity for item in sell), Decimal("0"))
            unknown_volume = sum((item.trade.quantity for item in unknown), Decimal("0"))
            signed_delta = buy_volume - sell_volume
            signed_imbalance = signed_delta / total_volume
            coverage = (buy_volume + sell_volume) / total_volume
            weighted = sum(
                (item.trade.quantity * item.confidence for item in items),
                Decimal("0"),
            ) / total_volume
            impulse = signed_delta if previous_session != session else signed_delta - previous_delta
            event_time = max(items, key=_sort_key).trade.event_time
            receive_time = max(
                items,
                key=lambda item: parse_utc_timestamp(
                    item.trade.receive_time,
                    "trade receive_time",
                ),
            ).trade.receive_time
            provisional = OrderFlowWindowV1(
                start,
                end,
                event_time,
                receive_time,
                session,
                len(items),
                len(buy),
                len(sell),
                len(unknown),
                total_volume,
                buy_volume,
                sell_volume,
                unknown_volume,
                signed_delta,
                signed_imbalance,
                coverage,
                weighted,
                impulse,
                ZERO_SHA256,
            )
            window = replace(
                provisional,
                window_checksum=canonical_checksum(provisional.payload_without_checksum()),
            )
            windows.append(window)
            previous_delta = signed_delta
            previous_session = session

        all_windows = tuple(windows)
        total_volume = sum((item.total_volume for item in all_windows), Decimal("0"))
        buy_volume = sum((item.buy_volume for item in all_windows), Decimal("0"))
        sell_volume = sum((item.sell_volume for item in all_windows), Decimal("0"))
        unknown_volume = sum((item.unknown_volume for item in all_windows), Decimal("0"))
        provisional_flow = OrderFlowStateV1(
            all_windows,
            sum(item.trades_total for item in all_windows),
            sum(item.buy_trades_total for item in all_windows),
            sum(item.sell_trades_total for item in all_windows),
            sum(item.unknown_trades_total for item in all_windows),
            total_volume,
            buy_volume,
            sell_volume,
            unknown_volume,
            buy_volume - sell_volume,
            unknown_volume / total_volume,
            (buy_volume + sell_volume) / total_volume,
            sum(
                (
                    item.confidence_weighted_coverage * item.total_volume
                    for item in all_windows
                ),
                Decimal("0"),
            )
            / total_volume,
            ZERO_SHA256,
        )
        order_flow = replace(
            provisional_flow,
            order_flow_checksum=canonical_checksum(
                provisional_flow.payload_without_checksum()
            ),
        )

        points: list[CVDPointV1] = []
        current_session: str | None = None
        running = Decimal("0")
        for window in all_windows:
            if window.session_id != current_session:
                current_session = window.session_id
                running = Decimal("0")
            running += window.signed_delta
            points.append(
                CVDPointV1(
                    window.event_time,
                    window.session_id,
                    window.window_checksum,
                    window.signed_delta,
                    running,
                )
            )
        provisional_cvd = CVDSeriesV1(
            policy.session_policy_version,
            tuple(points),
            ZERO_SHA256,
        )
        cvd = replace(
            provisional_cvd,
            cvd_checksum=canonical_checksum(provisional_cvd.payload_without_checksum()),
        )
    return order_flow, cvd


def build_lot45_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    require_git_sha(code_commit, "code_commit")
    config = load_json_object(root / CONFIG_PATH)
    policy = _validate_config(config)
    _verify_gate(root, config)
    state44, trades = _verify_lot44(root, config, policy)
    order_flow, cvd = build_order_flow(trades, policy)
    require(
        order_flow.unknown_volume_ratio <= policy.max_unknown_volume_ratio,
        "Lot45 unknown-volume ratio exceeds configured fail-closed threshold",
    )
    generated_at = require_text(config.get("generated_at"), "generated_at")
    event_time = max(
        (item.trade.event_time for item in trades),
        key=lambda value: parse_utc_timestamp(value, "trade event_time"),
    )
    receive_time = max(
        (item.trade.receive_time for item in trades),
        key=lambda value: parse_utc_timestamp(value, "trade receive_time"),
    )
    validate_causal_times(event_time, receive_time, generated_at)
    run_context = Lot45RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        CONFIG_VERSION,
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )
    lineage = Lot45LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_GATE_MERGE,
        EXPECTED_LOT44_STATE,
        EXPECTED_LOT44_AUDIT,
        EXPECTED_LOT44_CONFIDENCE,
        EXPECTED_LOT44_CONFIG,
        EXPECTED_LOT44_POST_MERGE,
        require_text(state44.get("receive_time"), "Lot44 receive_time"),
    )
    reason_codes = (
        "LOT45_OFFLINE_ORDER_FLOW_DELTA_CVD_VALIDATED",
        "EVENT_TIME_TUMBLING_WINDOWS_ENFORCED",
        "UNKNOWN_VOLUME_PRESERVED_WITH_ZERO_SIGNED_CONTRIBUTION",
        "CVD_SESSION_RESET_POLICY_VERSIONED",
        "CLASSIFICATION_COVERAGE_AND_CONFIDENCE_BOUND",
        "NO_FUTURE_STATE_OR_LOOKAHEAD",
        "LOT46_REMAINS_LOCKED",
    )
    provisional_state = OrderFlowDeltaCVDEngineStateV1(
        run_context,
        lineage,
        event_time,
        receive_time,
        generated_at,
        VALIDATION_STATE,
        POLICY_VERSION,
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        order_flow,
        cvd,
        reason_codes,
        lot45_safety(),
        ZERO_SHA256,
    )
    state = replace(
        provisional_state,
        output_checksum=canonical_checksum(provisional_state.payload_without_checksum()),
    )
    config_checksum = canonical_checksum(config)
    provisional_audit = OrderFlowDeltaCVDEngineAuditV1(
        code_commit,
        state.output_checksum,
        config_checksum,
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT44_STATE,
        EXPECTED_LOT44_AUDIT,
        EXPECTED_LOT44_CONFIDENCE,
        EXPECTED_LOT44_POST_MERGE,
        order_flow.order_flow_checksum,
        cvd.cvd_checksum,
        VALIDATION_STATE,
        lot45_safety(),
        ZERO_SHA256,
    )
    audit = replace(
        provisional_audit,
        audit_checksum=canonical_checksum(provisional_audit.payload_without_checksum()),
    )
    return state.to_dict(), audit.to_dict(), order_flow.to_dict(), cvd.to_dict()


def write_lot45_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    state, audit, order_flow, cvd = build_lot45_artifacts(root, code_commit)
    atomic_write_json(root / STATE_PATH, state)
    atomic_write_json(root / AUDIT_PATH, audit)
    atomic_write_json(root / ORDER_FLOW_PATH, order_flow)
    atomic_write_json(root / CVD_PATH, cvd)
    return state, audit, order_flow, cvd
