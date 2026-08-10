from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, InvalidOperation
from itertools import pairwise
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)

from .book_integrity_desynchronization_detector_models import (
    VALIDATION_STATE,
    BookHealthComponentV1,
    BookHealthVetoV1,
    BookIntegrityDesynchronizationDetectorAuditV1,
    BookIntegrityDesynchronizationDetectorStateV1,
    BookIntegrityStateV1,
    Lot40LineageEnvelopeV1,
    Lot40MetricsV1,
    Lot40RunContextV1,
)
from .book_integrity_desynchronization_detector_validation import (
    COMPONENT_NAMES,
    BookIntegrityValidationError,
    decimal_from_text,
    duration_us,
    lot40_safety,
    parse_utc_timestamp,
    require_integer,
    require_text,
    validate_causal_times,
)

CONFIG_PATH = Path("config/microstructure/book_integrity_desynchronization_detector_v1.json")
STATE_PATH = Path("data/audit/book_integrity_desynchronization_detector_lot40.json")
AUDIT_PATH = Path("data/audit/book_integrity_desynchronization_detector_audit_lot40.json")
INTEGRITY_PATH = Path("data/audit/book_integrity_state_lot40.json")
VETO_PATH = Path("data/audit/book_health_veto_lot40.json")
EXPECTED_GATE_CHECKSUM = "23d9f0bdb71a2ed26cf3ef89e5be6237fd286a38944f9fed4c6b8f18d4106f18"
EXPECTED_LOT39_STATE = "d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0"
EXPECTED_LOT39_AUDIT = "1e29d0b8695a1b8825e1fc91728a6254ad93c689e1f961cfa424e6d5fed8ed41"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_LOT39_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"
ZERO_SHA256 = "0" * 64
CRITICAL_COMPONENTS = {
    "SEQUENCE_CONTINUITY",
    "CROSSED_LOCKED_STATE",
    "CHECKSUM_INTEGRITY",
    "LEVEL_MONOTONICITY",
}
COMPONENT_REASON_CODES = {
    "SEQUENCE_CONTINUITY": ("LOT40_SEQUENCE_CONTINUITY_OK", "LOT40_SEQUENCE_CONTINUITY_FAILED"),
    "CROSSED_LOCKED_STATE": ("LOT40_BOOK_OPEN_UNCROSSED", "LOT40_CROSSED_OR_LOCKED_BOOK"),
    "FRESHNESS": ("LOT40_BOOK_FRESH", "LOT40_BOOK_STALE"),
    "CHECKSUM_INTEGRITY": ("LOT40_BOOK_CHECKSUM_VALID", "LOT40_BOOK_CHECKSUM_INVALID"),
    "DEPTH_INTEGRITY": ("LOT40_DEPTH_INTEGRITY_OK", "LOT40_DEPTH_COLLAPSE_DETECTED"),
    "LEVEL_MONOTONICITY": ("LOT40_LEVEL_MONOTONICITY_OK", "LOT40_LEVEL_MONOTONICITY_FAILED"),
}


def _validate_config(config: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version",
        "config_version",
        "run_id",
        "correlation_id",
        "lineage_id",
        "generated_at",
        "decision_time",
        "max_stale_age_us",
        "minimum_bid_depth_levels",
        "minimum_ask_depth_levels",
        "trade_health_threshold",
        "system_health_threshold",
        "system_threshold_consequence",
        "critical_failure_consequence",
        "component_weights",
        "entry_gate_path",
        "lot39_lifecycle_overlay_path",
        "lot39_state_path",
        "lot39_audit_path",
        "lot39_reconstructed_book_path",
        "lot39_delta_fixture_path",
    }
    if set(config) != expected_fields:
        raise BookIntegrityValidationError("Lot 40 config fields differ from contract")
    if config.get("schema_version") != "lot40-book-integrity-config-v1":
        raise BookIntegrityValidationError("Lot 40 config schema changed")
    if config.get("config_version") != "lot40-book-integrity-config-v1":
        raise BookIntegrityValidationError("Lot 40 config version changed")
    parse_utc_timestamp(require_text(config.get("generated_at"), "generated_at"), "generated_at")
    parse_utc_timestamp(require_text(config.get("decision_time"), "decision_time"), "decision_time")
    require_integer(config.get("max_stale_age_us"), "max_stale_age_us", minimum=1)
    require_integer(config.get("minimum_bid_depth_levels"), "minimum_bid_depth_levels", minimum=1)
    require_integer(config.get("minimum_ask_depth_levels"), "minimum_ask_depth_levels", minimum=1)
    _validate_policy(config)


def _validate_policy(config: dict[str, Any]) -> None:
    trade = decimal_from_text(config.get("trade_health_threshold"), "trade_health_threshold")
    system = decimal_from_text(config.get("system_health_threshold"), "system_health_threshold")
    if not Decimal("0") <= system <= trade <= Decimal("100"):
        raise BookIntegrityValidationError("Lot 40 threshold ordering invalid")
    if config.get("system_threshold_consequence") != "PAUSE":
        raise BookIntegrityValidationError("Lot 40 system threshold consequence changed")
    if config.get("critical_failure_consequence") != "BLOCK":
        raise BookIntegrityValidationError("Lot 40 critical consequence changed")
    weights = config.get("component_weights")
    if not isinstance(weights, dict) or set(weights) != COMPONENT_NAMES:
        raise BookIntegrityValidationError("Lot 40 component weight set changed")
    parsed = [
        decimal_from_text(weights[name], f"weight {name}", allow_zero=False)
        for name in sorted(weights)
    ]
    if sum(parsed, Decimal("0")) != Decimal("100"):
        raise BookIntegrityValidationError("Lot 40 component weights must total 100")


def _verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    checksum = body.pop(field, None)
    if checksum != expected or canonical_checksum(body) != checksum:
        raise BookIntegrityValidationError(f"{label} checksum changed")


def _verify_gate(root: Path, config: dict[str, Any]) -> None:
    gate = load_json_object(
        root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    )
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    if checksum != EXPECTED_GATE_CHECKSUM or canonical_checksum(body) != checksum:
        raise BookIntegrityValidationError("Lot 40 entry gate checksum changed")
    expected = {
        "gate_status": "GO_LOT40_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT40",
        "target_lot": 40,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_started": False,
        "next_lot": 41,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise BookIntegrityValidationError("Lot 40 gate does not authorize this scope")
    if gate.get("safety") != lot40_safety():
        raise BookIntegrityValidationError("Lot 40 gate safety boundary changed")


def _load_configured(root: Path, config: dict[str, Any], field: str) -> dict[str, Any]:
    return load_json_object(root / require_text(config.get(field), field))


def _verify_lot39(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    overlay = _load_configured(root, config, "lot39_lifecycle_overlay_path")
    if overlay.get("latest_implemented_lot") != 39:
        raise BookIntegrityValidationError("Lot 40 requires audited lifecycle latest lot 39")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise BookIntegrityValidationError("Lot 39 lifecycle lot map missing")
    lot39 = lots.get("39")
    if not isinstance(lot39, dict) or lot39.get("status") != (
        "IMPLEMENTED_VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY"
    ):
        raise BookIntegrityValidationError("Lot 39 lifecycle status changed")
    if lots.get("40") != {"implementation_started": False, "status": "PLANNED_LOCKED"}:
        raise BookIntegrityValidationError("historical Lot 40 lifecycle lock changed")
    state = _load_configured(root, config, "lot39_state_path")
    audit = _load_configured(root, config, "lot39_audit_path")
    book = _load_configured(root, config, "lot39_reconstructed_book_path")
    _verify_checksum(state, "output_checksum", EXPECTED_LOT39_STATE, "Lot 39 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_LOT39_AUDIT, "Lot 39 audit")
    _verify_checksum(book, "book_checksum", EXPECTED_LOT39_BOOK, "Lot 39 book")
    fixture_path = root / require_text(
        config.get("lot39_delta_fixture_path"), "lot39_delta_fixture_path"
    )
    if file_checksum(fixture_path) != EXPECTED_LOT39_FIXTURE:
        raise BookIntegrityValidationError("Lot 39 delta fixture changed")
    if state.get("reconstructed_book") != book or state.get("sequence_gap_event") is not None:
        raise BookIntegrityValidationError("Lot 39 state/book linkage changed")
    if (
        state.get("synchronization_state") != "SYNCED"
        or audit.get("synchronization_state") != "SYNCED"
    ):
        raise BookIntegrityValidationError("Lot 40 requires certified SYNCED Lot 39 book")
    if audit.get("state_output_checksum") != EXPECTED_LOT39_STATE:
        raise BookIntegrityValidationError("Lot 39 audit/state linkage changed")
    if audit.get("reconstructed_book_checksum") != EXPECTED_LOT39_BOOK:
        raise BookIntegrityValidationError("Lot 39 audit/book linkage changed")
    return book


def _parse_levels(raw: Any) -> tuple[tuple[tuple[Decimal, Decimal], ...], bool]:
    if not isinstance(raw, list) or not raw:
        return (), False
    parsed: list[tuple[Decimal, Decimal]] = []
    valid = True
    for level in raw:
        if not isinstance(level, dict) or set(level) != {"price", "quantity"}:
            return (), False
        try:
            price = Decimal(level["price"])
            quantity = Decimal(level["quantity"])
        except (InvalidOperation, TypeError):
            return (), False
        if not price.is_finite() or not quantity.is_finite() or price <= 0 or quantity < 0:
            valid = False
        parsed.append((price, quantity))
    return tuple(parsed), valid


def _strictly_monotonic(
    levels: tuple[tuple[Decimal, Decimal], ...], *, descending: bool
) -> bool:
    prices = tuple(price for price, _ in levels)
    if len(set(prices)) != len(prices):
        return False
    pairs = pairwise(prices)
    if descending:
        return all(left > right for left, right in pairs)
    return all(left < right for left, right in pairs)


def _sequence_continuous(book: dict[str, Any]) -> bool:
    base = book.get("base_sequence_id")
    sequence = book.get("sequence_id")
    applied = book.get("applied_delta_count")
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (base, sequence, applied)
    ):
        return False
    assert isinstance(base, int) and isinstance(sequence, int) and isinstance(applied, int)
    return (
        book.get("synchronization_state") == "SYNCED"
        and applied >= 1
        and sequence > base
        and sequence == base + applied
    )


def _checksum_valid(book: dict[str, Any]) -> bool:
    checksum = book.get("book_checksum")
    if not isinstance(checksum, str) or len(checksum) != 64:
        return False
    if any(character not in "0123456789abcdef" for character in checksum):
        return False
    body = dict(book)
    body.pop("book_checksum", None)
    return canonical_checksum(body) == checksum


def _stale_age_us(book: dict[str, Any], config: dict[str, Any]) -> int:
    received = parse_utc_timestamp(
        require_text(book.get("receive_time"), "book receive_time"), "book receive_time"
    )
    decision = parse_utc_timestamp(
        require_text(config.get("decision_time"), "decision_time"), "decision_time"
    )
    return duration_us(received, decision)


def _component(
    name: str,
    passed: bool,
    weight: Decimal,
) -> BookHealthComponentV1:
    success_reason, failure_reason = COMPONENT_REASON_CODES[name]
    return BookHealthComponentV1(
        name,
        passed,
        name in CRITICAL_COMPONENTS,
        weight,
        weight if passed else Decimal("0"),
        success_reason if passed else failure_reason,
    )


def _health_components(
    book: dict[str, Any],
    config: dict[str, Any],
    stale_age: int,
) -> tuple[BookHealthComponentV1, ...]:
    bids, bids_valid = _parse_levels(book.get("bids"))
    asks, asks_valid = _parse_levels(book.get("asks"))
    levels_valid = bids_valid and asks_valid
    monotonic = (
        levels_valid
        and _strictly_monotonic(bids, descending=True)
        and _strictly_monotonic(asks, descending=False)
    )
    open_uncrossed = levels_valid and bool(bids) and bool(asks) and bids[0][0] < asks[0][0]
    min_bids = require_integer(
        config.get("minimum_bid_depth_levels"), "minimum_bid_depth_levels", minimum=1
    )
    min_asks = require_integer(
        config.get("minimum_ask_depth_levels"), "minimum_ask_depth_levels", minimum=1
    )
    max_age = require_integer(config.get("max_stale_age_us"), "max_stale_age_us", minimum=1)
    passed = {
        "SEQUENCE_CONTINUITY": _sequence_continuous(book),
        "CROSSED_LOCKED_STATE": open_uncrossed,
        "FRESHNESS": stale_age <= max_age,
        "CHECKSUM_INTEGRITY": _checksum_valid(book),
        "DEPTH_INTEGRITY": len(bids) >= min_bids and len(asks) >= min_asks,
        "LEVEL_MONOTONICITY": monotonic,
    }
    weights = config.get("component_weights")
    if not isinstance(weights, dict):
        raise BookIntegrityValidationError("Lot 40 component weights missing")
    return tuple(
        _component(
            name,
            passed[name],
            decimal_from_text(weights[name], f"weight {name}", allow_zero=False),
        )
        for name in (
            "SEQUENCE_CONTINUITY",
            "CROSSED_LOCKED_STATE",
            "FRESHNESS",
            "CHECKSUM_INTEGRITY",
            "DEPTH_INTEGRITY",
            "LEVEL_MONOTONICITY",
        )
    )


def _health_status(components: tuple[BookHealthComponentV1, ...]) -> str:
    if any(component.critical and not component.passed for component in components):
        return "CRITICAL"
    if any(not component.passed for component in components):
        return "DEGRADED"
    return "HEALTHY"


def _consequence(
    components: tuple[BookHealthComponentV1, ...],
    score: Decimal,
    system_threshold: Decimal,
    trade_threshold: Decimal,
) -> tuple[str, bool]:
    critical = any(component.critical and not component.passed for component in components)
    if critical:
        return "BLOCK", True
    if score < system_threshold:
        return "PAUSE", False
    if score < trade_threshold:
        return "WAIT", False
    return "NONE", False


def evaluate_book_integrity(
    book: dict[str, Any],
    config: dict[str, Any],
) -> tuple[BookIntegrityStateV1, BookHealthVetoV1]:
    _validate_config(config)
    event_time = require_text(book.get("event_time"), "book event_time")
    receive_time = require_text(book.get("receive_time"), "book receive_time")
    decision_time = require_text(config.get("decision_time"), "decision_time")
    generated_at = require_text(config.get("generated_at"), "generated_at")
    validate_causal_times(event_time, receive_time, decision_time, generated_at)
    stale_age = _stale_age_us(book, config)
    components = _health_components(book, config, stale_age)
    score = sum((component.score for component in components), Decimal("0"))
    health_status = _health_status(components)
    bids, _ = _parse_levels(book.get("bids"))
    asks, _ = _parse_levels(book.get("asks"))
    crossed = bool(bids and asks and bids[0][0] > asks[0][0])
    locked = bool(bids and asks and bids[0][0] == asks[0][0])
    checksum_valid = next(
        component.passed for component in components if component.name == "CHECKSUM_INTEGRITY"
    )
    monotonic = next(
        component.passed for component in components if component.name == "LEVEL_MONOTONICITY"
    )
    reason_codes = (
        "LOT40_BOOK_INTEGRITY_EVALUATED",
        f"LOT40_HEALTH_{health_status}",
        "LOT41_REMAINS_LOCKED",
    )
    integrity = BookIntegrityStateV1(
        source_id=require_text(book.get("source_id"), "source_id"),
        venue=require_text(book.get("venue"), "venue"),
        instrument_id=require_text(book.get("instrument_id"), "instrument_id"),
        market_type=require_text(book.get("market_type"), "market_type"),
        event_time=event_time,
        receive_time=receive_time,
        decision_time=decision_time,
        sequence_id=require_integer(book.get("sequence_id"), "sequence_id"),
        synchronization_state=require_text(
            book.get("synchronization_state"), "synchronization_state"
        ),
        stale_age_us=stale_age,
        bid_depth_levels=len(bids),
        ask_depth_levels=len(asks),
        crossed=crossed,
        locked=locked,
        checksum_valid=checksum_valid,
        level_monotonicity_valid=monotonic,
        health_status=health_status,
        book_health_score=score,
        components=components,
        reason_codes=reason_codes,
        integrity_checksum=ZERO_SHA256,
    )
    integrity = replace(
        integrity,
        integrity_checksum=canonical_checksum(integrity.payload_without_checksum()),
    )
    trade_threshold = decimal_from_text(
        config.get("trade_health_threshold"), "trade_health_threshold"
    )
    system_threshold = decimal_from_text(
        config.get("system_health_threshold"), "system_health_threshold"
    )
    consequence, critical = _consequence(components, score, system_threshold, trade_threshold)
    veto_reasons = (
        {
            "NONE": "LOT40_NO_HEALTH_VETO",
            "WAIT": "LOT40_TRADE_HEALTH_WAIT",
            "PAUSE": "LOT40_SYSTEM_HEALTH_PAUSE",
            "BLOCK": "LOT40_CRITICAL_BOOK_HEALTH_BLOCK",
        }[consequence],
        "LOT41_REMAINS_LOCKED",
    )
    veto = BookHealthVetoV1(
        consequence=consequence,
        veto_active=consequence != "NONE",
        critical_veto_active=critical,
        trade_health_threshold=trade_threshold,
        system_health_threshold=system_threshold,
        critical_failure_consequence=require_text(
            config.get("critical_failure_consequence"), "critical_failure_consequence"
        ),
        system_threshold_consequence=require_text(
            config.get("system_threshold_consequence"), "system_threshold_consequence"
        ),
        book_health_score=score,
        reason_codes=veto_reasons,
        veto_checksum=ZERO_SHA256,
    )
    veto = replace(veto, veto_checksum=canonical_checksum(veto.payload_without_checksum()))
    return integrity, veto


def _build_context(config: dict[str, Any], code_commit: str) -> Lot40RunContextV1:
    return Lot40RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )


def _build_lineage(config: dict[str, Any], available_at: str) -> Lot40LineageEnvelopeV1:
    return Lot40LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT39_STATE,
        EXPECTED_LOT39_AUDIT,
        EXPECTED_LOT39_BOOK,
        EXPECTED_LOT39_FIXTURE,
        available_at,
    )


def _build_state(
    config: dict[str, Any],
    code_commit: str,
    integrity: BookIntegrityStateV1,
    veto: BookHealthVetoV1,
) -> BookIntegrityDesynchronizationDetectorStateV1:
    failed = sum(1 for component in integrity.components if not component.passed)
    critical_failed = sum(
        1 for component in integrity.components if component.critical and not component.passed
    )
    metrics = Lot40MetricsV1(
        len(integrity.components),
        failed,
        critical_failed,
        integrity.bid_depth_levels,
        integrity.ask_depth_levels,
        integrity.stale_age_us,
    )
    state = BookIntegrityDesynchronizationDetectorStateV1(
        _build_context(config, code_commit),
        _build_lineage(config, integrity.receive_time),
        integrity.event_time,
        integrity.receive_time,
        integrity.decision_time,
        require_text(config.get("generated_at"), "generated_at"),
        VALIDATION_STATE,
        integrity,
        veto,
        metrics,
        (
            "LOT40_OFFLINE_BOOK_INTEGRITY_VALIDATED",
            f"LOT40_CONSEQUENCE_{veto.consequence}",
            "LOT41_REMAINS_LOCKED",
        ),
        lot40_safety(),
        ZERO_SHA256,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    root: Path,
    code_commit: str,
    state: BookIntegrityDesynchronizationDetectorStateV1,
) -> BookIntegrityDesynchronizationDetectorAuditV1:
    audit = BookIntegrityDesynchronizationDetectorAuditV1(
        code_commit,
        file_checksum(root / CONFIG_PATH),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_LOT39_STATE,
        EXPECTED_LOT39_AUDIT,
        EXPECTED_LOT39_BOOK,
        EXPECTED_LOT39_FIXTURE,
        state.output_checksum,
        state.book_integrity.integrity_checksum,
        state.book_health_veto.veto_checksum,
        state.book_integrity.health_status,
        state.book_health_veto.consequence,
        lot40_safety(),
        ZERO_SHA256,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def build_lot40_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[
    BookIntegrityDesynchronizationDetectorStateV1,
    BookIntegrityDesynchronizationDetectorAuditV1,
]:
    config = load_json_object(root / CONFIG_PATH)
    _validate_config(config)
    _verify_gate(root, config)
    book = _verify_lot39(root, config)
    integrity, veto = evaluate_book_integrity(book, config)
    state = _build_state(config, code_commit, integrity, veto)
    return state, _build_audit(root, code_commit, state)


def write_lot40_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[
    BookIntegrityDesynchronizationDetectorStateV1,
    BookIntegrityDesynchronizationDetectorAuditV1,
]:
    state, audit = build_lot40_artifacts(root, code_commit)
    atomic_write_json(root / STATE_PATH, state.to_dict())
    atomic_write_json(root / AUDIT_PATH, audit.to_dict())
    atomic_write_json(root / INTEGRITY_PATH, state.book_integrity.to_dict())
    atomic_write_json(root / VETO_PATH, state.book_health_veto.to_dict())
    return state, audit


__all__ = [
    "AUDIT_PATH",
    "CONFIG_PATH",
    "INTEGRITY_PATH",
    "STATE_PATH",
    "VETO_PATH",
    "build_lot40_artifacts",
    "evaluate_book_integrity",
    "write_lot40_artifacts",
]
