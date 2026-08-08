from __future__ import annotations

from collections import Counter
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from .candle_trade_book_reconciliation_models import (
    CLASSIFICATIONS,
    ENTITY_TYPES,
    SOURCE_OF_TRUTH,
    CandleTradeBookReconciliationAuditV1,
    CandleTradeBookReconciliationStateV1,
    Lot35LineageEnvelopeV1,
    Lot35MetricsV1,
    Lot35RunContextV1,
    ReconciliationDeltaV1,
    ReconciliationReportV1,
    ReconciliationSnapshotV1,
    ReconciliationVetoV1,
)
from .candle_trade_book_reconciliation_validation import (
    ReconciliationError,
    absolute_decimal_delta,
    canonical_decimal,
    decimal_from_string,
    duration_us,
    lot35_safety,
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_text,
)
from .market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)

EXPECTED_GATE_CHECKSUM = "e3ca9847c39a9ab8a043639cda556308506e9d5a497eb7821d3b962278c507ab"
EXPECTED_LOT34_STATE_CHECKSUM = "bc66816383ddf141016ad66796cc5dd4ad3442cd3594d96ad1f7db13d7c6bc01"
EXPECTED_LOT34_AUDIT_CHECKSUM = "cd4410a2ea9ef6cdc061caf5115d908d03575e219eb9f4da402bff1712f6c7ce"
SNAPSHOT_FIELDS = {
    "record_id",
    "identifier",
    "quantity",
    "price",
    "fee",
    "balance",
    "position",
    "event_time",
}
RECORD_FIELDS = {
    "reconciliation_id",
    "entity_type",
    "source_of_truth",
    "primary",
    "secondary",
}
CONFIG_FIELDS = {
    "schema_version",
    "config_version",
    "run_id",
    "correlation_id",
    "lineage_id",
    "event_time",
    "available_at",
    "generated_at",
    "tolerance_version",
    "tolerances",
    "critical_multiplier",
    "records",
}
TOLERANCE_FIELDS = {
    "quantity_abs",
    "price_abs",
    "fee_abs",
    "balance_abs",
    "position_abs",
    "timestamp_us",
}
LOT35_REASON_CODES = (
    "LOT35_ENTRY_GATE_VERIFIED",
    "LOT34_DATA_QUALITY_LINEAGE_VERIFIED",
    "RECONCILIATION_DELTAS_COMPUTED_EXACTLY",
    "VERSIONED_TOLERANCES_APPLIED",
    "SOURCE_OF_TRUTH_RECORDED_EXPLICITLY",
    "RECONCILIATION_VETO_EVALUATED_FAIL_CLOSED",
    "RAW_DATA_IMMUTABILITY_PRESERVED",
    "EXTERNAL_CONNECTIVITY_DISABLED",
    "LOT36_REMAINS_LOCKED",
)


def _verify_checksum(payload: dict[str, Any], field: str, expected: str) -> None:
    body = dict(payload)
    checksum = body.pop(field, None)
    if checksum != expected or canonical_checksum(body) != checksum:
        raise ReconciliationError(f"certified checksum mismatch: {field}")


def _verify_gate(gate: dict[str, Any]) -> None:
    _verify_checksum(gate, "output_checksum", EXPECTED_GATE_CHECKSUM)
    expected = {
        "gate_status": "GO_LOT35_IMPLEMENTATION_ENTRY",
        "target_lot": 35,
        "current_version": "0.34.0",
        "human_decision": "APPROVED_START_LOT35",
        "implementation_started": False,
        "owner": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "next_lot": 36,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise ReconciliationError("Lot 35 gate does not authorize implementation")
    if gate.get("safety") != lot35_safety():
        raise ReconciliationError("Lot 35 gate safety boundary changed")


def _verify_lot34_evidence(root: Path) -> None:
    state = load_json_object(root / "data/audit/market_data_quality_engine_lot34.json")
    audit = load_json_object(root / "data/audit/market_data_quality_engine_audit_lot34.json")
    anomalies = load_json_object(root / "data/audit/data_anomalies_lot34.json")
    veto = load_json_object(root / "data/audit/data_quality_veto_lot34.json")
    _verify_checksum(state, "output_checksum", EXPECTED_LOT34_STATE_CHECKSUM)
    _verify_checksum(audit, "audit_checksum", EXPECTED_LOT34_AUDIT_CHECKSUM)
    if audit.get("state_output_checksum") != EXPECTED_LOT34_STATE_CHECKSUM:
        raise ReconciliationError("Lot 34 audit/state lineage mismatch")
    if anomalies.get("records") != []:
        raise ReconciliationError("Lot 35 reference requires certified Lot 34 anomaly-free input")
    if veto.get("action") != "ALLOW_ANALYSIS":
        raise ReconciliationError("Lot 34 quality veto does not permit offline analysis")
    if state.get("raw_data_mutation_allowed") is not False:
        raise ReconciliationError("Lot 34 raw-data immutability changed")


def _validate_config_identity(config: dict[str, Any]) -> None:
    if set(config) != CONFIG_FIELDS:
        raise ReconciliationError("Lot 35 configuration fields differ")
    if config["schema_version"] != "candle-trade-book-reconciliation-config-v1":
        raise ReconciliationError("Lot 35 configuration schema changed")
    if config["config_version"] != "lot35-candle-trade-book-reconciliation-config-v1":
        raise ReconciliationError("Lot 35 configuration version changed")
    require_identifier(config["run_id"], "run_id")
    require_identifier(config["correlation_id"], "correlation_id")
    require_identifier(config["lineage_id"], "lineage_id")
    require_identifier(config["tolerance_version"], "tolerance_version")


def _validate_config_times(config: dict[str, Any]) -> None:
    event = parse_utc_timestamp(config["event_time"], "event_time")
    available = parse_utc_timestamp(config["available_at"], "available_at")
    generated = parse_utc_timestamp(config["generated_at"], "generated_at")
    if not event <= available <= generated:
        raise ReconciliationError("Lot 35 configuration violates causal availability")


def _validate_tolerances(config: dict[str, Any]) -> None:
    tolerances = config["tolerances"]
    if not isinstance(tolerances, dict) or set(tolerances) != TOLERANCE_FIELDS:
        raise ReconciliationError("Lot 35 tolerances differ from contract")
    for field in TOLERANCE_FIELDS - {"timestamp_us"}:
        value = decimal_from_string(tolerances[field], field)
        if value < Decimal("0"):
            raise ReconciliationError(f"{field} tolerance must be non-negative")
    require_integer(tolerances["timestamp_us"], "timestamp_us", minimum=0)
    require_integer(config["critical_multiplier"], "critical_multiplier", minimum=1)


def _validate_snapshot_shape(value: object, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != SNAPSHOT_FIELDS:
        raise ReconciliationError(f"{label} snapshot fields differ")
    ReconciliationSnapshotV1(**value)


def _validate_records(config: dict[str, Any]) -> None:
    records = config["records"]
    if not isinstance(records, list) or not records:
        raise ReconciliationError("Lot 35 requires reconciliation records")
    for record in records:
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            raise ReconciliationError("Lot 35 reconciliation record fields differ")
        require_identifier(record["reconciliation_id"], "reconciliation_id")
        if record["entity_type"] not in ENTITY_TYPES:
            raise ReconciliationError("unknown reconciliation entity type")
        if record["source_of_truth"] not in SOURCE_OF_TRUTH:
            raise ReconciliationError("unknown source-of-truth value")
        _validate_snapshot_shape(record["primary"], "primary")
        _validate_snapshot_shape(record["secondary"], "secondary")
        if record["primary"] is None and record["secondary"] is None:
            raise ReconciliationError("reconciliation cannot have two absent sources")


def _validate_config(config: dict[str, Any]) -> None:
    _validate_config_identity(config)
    _validate_config_times(config)
    _validate_tolerances(config)
    _validate_records(config)


def _snapshot(value: object) -> ReconciliationSnapshotV1 | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ReconciliationError("reconciliation snapshot must be an object")
    return ReconciliationSnapshotV1(**value)


def _delta(
    primary: ReconciliationSnapshotV1,
    secondary: ReconciliationSnapshotV1,
) -> ReconciliationDeltaV1:
    timestamp = duration_us(
        parse_utc_timestamp(primary.event_time, "primary.event_time"),
        parse_utc_timestamp(secondary.event_time, "secondary.event_time"),
    )
    return ReconciliationDeltaV1(
        canonical_decimal(absolute_decimal_delta(primary.quantity, secondary.quantity, "quantity")),
        canonical_decimal(absolute_decimal_delta(primary.price, secondary.price, "price")),
        canonical_decimal(absolute_decimal_delta(primary.fee, secondary.fee, "fee")),
        canonical_decimal(absolute_decimal_delta(primary.balance, secondary.balance, "balance")),
        canonical_decimal(absolute_decimal_delta(primary.position, secondary.position, "position")),
        timestamp,
    )


def _decimal_deltas(delta: ReconciliationDeltaV1) -> dict[str, Decimal]:
    return {
        "quantity_abs": decimal_from_string(delta.quantity_abs, "quantity_abs"),
        "price_abs": decimal_from_string(delta.price_abs, "price_abs"),
        "fee_abs": decimal_from_string(delta.fee_abs, "fee_abs"),
        "balance_abs": decimal_from_string(delta.balance_abs, "balance_abs"),
        "position_abs": decimal_from_string(delta.position_abs, "position_abs"),
    }


def _all_zero(delta: ReconciliationDeltaV1) -> bool:
    return all(value == Decimal("0") for value in _decimal_deltas(delta).values()) and delta.timestamp_us == 0


def _within_tolerance(
    delta: ReconciliationDeltaV1,
    config: dict[str, Any],
    factor: int,
) -> bool:
    tolerances = config["tolerances"]
    values = _decimal_deltas(delta)
    for field, value in values.items():
        limit = decimal_from_string(tolerances[field], field) * factor
        if value > limit:
            return False
    timestamp_limit = require_integer(tolerances["timestamp_us"], "timestamp_us", minimum=0)
    return delta.timestamp_us <= timestamp_limit * factor


def _base_classification(
    primary: ReconciliationSnapshotV1,
    secondary: ReconciliationSnapshotV1,
    delta: ReconciliationDeltaV1,
    config: dict[str, Any],
) -> tuple[str, tuple[str, ...]]:
    if primary.identifier != secondary.identifier:
        return "CRITICAL_DIVERGENCE", ("RECONCILIATION_IDENTIFIER_MISMATCH",)
    if _all_zero(delta):
        return "MATCH", ("RECONCILIATION_MATCH",)
    if _within_tolerance(delta, config, 1):
        return "TOLERATED_DIFF", ("RECONCILIATION_WITHIN_TOLERANCE",)
    multiplier = require_integer(config["critical_multiplier"], "critical_multiplier", minimum=1)
    if _within_tolerance(delta, config, multiplier):
        reasons = ["RECONCILIATION_MINOR_DIVERGENCE"]
        fee = decimal_from_string(delta.fee_abs, "fee_abs")
        fee_limit = decimal_from_string(config["tolerances"]["fee_abs"], "fee_abs")
        if fee > fee_limit:
            reasons.append("RECONCILIATION_FEE_DIFF_REQUIRES_PAUSE")
        return "MINOR_DIVERGENCE", tuple(reasons)
    return "CRITICAL_DIVERGENCE", ("RECONCILIATION_CRITICAL_DIVERGENCE",)


def _corrective_action(classification: str) -> str:
    if classification in {"MATCH", "TOLERATED_DIFF"}:
        return "NONE"
    if classification == "MINOR_DIVERGENCE":
        return "REVIEW_AND_PAUSE"
    if classification == "CRITICAL_DIVERGENCE":
        return "MANUAL_RECONCILIATION_REQUIRED"
    raise ReconciliationError("unexpected reconciliation classification")


def _build_report(
    record: dict[str, Any],
    duplicate: bool,
    config: dict[str, Any],
) -> ReconciliationReportV1:
    primary = _snapshot(record["primary"])
    secondary = _snapshot(record["secondary"])
    source_of_truth = require_text(record["source_of_truth"], "source_of_truth")
    reasons: tuple[str, ...]
    if primary is None or secondary is None:
        orphan = True
        delta = None
        classification = "CRITICAL_DIVERGENCE"
        reasons = ("RECONCILIATION_ORPHAN",)
    else:
        orphan = False
        delta = _delta(primary, secondary)
        if source_of_truth == "UNKNOWN":
            classification = "CRITICAL_DIVERGENCE"
            reasons = ("RECONCILIATION_SOURCE_OF_TRUTH_UNKNOWN",)
        else:
            classification, base_reasons = _base_classification(
                primary,
                secondary,
                delta,
                config,
            )
            if duplicate:
                if classification == "CRITICAL_DIVERGENCE":
                    reasons = (*base_reasons, "RECONCILIATION_DUPLICATE")
                else:
                    classification = "MINOR_DIVERGENCE"
                    reasons = ("RECONCILIATION_DUPLICATE",)
            else:
                reasons = base_reasons
    if classification not in CLASSIFICATIONS:
        raise ReconciliationError("classification escaped contract")
    return ReconciliationReportV1(
        require_identifier(record["reconciliation_id"], "reconciliation_id"),
        require_text(record["entity_type"], "entity_type"),
        source_of_truth,
        None if primary is None else primary.record_id,
        None if secondary is None else secondary.record_id,
        classification,
        delta,
        require_identifier(config["tolerance_version"], "tolerance_version"),
        duplicate,
        orphan,
        _corrective_action(classification),
        reasons,
    )


def _report_sort_key(report: ReconciliationReportV1) -> tuple[str, str, str, str]:
    return (
        report.reconciliation_id,
        report.primary_record_id or "",
        report.secondary_record_id or "",
        canonical_checksum(report.to_dict()),
    )


def build_reconciliation_reports(config: dict[str, Any]) -> tuple[ReconciliationReportV1, ...]:
    _validate_config(config)
    identifiers = [record["reconciliation_id"] for record in config["records"]]
    counts = Counter(identifiers)
    reports = [
        _build_report(record, counts[record["reconciliation_id"]] > 1, config)
        for record in config["records"]
    ]
    return tuple(sorted(reports, key=_report_sort_key))


def _build_veto(reports: tuple[ReconciliationReportV1, ...]) -> ReconciliationVetoV1:
    minor = sum(report.classification == "MINOR_DIVERGENCE" for report in reports)
    critical = sum(report.classification == "CRITICAL_DIVERGENCE" for report in reports)
    if critical:
        action = "KILL_SWITCH"
        reasons = ("RECONCILIATION_CRITICAL_DIVERGENCE_PRESENT",)
    elif minor:
        action = "PAUSE"
        reasons = ("RECONCILIATION_MINOR_DIVERGENCE_PRESENT",)
    else:
        action = "ALLOW_ANALYSIS"
        reasons = ("RECONCILIATION_GATE_PASSED",)
    return ReconciliationVetoV1(action, bool(reports), minor, critical, reasons)


def _build_run_context(config: dict[str, Any], code_commit: str) -> Lot35RunContextV1:
    return Lot35RunContextV1(
        require_identifier(config["run_id"], "run_id"),
        "DATA_GOVERNANCE_ONLY",
        require_identifier(config["config_version"], "config_version"),
        require_git_sha(code_commit),
        require_identifier(config["correlation_id"], "correlation_id"),
    )


def _build_lineage(root: Path, config: dict[str, Any]) -> Lot35LineageEnvelopeV1:
    lot34_state = load_json_object(root / "data/audit/market_data_quality_engine_lot34.json")
    lot34_audit = load_json_object(root / "data/audit/market_data_quality_engine_audit_lot34.json")
    return Lot35LineageEnvelopeV1(
        require_identifier(config["lineage_id"], "lineage_id"),
        require_text(lot34_state["output_checksum"], "lot34_state_checksum"),
        require_text(lot34_audit["audit_checksum"], "lot34_audit_checksum"),
        file_checksum(root / "data/audit/data_quality_states_lot34.json"),
        file_checksum(root / "data/audit/data_anomalies_lot34.json"),
        file_checksum(root / "data/audit/data_quality_veto_lot34.json"),
        require_text(config["available_at"], "available_at"),
    )


def _classification_counts(
    reports: tuple[ReconciliationReportV1, ...],
) -> dict[str, int]:
    return {
        classification: sum(report.classification == classification for report in reports)
        for classification in sorted(CLASSIFICATIONS)
    }


def _build_state(
    root: Path,
    config: dict[str, Any],
    code_commit: str,
    reports: tuple[ReconciliationReportV1, ...],
    veto: ReconciliationVetoV1,
) -> CandleTradeBookReconciliationStateV1:
    counts = _classification_counts(reports)
    state = CandleTradeBookReconciliationStateV1(
        _build_run_context(config, code_commit),
        _build_lineage(root, config),
        require_text(config["event_time"], "event_time"),
        require_text(config["available_at"], "available_at"),
        require_text(config["generated_at"], "generated_at"),
        "VALIDATED_RECONCILIATION_ONLY" if veto.action == "ALLOW_ANALYSIS" else "BLOCKED_RECONCILIATION",
        reports,
        veto,
        Lot35MetricsV1(
            len(reports),
            0,
            counts["MATCH"],
            counts["TOLERATED_DIFF"],
            counts["MINOR_DIVERGENCE"],
            counts["CRITICAL_DIVERGENCE"],
            0,
        ),
        LOT35_REASON_CODES,
        lot35_safety(),
        "0" * 64,
    )
    return replace(
        state,
        output_checksum=canonical_checksum(state.payload_without_checksum()),
    )


def _build_audit(
    config_path: Path,
    code_commit: str,
    state: CandleTradeBookReconciliationStateV1,
) -> CandleTradeBookReconciliationAuditV1:
    counts = _classification_counts(state.reports)
    audit = CandleTradeBookReconciliationAuditV1(
        code_commit,
        state.output_checksum,
        file_checksum(config_path),
        state.lineage.lot34_state_checksum,
        state.lineage.lot34_audit_checksum,
        len(state.reports),
        counts["MATCH"],
        counts["TOLERATED_DIFF"],
        counts["MINOR_DIVERGENCE"],
        counts["CRITICAL_DIVERGENCE"],
        state.veto.action,
        state.validation_state,
        lot35_safety(),
        "0" * 64,
    )
    return replace(
        audit,
        audit_checksum=canonical_checksum(audit.payload_without_checksum()),
    )


def build_lot35_artifacts(
    root: Path, code_commit: str
) -> tuple[CandleTradeBookReconciliationStateV1, CandleTradeBookReconciliationAuditV1]:
    gate = load_json_object(root / "data/audit/lot35_v3_entry_gate.json")
    config_path = root / "config/data_governance/candle_trade_book_reconciliation_v1.json"
    config = load_json_object(config_path)
    _verify_gate(gate)
    _verify_lot34_evidence(root)
    _validate_config(config)
    reports = build_reconciliation_reports(config)
    veto = _build_veto(reports)
    state = _build_state(root, config, code_commit, reports, veto)
    audit = _build_audit(config_path, code_commit, state)
    return state, audit


def persist_lot35_artifacts(
    root: Path,
    state: CandleTradeBookReconciliationStateV1,
    audit: CandleTradeBookReconciliationAuditV1,
) -> None:
    atomic_write_json(
        root / "data/audit/candle_trade_book_reconciliation_lot35.json",
        state.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/candle_trade_book_reconciliation_audit_lot35.json",
        audit.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/reconciliation_reports_lot35.json",
        {
            "schema_version": "reconciliation-report-collection-v1",
            "records": [report.to_dict() for report in state.reports],
        },
    )
    atomic_write_json(
        root / "data/audit/reconciliation_veto_lot35.json",
        state.veto.to_dict(),
    )
