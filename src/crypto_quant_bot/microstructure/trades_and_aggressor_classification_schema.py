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

from .order_book_l2_snapshot_engine_models import OrderBookLevelV1, OrderBookSnapshotV1
from .trades_and_aggressor_classification_schema_models import (
    AggressorConfidenceStateV1,
    ClassifiedTradeV1,
    Lot44LineageEnvelopeV1,
    Lot44MetricsV1,
    Lot44RunContextV1,
    TimestampedTradeV1,
    TradesAggressorClassificationSchemaAuditV1,
    TradesAggressorClassificationSchemaStateV1,
)
from .trades_and_aggressor_classification_schema_validation import (
    CONFIDENCE_SEMANTICS,
    decimal_from_text,
    duration_us,
    lot44_safety,
    parse_utc_timestamp,
    require,
    require_closed_mapping,
    require_integer,
    require_text,
)

CONFIG_PATH = Path("config/microstructure/trades_and_aggressor_classification_schema_v1.json")
STATE_PATH = Path("data/audit/trades_and_aggressor_classification_schema_lot44.json")
AUDIT_PATH = Path("data/audit/trades_and_aggressor_classification_schema_audit_lot44.json")
CONFIDENCE_PATH = Path("data/audit/aggressor_confidence_state_lot44.json")
EXPECTED_GATE_CHECKSUM = "100d21ea18cfd7d9fe275ac0bea162c76a0bb7e5f85e319b543b4053e3c4d5ef"
EXPECTED_TRADE_FIXTURE_CHECKSUM = "b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8"
EXPECTED_SNAPSHOT_CHECKSUM = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
EXPECTED_LOT43_STATE = "30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6"
EXPECTED_LOT43_AUDIT = "3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67"
EXPECTED_LOT43_RESILIENCE = "598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb"
EXPECTED_LOT43_POST_MERGE = "167c69b324377ceefd322d59fab7f42d9f7998efde94503d6d86ca4a51ed9c14"
ZERO_SHA256 = "0" * 64
COMMON_REASON_CODES = (
    "LOT44_OFFLINE_AGGRESSOR_CLASSIFICATION_VALIDATED",
    "QUOTE_TEST_PRIMARY_POLICY_ENFORCED",
    "UNKNOWN_VOLUME_PRESERVED",
    "NO_FUTURE_QUOTE_BACKFILL",
    "PARTICIPANT_INTENT_NOT_ASSERTED",
    "LOT45_AND_LOT46_REMAIN_LOCKED",
)


def _validate_config(config: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "config_version",
        "confidence_version",
        "run_id",
        "correlation_id",
        "lineage_id",
        "generated_at",
        "entry_gate_path",
        "trade_fixture_path",
        "order_book_snapshot_path",
        "max_quote_age_us",
        "tick_rule_fallback_when_quote_unavailable",
        "quote_test_confidence",
        "tick_rule_confidence",
        "unknown_confidence",
    }
    require(set(config) == expected, "Lot 44 config fields differ from contract")
    require(
        config.get("schema_version")
        == "lot44-trades-aggressor-classification-config-v1",
        "Lot 44 config schema changed",
    )
    require(
        config.get("config_version")
        == "lot44-trades-aggressor-classification-config-v1",
        "Lot 44 config version changed",
    )
    require_text(config.get("confidence_version"), "confidence_version")
    parse_utc_timestamp(config.get("generated_at"), "generated_at")
    require_integer(config.get("max_quote_age_us"), "max_quote_age_us", minimum=1)
    require(
        config.get("tick_rule_fallback_when_quote_unavailable") is True,
        "tick-rule fallback policy changed",
    )
    quote = decimal_from_text(
        config.get("quote_test_confidence"),
        "quote_test_confidence",
        allow_zero=True,
    )
    tick = decimal_from_text(
        config.get("tick_rule_confidence"),
        "tick_rule_confidence",
        allow_zero=True,
    )
    unknown = decimal_from_text(
        config.get("unknown_confidence"),
        "unknown_confidence",
        allow_zero=True,
    )
    require(quote > tick > unknown == 0, "Lot 44 confidence policy ordering changed")


def _verify_gate(root: Path, config: dict[str, Any]) -> None:
    gate = load_json_object(
        root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    )
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    require(checksum == EXPECTED_GATE_CHECKSUM, "Lot 44 entry gate checksum changed")
    require(
        canonical_checksum(body) == checksum,
        "Lot 44 entry gate payload mismatch",
    )
    expected = {
        "gate_status": "GO_LOT44_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT44",
        "target_lot": 44,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_started": False,
        "next_lot": 45,
        "next_lot_status": "PLANNED_LOCKED",
    }
    require(
        all(gate.get(field) == value for field, value in expected.items()),
        "Lot 44 gate does not authorize implementation",
    )
    require(gate.get("safety") == lot44_safety(), "Lot 44 gate safety boundary changed")
    prerequisites = gate.get("prerequisites")
    require(isinstance(prerequisites, dict), "Lot 44 gate prerequisites missing")
    required = {
        "lot43_state_checksum": EXPECTED_LOT43_STATE,
        "lot43_audit_checksum": EXPECTED_LOT43_AUDIT,
        "lot43_resilience_checksum": EXPECTED_LOT43_RESILIENCE,
        "lot43_post_merge_audit_checksum": EXPECTED_LOT43_POST_MERGE,
        "lot43_post_merge_verdict": "GO_LOT43_POST_MERGE",
    }
    require(
        all(prerequisites.get(field) == value for field, value in required.items()),
        "Lot 43 prerequisite evidence changed",
    )


def _load_trade_fixture(
    root: Path,
    config: dict[str, Any],
) -> tuple[tuple[TimestampedTradeV1, ...], str]:
    path = root / require_text(config.get("trade_fixture_path"), "trade_fixture_path")
    checksum = file_checksum(path)
    require(
        checksum == EXPECTED_TRADE_FIXTURE_CHECKSUM,
        "Lot 37 trade fixture checksum changed",
    )
    fixture = load_json_object(path)
    required = {
        "schema_version",
        "fixture_id",
        "fixture_only",
        "canonical_contract",
        "source_id",
        "venue",
        "instrument_id",
        "market_type",
        "event_time",
        "available_at",
        "trades",
        "reason_codes",
        "used_for_decision",
    }
    require_closed_mapping(fixture, required, "Lot 37 trade fixture")
    require(
        fixture["schema_version"] == "lot37-offline-trade-availability-fixture-v1",
        "trade fixture schema changed",
    )
    require(
        fixture["fixture_only"] is True and fixture["canonical_contract"] is False,
        "trade fixture identity changed",
    )
    require(
        fixture["used_for_decision"] is False,
        "raw trade fixture cannot become decision data",
    )
    event_time = require_text(fixture["event_time"], "fixture event_time")
    receive_time = require_text(fixture["available_at"], "fixture available_at")
    trades = fixture.get("trades")
    require(isinstance(trades, list) and bool(trades), "trade fixture requires records")
    mapped = tuple(
        _map_trade(fixture, raw, event_time, receive_time) for raw in trades
    )
    require(
        len({item.trade_id for item in mapped}) == len(mapped),
        "trade fixture ids must be unique",
    )
    return mapped, checksum


def _map_trade(
    fixture: dict[str, Any],
    raw: object,
    event_time: str,
    receive_time: str,
) -> TimestampedTradeV1:
    item = require_closed_mapping(
        raw,
        {"trade_id", "price", "quantity", "side"},
        "trade record",
    )
    return TimestampedTradeV1(
        source_id=require_text(fixture["source_id"], "source_id"),
        venue=require_text(fixture["venue"], "venue"),
        instrument_id=require_text(fixture["instrument_id"], "instrument_id"),
        market_type=require_text(fixture["market_type"], "market_type"),
        trade_id=require_text(item["trade_id"], "trade_id"),
        event_time=event_time,
        receive_time=receive_time,
        price=decimal_from_text(item["price"], "trade price"),
        quantity=decimal_from_text(item["quantity"], "trade quantity"),
        source_side=require_text(item["side"], "trade source side"),
    )


def _load_snapshot(root: Path, config: dict[str, Any]) -> OrderBookSnapshotV1:
    raw = load_json_object(
        root
        / require_text(
            config.get("order_book_snapshot_path"),
            "order_book_snapshot_path",
        )
    )
    body = dict(raw)
    checksum = body.pop("snapshot_checksum", None)
    require(checksum == EXPECTED_SNAPSHOT_CHECKSUM, "Lot 38 snapshot checksum changed")
    require(canonical_checksum(body) == checksum, "Lot 38 snapshot payload mismatch")
    bids = tuple(
        OrderBookLevelV1(
            decimal_from_text(item["price"], "bid price"),
            decimal_from_text(item["quantity"], "bid quantity", allow_zero=True),
        )
        for item in raw["bids"]
    )
    asks = tuple(
        OrderBookLevelV1(
            decimal_from_text(item["price"], "ask price"),
            decimal_from_text(item["quantity"], "ask quantity", allow_zero=True),
        )
        for item in raw["asks"]
    )
    return OrderBookSnapshotV1(
        source_id=raw["source_id"],
        venue=raw["venue"],
        instrument_id=raw["instrument_id"],
        market_type=raw["market_type"],
        event_time=raw["event_time"],
        receive_time=raw["receive_time"],
        sequence_id=raw["sequence_id"],
        sequence_anchor=raw["sequence_anchor"],
        venue_state=raw["venue_state"],
        bids=bids,
        asks=asks,
        source_bid_depth=raw["source_bid_depth"],
        source_ask_depth=raw["source_ask_depth"],
        normalized_bid_depth=raw["normalized_bid_depth"],
        normalized_ask_depth=raw["normalized_ask_depth"],
        published_bid_depth=raw["published_bid_depth"],
        published_ask_depth=raw["published_ask_depth"],
        snapshot_checksum=raw["snapshot_checksum"],
    )


def _confidence_state(config: dict[str, Any]) -> AggressorConfidenceStateV1:
    base = AggressorConfidenceStateV1(
        policy_version=require_text(config["confidence_version"], "confidence_version"),
        semantics=CONFIDENCE_SEMANTICS,
        quote_test_confidence=decimal_from_text(
            config["quote_test_confidence"],
            "quote_test_confidence",
            allow_zero=True,
        ),
        tick_rule_confidence=decimal_from_text(
            config["tick_rule_confidence"],
            "tick_rule_confidence",
            allow_zero=True,
        ),
        unknown_confidence=decimal_from_text(
            config["unknown_confidence"],
            "unknown_confidence",
            allow_zero=True,
        ),
        confidence_checksum=ZERO_SHA256,
    )
    return replace(
        base,
        confidence_checksum=canonical_checksum(base.payload_without_checksum()),
    )


def _identity_matches(
    trade: TimestampedTradeV1,
    snapshot: OrderBookSnapshotV1,
) -> None:
    require(
        (trade.source_id, trade.venue, trade.instrument_id, trade.market_type)
        == (
            snapshot.source_id,
            snapshot.venue,
            snapshot.instrument_id,
            snapshot.market_type,
        ),
        "trade and quote identity mismatch",
    )


def _quote_usable(
    trade: TimestampedTradeV1,
    snapshot: OrderBookSnapshotV1,
    max_age_us: int,
) -> tuple[bool, str]:
    _identity_matches(trade, snapshot)
    if parse_utc_timestamp(
        snapshot.receive_time,
        "quote receive_time",
    ) > parse_utc_timestamp(trade.receive_time, "trade receive_time"):
        return False, "FUTURE_QUOTE_FORBIDDEN"
    if duration_us(snapshot.receive_time, trade.receive_time) > max_age_us:
        return False, "STALE_QUOTE_UNKNOWN"
    if snapshot.venue_state == "LOCKED":
        return False, "LOCKED_QUOTE_UNKNOWN"
    return True, "QUOTE_CAUSALLY_USABLE"


def classify_trade(
    trade: TimestampedTradeV1,
    snapshot: OrderBookSnapshotV1 | None,
    previous_trade: TimestampedTradeV1 | None,
    *,
    max_quote_age_us: int,
    confidence: AggressorConfidenceStateV1,
    tick_rule_fallback: bool,
) -> ClassifiedTradeV1:
    if snapshot is not None:
        usable, reason = _quote_usable(trade, snapshot, max_quote_age_us)
        if not usable:
            return _unknown(trade, snapshot.snapshot_checksum, reason, confidence)
        best_bid, best_ask = snapshot.bids[0].price, snapshot.asks[0].price
        if trade.price >= best_ask:
            return _classified(
                trade,
                "BUY_AGGRESSOR",
                "QUOTE_TEST",
                confidence.quote_test_confidence,
                snapshot.snapshot_checksum,
                "TRADE_AT_OR_ABOVE_ASK",
            )
        if trade.price <= best_bid:
            return _classified(
                trade,
                "SELL_AGGRESSOR",
                "QUOTE_TEST",
                confidence.quote_test_confidence,
                snapshot.snapshot_checksum,
                "TRADE_AT_OR_BELOW_BID",
            )
        return _unknown(
            trade,
            snapshot.snapshot_checksum,
            "TRADE_INSIDE_SPREAD_UNKNOWN",
            confidence,
        )
    if not tick_rule_fallback or previous_trade is None:
        return _unknown(
            trade,
            ZERO_SHA256,
            "QUOTE_UNAVAILABLE_NO_FALLBACK_EVIDENCE",
            confidence,
        )
    require(
        parse_utc_timestamp(previous_trade.receive_time, "previous receive_time")
        <= parse_utc_timestamp(trade.receive_time, "trade receive_time"),
        "tick-rule previous trade cannot be future",
    )
    if trade.price > previous_trade.price:
        return _classified(
            trade,
            "BUY_AGGRESSOR",
            "TICK_RULE",
            confidence.tick_rule_confidence,
            ZERO_SHA256,
            "QUOTE_UNAVAILABLE_TICK_UP",
        )
    if trade.price < previous_trade.price:
        return _classified(
            trade,
            "SELL_AGGRESSOR",
            "TICK_RULE",
            confidence.tick_rule_confidence,
            ZERO_SHA256,
            "QUOTE_UNAVAILABLE_TICK_DOWN",
        )
    return _unknown(
        trade,
        ZERO_SHA256,
        "QUOTE_UNAVAILABLE_ZERO_TICK_UNKNOWN",
        confidence,
    )


def _classified(
    trade: TimestampedTradeV1,
    side: str,
    method: str,
    confidence_value: Decimal,
    quote_checksum: str,
    reason: str,
) -> ClassifiedTradeV1:
    return ClassifiedTradeV1(
        trade,
        side,
        method,
        confidence_value,
        "lot44-aggressor-confidence-v1",
        quote_checksum,
        (reason, "PARTICIPANT_INTENT_NOT_ASSERTED"),
    )


def _unknown(
    trade: TimestampedTradeV1,
    quote_checksum: str,
    reason: str,
    confidence: AggressorConfidenceStateV1,
) -> ClassifiedTradeV1:
    return ClassifiedTradeV1(
        trade,
        "UNKNOWN",
        "NONE",
        confidence.unknown_confidence,
        confidence.policy_version,
        quote_checksum,
        (reason, "UNKNOWN_VOLUME_PRESERVED"),
    )


def _volume(items: tuple[ClassifiedTradeV1, ...]) -> Decimal:
    return sum((item.trade.quantity for item in items), Decimal(0))


def _metrics(items: tuple[ClassifiedTradeV1, ...]) -> Lot44MetricsV1:
    buy = tuple(
        item for item in items if item.aggressor_classification == "BUY_AGGRESSOR"
    )
    sell = tuple(
        item for item in items if item.aggressor_classification == "SELL_AGGRESSOR"
    )
    unknown = tuple(
        item for item in items if item.aggressor_classification == "UNKNOWN"
    )
    total = _volume(items)
    buy_volume = _volume(buy)
    sell_volume = _volume(sell)
    unknown_volume = _volume(unknown)
    return Lot44MetricsV1(
        len(items),
        len(buy),
        len(sell),
        len(unknown),
        total,
        buy_volume,
        sell_volume,
        unknown_volume,
        unknown_volume / total,
    )


def build_lot44_artifacts(
    root: Path,
    *,
    code_commit: str,
) -> tuple[
    TradesAggressorClassificationSchemaStateV1,
    TradesAggressorClassificationSchemaAuditV1,
]:
    config = load_json_object(root / CONFIG_PATH)
    _validate_config(config)
    _verify_gate(root, config)
    trades, trade_checksum = _load_trade_fixture(root, config)
    snapshot = _load_snapshot(root, config)
    confidence = _confidence_state(config)
    max_age = require_integer(
        config["max_quote_age_us"],
        "max_quote_age_us",
        minimum=1,
    )
    classified: list[ClassifiedTradeV1] = []
    for index, trade in enumerate(trades):
        previous = trades[index - 1] if index else None
        classified.append(
            classify_trade(
                trade,
                snapshot,
                previous,
                max_quote_age_us=max_age,
                confidence=confidence,
                tick_rule_fallback=config[
                    "tick_rule_fallback_when_quote_unavailable"
                ],
            )
        )
    items = tuple(classified)
    metrics = _metrics(items)
    generated_at = require_text(config["generated_at"], "generated_at")
    receive_time = max(item.trade.receive_time for item in items)
    event_time = max(item.trade.event_time for item in items)
    lineage = Lot44LineageEnvelopeV1(
        require_text(config["lineage_id"], "lineage_id"),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT43_STATE,
        EXPECTED_LOT43_AUDIT,
        EXPECTED_LOT43_RESILIENCE,
        EXPECTED_LOT43_POST_MERGE,
        trade_checksum,
        snapshot.snapshot_checksum,
        receive_time,
    )
    context = Lot44RunContextV1(
        require_text(config["run_id"], "run_id"),
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        require_text(config["config_version"], "config_version"),
        code_commit,
        require_text(config["correlation_id"], "correlation_id"),
    )
    state0 = TradesAggressorClassificationSchemaStateV1(
        context,
        lineage,
        event_time,
        receive_time,
        generated_at,
        "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY",
        items,
        confidence,
        metrics,
        COMMON_REASON_CODES,
        lot44_safety(),
        ZERO_SHA256,
    )
    state = replace(
        state0,
        output_checksum=canonical_checksum(state0.payload_without_checksum()),
    )
    config_checksum = file_checksum(root / CONFIG_PATH)
    audit0 = TradesAggressorClassificationSchemaAuditV1(
        code_commit,
        state.output_checksum,
        config_checksum,
        EXPECTED_GATE_CHECKSUM,
        trade_checksum,
        snapshot.snapshot_checksum,
        state.validation_state,
        lot44_safety(),
        ZERO_SHA256,
    )
    audit = replace(
        audit0,
        audit_checksum=canonical_checksum(audit0.payload_without_checksum()),
    )
    return state, audit


def write_lot44_artifacts(
    root: Path,
    *,
    code_commit: str,
) -> tuple[
    TradesAggressorClassificationSchemaStateV1,
    TradesAggressorClassificationSchemaAuditV1,
]:
    state, audit = build_lot44_artifacts(root, code_commit=code_commit)
    atomic_write_json(root / STATE_PATH, state.to_dict())
    atomic_write_json(root / AUDIT_PATH, audit.to_dict())
    atomic_write_json(root / CONFIDENCE_PATH, state.confidence_state.to_dict())
    return state, audit
