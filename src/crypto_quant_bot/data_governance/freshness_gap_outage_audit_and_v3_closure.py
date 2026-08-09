from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

from .candle_trade_book_reconciliation import build_lot35_artifacts
from .candle_trade_book_reconciliation_models import (
    CandleTradeBookReconciliationStateV1,
)
from .candle_trade_book_reconciliation_validation import (
    parse_utc_timestamp,
    require_identifier,
    require_integer,
    require_text,
)
from .freshness_gap_outage_audit_and_v3_closure_models import (
    ClosureManifestV1,
    FreshnessGapOutageAuditV3ClosureAuditV1,
    FreshnessGapOutageAuditV3ClosureStateV1,
    FreshnessGapOutageEvidenceV1,
    Lot36LineageEnvelopeV1,
    Lot36MetricsV1,
    Lot36RunContextV1,
    LotValidationReportV1,
    ReplayEvidenceV1,
)
from .freshness_gap_outage_audit_and_v3_closure_validation import (
    MICROSECONDS_PER_SECOND,
    V3ClosureError,
    duration_us,
    lot36_safety,
    require_basis_points,
)
from .market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)
from .market_data_quality_engine import build_lot34_artifacts, detect_anomalies
from .market_data_quality_engine_models import (
    DataAnomalyV1,
    DataQualityStateV1,
    DataQualityVetoV1,
    MarketDataQualityEngineStateV1,
)

EXPECTED_GATE_CHECKSUM = "ccddc668b83267effb6e82827c6a0f1f8d5879803f7d3e5cc6f9cfc745ba78a5"
EXPECTED_ROADMAP_BLOB = "84de51bda788a8d124fb7d344419c4a4b12030b5"
EXPECTED_LOT34_IMPLEMENTATION_COMMIT = "27ec00236bd0cd9adbc76b3df546a2c7b4bf9a4e"
EXPECTED_LOT34_STATE_CHECKSUM = "bc66816383ddf141016ad66796cc5dd4ad3442cd3594d96ad1f7db13d7c6bc01"
EXPECTED_LOT34_AUDIT_CHECKSUM = "cd4410a2ea9ef6cdc061caf5115d908d03575e219eb9f4da402bff1712f6c7ce"
EXPECTED_LOT35_IMPLEMENTATION_COMMIT = "a4501bb0d400c6c1b5cf970fc5aa6456ad8c6ea8"
EXPECTED_LOT35_STATE_CHECKSUM = "8fc7243beffdf985fd6947557b87ab7bd27f9191520eb2d5d9af25d1e7a886b4"
EXPECTED_LOT35_AUDIT_CHECKSUM = "98a88396f5b2e5ffc1cde02435399540ad213f5ec361b33e8a19c08b0fedf1de"
CONFIG_PATH = "config/data_governance/freshness_gap_outage_v3_closure_v1.json"
ROADMAP_PATH = "data/audit/product_scope_roadmap_lot21.jsonl"
CONFIG_FIELDS = {
    "schema_version",
    "config_version",
    "run_id",
    "correlation_id",
    "lineage_id",
    "event_time",
    "available_at",
    "generated_at",
    "freshness_reference_time",
    "max_staleness_seconds",
    "outage_interval_multiplier",
    "lot34_config_path",
    "required_lots",
}
COMMON_REASON_CODES = (
    "LOT36_ENTRY_GATE_VERIFIED",
    "CANONICAL_LOT36_ROADMAP_VERIFIED",
    "LOT34_QUALITY_REPLAY_VERIFIED",
    "LOT35_RECONCILIATION_REPLAY_VERIFIED",
    "FRESHNESS_GAP_OUTAGE_AUDIT_COMPLETED",
    "V3_CHAIN_CONTINUITY_VERIFIED",
    "RAW_DATA_IMMUTABILITY_PRESERVED",
    "EXTERNAL_CONNECTIVITY_DISABLED",
    "LOT37_REMAINS_LOCKED",
    "POST_MERGE_AUDIT_REQUIRED_FOR_V3_FINALIZATION",
)


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def _verify_payload_checksum(
    payload: dict[str, Any], field: str, expected: str, label: str
) -> None:
    content = dict(payload)
    checksum = content.pop(field, None)
    if checksum != expected or canonical_checksum(content) != checksum:
        raise V3ClosureError(f"{label} checksum mismatch")


def _verify_gate(root: Path) -> dict[str, Any]:
    gate = load_json_object(root / "data/audit/lot36_v3_entry_gate.json")
    _verify_payload_checksum(gate, "output_checksum", EXPECTED_GATE_CHECKSUM, "Lot 36 gate")
    expected = {
        "gate_status": "GO_LOT36_IMPLEMENTATION_ENTRY",
        "target_lot": 36,
        "current_version": "0.35.0",
        "human_decision": "APPROVED_START_LOT36",
        "implementation_started": False,
        "owner": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "next_lot": 37,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise V3ClosureError("Lot 36 entry gate does not authorize implementation")
    if gate.get("safety") != lot36_safety():
        raise V3ClosureError("Lot 36 gate safety boundary changed")
    return gate


def _verify_canonical_roadmap(root: Path, gate: dict[str, Any]) -> None:
    raw = (root / ROADMAP_PATH).read_bytes()
    if _git_blob_sha(raw) != EXPECTED_ROADMAP_BLOB:
        raise V3ClosureError("canonical roadmap blob changed")
    lines = raw.decode("utf-8").splitlines()
    if len(lines) < 37:
        raise V3ClosureError("canonical Lot 36 roadmap record missing")
    record = json.loads(lines[36])
    expected = {
        "lot_id": "Lot 36",
        "lot_number": 36,
        "title": "Freshness, Gap, Outage Audit & V3 Closure",
        "version_id": "V3_MARKET_DATA_GOVERNANCE",
        "responsible_component": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "status": "PLANNED_LOCKED",
    }
    if any(record.get(field) != value for field, value in expected.items()):
        raise V3ClosureError("canonical Lot 36 roadmap identity changed")
    reference = gate.get("canonical_roadmap")
    if not isinstance(reference, dict):
        raise V3ClosureError("Lot 36 canonical roadmap binding missing")
    if reference.get("source_blob_sha") != EXPECTED_ROADMAP_BLOB:
        raise V3ClosureError("Lot 36 gate lost canonical roadmap binding")


def _verify_historical_lifecycle(root: Path) -> None:
    overlay = load_json_object(root / "data/audit/roadmap_lifecycle_overlay_lot35.json")
    if overlay.get("latest_implemented_lot") != 35:
        raise V3ClosureError("Lot 35 is not the audited predecessor")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise V3ClosureError("historical lifecycle lots missing")
    lot35 = lots.get("35")
    if not isinstance(lot35, dict):
        raise V3ClosureError("historical Lot 35 lifecycle missing")
    if lot35.get("status") != "IMPLEMENTED_VALIDATED_RECONCILIATION_ONLY":
        raise V3ClosureError("historical Lot 35 status changed")
    expected_lock = {"implementation_started": False, "status": "PLANNED_LOCKED"}
    if lots.get("36") != expected_lock:
        raise V3ClosureError("Lot 36 historical lock changed")


def _validate_config(config: dict[str, Any]) -> None:
    if set(config) != CONFIG_FIELDS:
        raise V3ClosureError("Lot 36 configuration fields differ")
    if config["schema_version"] != "freshness-gap-outage-v3-closure-config-v1":
        raise V3ClosureError("Lot 36 configuration schema changed")
    if config["config_version"] != "lot36-freshness-gap-outage-v3-closure-config-v1":
        raise V3ClosureError("Lot 36 configuration version changed")
    for field in ("run_id", "correlation_id", "lineage_id"):
        require_identifier(config[field], field)
    event = parse_utc_timestamp(config["event_time"], "event_time")
    available = parse_utc_timestamp(config["available_at"], "available_at")
    generated = parse_utc_timestamp(config["generated_at"], "generated_at")
    reference = parse_utc_timestamp(config["freshness_reference_time"], "freshness_reference_time")
    if not event <= available <= generated or reference > generated:
        raise V3ClosureError("Lot 36 configuration violates causal time")
    require_integer(config["max_staleness_seconds"], "max_staleness_seconds", minimum=0)
    require_integer(config["outage_interval_multiplier"], "outage_interval_multiplier", minimum=2)
    if config["required_lots"] != list(range(31, 37)):
        raise V3ClosureError("Lot 36 required lot chain changed")
    require_text(config["lot34_config_path"], "lot34_config_path")


def _replay_previous_lots(
    root: Path,
) -> tuple[MarketDataQualityEngineStateV1, CandleTradeBookReconciliationStateV1]:
    lot34_state, lot34_audit = build_lot34_artifacts(root, EXPECTED_LOT34_IMPLEMENTATION_COMMIT)
    if lot34_state.output_checksum != EXPECTED_LOT34_STATE_CHECKSUM:
        raise V3ClosureError("Lot 34 deterministic replay state diverged")
    if lot34_audit.audit_checksum != EXPECTED_LOT34_AUDIT_CHECKSUM:
        raise V3ClosureError("Lot 34 deterministic replay audit diverged")
    lot35_state, lot35_audit = build_lot35_artifacts(root, EXPECTED_LOT35_IMPLEMENTATION_COMMIT)
    if lot35_state.output_checksum != EXPECTED_LOT35_STATE_CHECKSUM:
        raise V3ClosureError("Lot 35 deterministic replay state diverged")
    if lot35_audit.audit_checksum != EXPECTED_LOT35_AUDIT_CHECKSUM:
        raise V3ClosureError("Lot 35 deterministic replay audit diverged")
    return lot34_state, lot35_state


def _record_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        require_identifier(record.get("source_id"), "source_id"),
        require_identifier(record.get("instrument_id"), "instrument_id"),
        require_identifier(record.get("timeframe"), "timeframe"),
    )


def _record_order(record: dict[str, Any]) -> tuple[datetime, int, int, str]:
    return (
        parse_utc_timestamp(record.get("event_time"), "event_time"),
        require_integer(record.get("sequence_id"), "sequence_id", minimum=0),
        require_integer(record.get("revision_id"), "revision_id", minimum=0),
        require_identifier(record.get("record_id"), "record_id"),
    )


def _group_records(
    records: list[dict[str, Any]],
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        parse_utc_timestamp(record.get("available_at"), "available_at")
        grouped.setdefault(_record_key(record), []).append(record)
    if not grouped:
        raise V3ClosureError("Lot 36 requires quality records")
    return grouped


def _matching_quality_state(
    states: tuple[DataQualityStateV1, ...], key: tuple[str, str, str]
) -> DataQualityStateV1 | None:
    matches = [
        state
        for state in states
        if (state.source_id, state.instrument_id, state.timeframe) == key
    ]
    if len(matches) > 1:
        raise V3ClosureError("duplicate data quality state for freshness audit")
    return matches[0] if matches else None


def _interval_counts(
    ordered: list[dict[str, Any]], step_us: int, outage_multiplier: int
) -> tuple[int, int, int, int, int]:
    unique_times = sorted({_record_order(record)[0] for record in ordered})
    if not unique_times:
        return 0, 0, 0, 0, 0
    expected = duration_us(unique_times[0], unique_times[-1]) // step_us + 1
    observed = len(unique_times)
    missing = max(expected - observed, 0)
    gap_count = 0
    outage_count = 0
    for previous, current in pairwise(unique_times):
        delta = duration_us(previous, current)
        gap_count += delta > step_us
        outage_count += delta >= step_us * outage_multiplier
    return expected, observed, missing, gap_count, outage_count


def _freshness_reason_codes(
    missing: int, gaps: int, outages: int, stale: int, quality_known: bool, quality_pass: bool
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not quality_known:
        reasons.append("QUALITY_STATE_MISSING")
    elif not quality_pass:
        reasons.append("QUALITY_STATE_NOT_PASS")
    if missing:
        reasons.append("MISSING_INTERVALS_DETECTED")
    if gaps:
        reasons.append("GAPS_DETECTED")
    if outages:
        reasons.append("OUTAGES_DETECTED")
    if stale:
        reasons.append("LATEST_DATA_STALE")
    if not reasons:
        reasons.append("FRESHNESS_GAP_OUTAGE_PASS")
    return tuple(reasons)


def _latest_record(ordered: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        ordered,
        key=lambda record: parse_utc_timestamp(record["available_at"], "available_at"),
    )


def _freshness_evidence_for_group(
    key: tuple[str, str, str],
    records: list[dict[str, Any]],
    quality_state: DataQualityStateV1 | None,
    timeframe_seconds: dict[str, int],
    reference_time: datetime,
    max_staleness_seconds: int,
    outage_multiplier: int,
) -> FreshnessGapOutageEvidenceV1:
    ordered = sorted(records, key=_record_order)
    step_seconds = timeframe_seconds.get(key[2])
    if not isinstance(step_seconds, int) or step_seconds <= 0:
        raise V3ClosureError(f"timeframe interval missing: {key[2]}")
    counts = _interval_counts(
        ordered, step_seconds * MICROSECONDS_PER_SECOND, outage_multiplier
    )
    expected, observed, missing, gaps, outages = counts
    latest = _latest_record(ordered)
    latest_event = parse_utc_timestamp(latest["event_time"], "event_time")
    latest_available = parse_utc_timestamp(latest["available_at"], "available_at")
    age_us = duration_us(latest_available, reference_time)
    max_staleness_us = max_staleness_seconds * MICROSECONDS_PER_SECOND
    stale = int(age_us > max_staleness_us)
    quality_known = quality_state is not None and quality_state.status != "UNKNOWN"
    quality_pass = quality_state is not None and quality_state.status == "PASS"
    blocked = bool(missing or gaps or outages or stale or not quality_pass)
    freshness_bps = 0 if stale or quality_state is None else quality_state.freshness_bps
    return FreshnessGapOutageEvidenceV1(
        key[0], key[1], key[2], len(records), expected, observed, missing, gaps, outages,
        stale, latest_event.isoformat().replace("+00:00", "Z"),
        latest_available.isoformat().replace("+00:00", "Z"),
        reference_time.isoformat().replace("+00:00", "Z"), age_us, max_staleness_us,
        freshness_bps, "BLOCKED" if blocked else "PASS",
        _freshness_reason_codes(missing, gaps, outages, stale, quality_known, quality_pass),
    )


def audit_freshness_gap_outage(
    records: list[dict[str, Any]],
    quality_states: tuple[DataQualityStateV1, ...],
    timeframe_seconds: dict[str, int],
    reference_time: str,
    max_staleness_seconds: int,
    outage_multiplier: int,
) -> tuple[FreshnessGapOutageEvidenceV1, ...]:
    reference = parse_utc_timestamp(reference_time, "reference_time")
    grouped = _group_records(records)
    return tuple(
        _freshness_evidence_for_group(
            key,
            grouped[key],
            _matching_quality_state(quality_states, key),
            timeframe_seconds,
            reference,
            max_staleness_seconds,
            outage_multiplier,
        )
        for key in sorted(grouped)
    )


def _closure_quality_veto(
    quality_states: tuple[DataQualityStateV1, ...],
    anomalies: tuple[DataAnomalyV1, ...],
    freshness: tuple[FreshnessGapOutageEvidenceV1, ...],
    minimum_quality_bps: int,
) -> DataQualityVetoV1:
    quality_known = bool(quality_states) and all(
        state.status != "UNKNOWN" for state in quality_states
    )
    observed = min((state.quality_score_bps for state in quality_states), default=0)
    blocked = (
        not quality_known
        or observed < minimum_quality_bps
        or bool(anomalies)
        or any(item.status != "PASS" for item in freshness)
    )
    blocking_types = tuple(sorted({item.anomaly_type for item in anomalies}))
    reasons = (
        ("V3_CLOSURE_DATA_QUALITY_BLOCKED",)
        if blocked
        else ("V3_CLOSURE_DATA_QUALITY_PASS",)
    )
    return DataQualityVetoV1(
        action="BLOCK_ANALYSIS_OR_TRADING" if blocked else "ALLOW_ANALYSIS",
        quality_known=quality_known,
        minimum_quality_bps=minimum_quality_bps,
        observed_quality_bps=observed,
        blocking_anomaly_types=blocking_types,
        reason_codes=reasons,
    )


def _build_manifest(ready: bool) -> ClosureManifestV1:
    closure_status = (
        "CANDIDATE_VALIDATED_AWAITING_POST_MERGE_AUDIT" if ready else "BLOCKED"
    )
    reason_codes = (
        "V3_CLOSURE_CANDIDATE_READY" if ready else "V3_CLOSURE_BLOCKED",
        "POST_MERGE_AUDIT_REQUIRED",
        "HUMAN_REVIEW_REQUIRED",
        "LOT37_REMAINS_LOCKED",
    )
    payload: dict[str, Any] = {
        "schema_version": "closure-manifest-v1",
        "version_id": "V3_MARKET_DATA_GOVERNANCE",
        "lots_included": list(range(31, 37)),
        "closure_status": closure_status,
        "v3_closed": False,
        "post_merge_audit_required": True,
        "human_review_required": True,
        "next_lot": 37,
        "next_lot_status": "PLANNED_LOCKED",
        "reason_codes": list(reason_codes),
    }
    return ClosureManifestV1(
        "V3_MARKET_DATA_GOVERNANCE", tuple(range(31, 37)), closure_status, False,
        True, True, 37, "PLANNED_LOCKED", reason_codes, canonical_checksum(payload)
    )


def _build_validation_report(ready: bool) -> LotValidationReportV1:
    return LotValidationReportV1(
        validated_lots=tuple(range(31, 37)),
        required_validator_count=6,
        closure_candidate_ready=ready,
        reason_codes=(
            "LOTS31_35_CERTIFIED_LINEAGE_VERIFIED",
            "LOT36_CLOSURE_INVARIANTS_PASS" if ready else "LOT36_CLOSURE_INVARIANTS_BLOCKED",
        ),
    )


def _build_lineage(config: dict[str, Any]) -> Lot36LineageEnvelopeV1:
    return Lot36LineageEnvelopeV1(
        config["lineage_id"], EXPECTED_GATE_CHECKSUM, EXPECTED_ROADMAP_BLOB,
        EXPECTED_LOT34_STATE_CHECKSUM, EXPECTED_LOT34_AUDIT_CHECKSUM,
        EXPECTED_LOT35_STATE_CHECKSUM, EXPECTED_LOT35_AUDIT_CHECKSUM,
        config["available_at"],
    )


def _build_metrics(
    records: list[dict[str, Any]],
    freshness: tuple[FreshnessGapOutageEvidenceV1, ...],
    anomaly_count: int,
    ready: bool,
    config: dict[str, Any],
) -> Lot36MetricsV1:
    available = parse_utc_timestamp(config["available_at"], "available_at")
    generated = parse_utc_timestamp(config["generated_at"], "generated_at")
    return Lot36MetricsV1(
        len(records), 0 if ready else 1,
        sum(item.gap_count for item in freshness),
        sum(item.outage_count for item in freshness),
        sum(item.stale_record_count for item in freshness),
        anomaly_count, duration_us(available, generated),
    )


def _quality_inputs(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    path = root / require_text(config["lot34_config_path"], "lot34_config_path")
    quality_config = load_json_object(path)
    records = quality_config.get("records")
    raw_intervals = quality_config.get("timeframe_seconds")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise V3ClosureError("Lot 34 quality records unavailable for closure")
    if not isinstance(raw_intervals, dict):
        raise V3ClosureError("Lot 34 timeframe configuration missing")
    intervals = {
        require_identifier(key, "timeframe"): require_integer(value, "interval", minimum=1)
        for key, value in raw_intervals.items()
    }
    return quality_config, [dict(item) for item in records], intervals


def _closure_ready(
    quality_veto: DataQualityVetoV1,
    lot35_state: CandleTradeBookReconciliationStateV1,
    freshness: tuple[FreshnessGapOutageEvidenceV1, ...],
    anomalies: tuple[DataAnomalyV1, ...],
) -> bool:
    return (
        quality_veto.action == "ALLOW_ANALYSIS"
        and lot35_state.veto.action == "ALLOW_ANALYSIS"
        and all(item.status == "PASS" for item in freshness)
        and not anomalies
    )


def _build_state(
    config: dict[str, Any],
    code_commit: str,
    lot34_state: MarketDataQualityEngineStateV1,
    lot35_state: CandleTradeBookReconciliationStateV1,
    records: list[dict[str, Any]],
    freshness: tuple[FreshnessGapOutageEvidenceV1, ...],
    anomalies: tuple[DataAnomalyV1, ...],
    quality_veto: DataQualityVetoV1,
) -> FreshnessGapOutageAuditV3ClosureStateV1:
    ready = _closure_ready(quality_veto, lot35_state, freshness, anomalies)
    state = FreshnessGapOutageAuditV3ClosureStateV1(
        Lot36RunContextV1(config["run_id"], "DATA_GOVERNANCE_ONLY", config["config_version"], code_commit, config["correlation_id"]),
        _build_lineage(config), config["event_time"], config["available_at"], config["generated_at"],
        "VALIDATED_V3_CLOSURE_CANDIDATE" if ready else "BLOCKED_V3_CLOSURE",
        freshness, lot34_state.quality_states, anomalies, quality_veto, lot35_state.veto,
        _build_validation_report(ready), _build_manifest(ready),
        _build_metrics(records, freshness, len(anomalies), ready, config),
        (*COMMON_REASON_CODES, "V3_CLOSURE_CANDIDATE_READY" if ready else "V3_CLOSURE_BLOCKED"),
        lot36_safety(), "0" * 64,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    state: FreshnessGapOutageAuditV3ClosureStateV1,
    code_commit: str,
    config_path: Path,
) -> FreshnessGapOutageAuditV3ClosureAuditV1:
    audit = FreshnessGapOutageAuditV3ClosureAuditV1(
        code_commit, state.output_checksum, file_checksum(config_path),
        state.closure_manifest.manifest_checksum,
        EXPECTED_LOT34_STATE_CHECKSUM, EXPECTED_LOT34_AUDIT_CHECKSUM,
        EXPECTED_LOT35_STATE_CHECKSUM, EXPECTED_LOT35_AUDIT_CHECKSUM,
        len(state.freshness_audits), len(state.anomalies),
        state.data_quality_veto.action, state.reconciliation_veto.action,
        state.validation_state, lot36_safety(), "0" * 64,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def build_lot36_artifacts(
    root: Path, code_commit: str
) -> tuple[FreshnessGapOutageAuditV3ClosureStateV1, FreshnessGapOutageAuditV3ClosureAuditV1]:
    gate = _verify_gate(root)
    _verify_canonical_roadmap(root, gate)
    _verify_historical_lifecycle(root)
    config_path = root / CONFIG_PATH
    config = load_json_object(config_path)
    _validate_config(config)
    lot34_state, lot35_state = _replay_previous_lots(root)
    quality_config, records, intervals = _quality_inputs(root, config)
    anomalies = detect_anomalies(quality_config)
    if anomalies != lot34_state.anomalies:
        raise V3ClosureError("Lot 34 anomaly replay diverged during V3 closure")
    freshness = audit_freshness_gap_outage(
        records, lot34_state.quality_states, intervals, config["freshness_reference_time"],
        require_integer(config["max_staleness_seconds"], "max_staleness_seconds", minimum=0),
        require_integer(config["outage_interval_multiplier"], "outage_interval_multiplier", minimum=2),
    )
    minimum = require_basis_points(quality_config["minimum_quality_bps"], "minimum_quality_bps")
    quality_veto = _closure_quality_veto(lot34_state.quality_states, anomalies, freshness, minimum)
    state = _build_state(config, code_commit, lot34_state, lot35_state, records, freshness, anomalies, quality_veto)
    return state, _build_audit(state, code_commit, config_path)


def build_replay_evidence(root: Path, code_commit: str) -> ReplayEvidenceV1:
    run1, _ = build_lot36_artifacts(root, code_commit)
    run2, _ = build_lot36_artifacts(root, code_commit)
    match = run1.output_checksum == run2.output_checksum
    replay_status = "REPLAY_MATCH" if match else "REPLAY_DIVERGENCE"
    reason_codes = (
        "LOT36_DETERMINISTIC_REPLAY_MATCH" if match else "LOT36_NON_DETERMINISTIC_REPLAY",
    )
    payload: dict[str, Any] = {
        "schema_version": "replay-evidence-v1",
        "run1_checksum": run1.output_checksum,
        "run2_checksum": run2.output_checksum,
        "replay_status": replay_status,
        "match": match,
        "reason_codes": list(reason_codes),
    }
    return ReplayEvidenceV1(
        run1.output_checksum, run2.output_checksum, replay_status, match,
        reason_codes, canonical_checksum(payload),
    )


def _output_paths(root: Path) -> dict[str, Path]:
    return {
        "state": root / "data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json",
        "audit": root / "data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json",
        "quality_states": root / "data/audit/data_quality_states_lot36.json",
        "anomalies": root / "data/audit/data_anomalies_lot36.json",
        "quality_veto": root / "data/audit/data_quality_veto_lot36.json",
        "replay": root / "data/audit/replay_evidence_lot36.json",
        "manifest": root / "data/audit/closure_manifest_lot36.json",
    }


def write_lot36_artifacts(root: Path, code_commit: str) -> dict[str, str]:
    state, audit = build_lot36_artifacts(root, code_commit)
    replay = build_replay_evidence(root, code_commit)
    outputs = _output_paths(root)
    atomic_write_json(outputs["state"], state.to_dict())
    atomic_write_json(outputs["audit"], audit.to_dict())
    atomic_write_json(outputs["quality_states"], {"schema_version": "data-quality-state-collection-v1", "records": [item.to_dict() for item in state.quality_states]})
    atomic_write_json(outputs["anomalies"], {"schema_version": "data-anomaly-collection-v1", "records": [item.to_dict() for item in state.anomalies]})
    atomic_write_json(outputs["quality_veto"], state.data_quality_veto.to_dict())
    atomic_write_json(outputs["replay"], replay.to_dict())
    atomic_write_json(outputs["manifest"], state.closure_manifest.to_dict())
    return {name: str(path.relative_to(root)) for name, path in outputs.items()}
