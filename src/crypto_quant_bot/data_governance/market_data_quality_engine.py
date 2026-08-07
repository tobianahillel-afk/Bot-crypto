from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

from .market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)
from .market_data_quality_engine_models import (
    DataAnomalyV1,
    DataQualityStateV1,
    DataQualityVetoV1,
    Lot34LineageEnvelopeV1,
    Lot34MetricsV1,
    Lot34RunContextV1,
    MarketDataQualityEngineAuditV1,
    MarketDataQualityEngineStateV1,
)
from .market_data_quality_engine_validation import (
    MarketDataQualityError,
    decimal_from_string,
    lot34_safety,
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_text,
)

EXPECTED_GATE_CHECKSUM = "4a5bf1d61f97ce4a49836da577e6a2464544f16554143973caf32777de4830fa"
REQUIRED_RECORD_FIELDS = {
    "record_id",
    "source_id",
    "instrument_id",
    "timeframe",
    "event_time",
    "available_at",
    "sequence_id",
    "revision_id",
    "source_schema_version",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "bid",
    "ask",
}
MICROSECONDS_PER_SECOND = 1_000_000


def _duration_us(start: datetime, end: datetime) -> int:
    delta = end - start
    return (
        delta.days * 86_400_000_000
        + delta.seconds * MICROSECONDS_PER_SECOND
        + delta.microseconds
    )


ANOMALY_REASON = {
    "MISSING_INTERVAL": "DQ_MISSING_INTERVAL",
    "DUPLICATE": "DQ_DUPLICATE_EVENT",
    "OUT_OF_ORDER": "DQ_OUT_OF_ORDER_EVENT",
    "STALE_DATA": "DQ_STALE_DATA",
    "INVALID_OHLC": "DQ_INVALID_OHLC",
    "NEGATIVE_VOLUME": "DQ_NEGATIVE_VOLUME",
    "IMPOSSIBLE_SPREAD": "DQ_IMPOSSIBLE_SPREAD",
    "SCHEMA_DRIFT": "DQ_SCHEMA_DRIFT",
}
LOT34_REASON_CODES = (
    "LOT34_ENTRY_GATE_VERIFIED",
    "LOT33_TEMPORAL_LINEAGE_VERIFIED",
    "QUALITY_ANOMALY_FAMILIES_EVALUATED",
    "QUALITY_SCORES_COMPUTED_IN_BASIS_POINTS",
    "NON_DESTRUCTIVE_QUARANTINE_ENFORCED",
    "DATA_QUALITY_VETO_EVALUATED_FAIL_CLOSED",
    "EXTERNAL_CONNECTIVITY_DISABLED",
    "LOT35_REMAINS_LOCKED",
)
LOT34_CONFIG_FIELDS = {
    "schema_version",
    "config_version",
    "run_id",
    "correlation_id",
    "lineage_id",
    "event_time",
    "available_at",
    "generated_at",
    "expected_source_schema_version",
    "minimum_quality_bps",
    "max_staleness_seconds",
    "timeframe_seconds",
    "records",
}


def _verify_gate(gate: dict[str, Any]) -> None:
    payload = dict(gate)
    checksum = payload.pop("output_checksum", None)
    if checksum != EXPECTED_GATE_CHECKSUM or canonical_checksum(payload) != checksum:
        raise MarketDataQualityError("Lot 34 entry gate checksum mismatch")
    expected = {
        "gate_status": "GO_LOT34_IMPLEMENTATION_ENTRY",
        "target_lot": 34,
        "current_version": "0.33.0",
        "human_decision": "APPROVED_START_LOT34",
        "implementation_started": False,
        "owner": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "next_lot": 35,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise MarketDataQualityError("Lot 34 entry gate does not authorize implementation")
    if gate.get("safety") != lot34_safety():
        raise MarketDataQualityError("Lot 34 gate safety boundary changed")


def _validate_config_identity(config: dict[str, Any]) -> None:
    if set(config) != LOT34_CONFIG_FIELDS:
        raise MarketDataQualityError("Lot 34 configuration fields differ")
    if config["schema_version"] != "market-data-quality-config-v1":
        raise MarketDataQualityError("Lot 34 configuration schema changed")
    if config["config_version"] != "lot34-market-data-quality-config-v1":
        raise MarketDataQualityError("Lot 34 configuration version changed")


def _validate_config_times(config: dict[str, Any]) -> None:
    event = parse_utc_timestamp(config["event_time"], "event_time")
    available = parse_utc_timestamp(config["available_at"], "available_at")
    generated = parse_utc_timestamp(config["generated_at"], "generated_at")
    if not event <= available <= generated:
        raise MarketDataQualityError("Lot 34 configuration violates causal availability")


def _validate_config_limits(config: dict[str, Any]) -> None:
    minimum = require_integer(
        config["minimum_quality_bps"], "minimum_quality_bps", minimum=0
    )
    require_integer(
        config["max_staleness_seconds"], "max_staleness_seconds", minimum=0
    )
    if minimum > 10_000:
        raise MarketDataQualityError("minimum_quality_bps cannot exceed 10000")
    intervals = config["timeframe_seconds"]
    if not isinstance(intervals, dict) or not intervals:
        raise MarketDataQualityError("timeframe_seconds must be a non-empty object")
    for timeframe, seconds in intervals.items():
        require_identifier(timeframe, "timeframe")
        require_integer(seconds, "timeframe_seconds", minimum=1)
    records = config["records"]
    if not isinstance(records, list) or not records:
        raise MarketDataQualityError("Lot 34 requires at least one quality record")


def _validate_config(config: dict[str, Any]) -> None:
    _validate_config_identity(config)
    _validate_config_times(config)
    _validate_config_limits(config)


def _record_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        require_identifier(record.get("source_id"), "source_id"),
        require_identifier(record.get("instrument_id"), "instrument_id"),
        require_identifier(record.get("timeframe"), "timeframe"),
    )


def _event_identity(record: dict[str, Any]) -> tuple[str, str, str, str, int, int]:
    source, instrument, timeframe = _record_key(record)
    return (
        source,
        instrument,
        timeframe,
        require_text(record.get("event_time"), "event_time"),
        require_integer(record.get("sequence_id"), "sequence_id", minimum=0),
        require_integer(record.get("revision_id"), "revision_id", minimum=0),
    )


def _anomaly(
    index: int,
    anomaly_type: str,
    record_ids: tuple[str, ...],
    start: str,
    end: str,
) -> DataAnomalyV1:
    return DataAnomalyV1(
        anomaly_id=f"lot34-{anomaly_type.lower()}-{index:04d}",
        anomaly_type=anomaly_type,
        severity="ERROR",
        record_ids=record_ids,
        interval_start=start,
        interval_end=end,
        correction_permitted=False,
        quarantined=True,
        reason_code=ANOMALY_REASON[anomaly_type],
    )


def _schema_anomalies(
    records: list[dict[str, Any]], expected_schema: str
) -> list[DataAnomalyV1]:
    anomalies: list[DataAnomalyV1] = []
    for record in records:
        record_id = require_identifier(record.get("record_id"), "record_id")
        event_time = require_text(record.get("event_time"), "event_time")
        field_drift = set(record) != REQUIRED_RECORD_FIELDS
        version_drift = record.get("source_schema_version") != expected_schema
        if field_drift or version_drift:
            anomalies.append(
                _anomaly(
                    len(anomalies) + 1,
                    "SCHEMA_DRIFT",
                    (record_id,),
                    event_time,
                    event_time,
                )
            )
    return anomalies


def _duplicate_anomalies(
    records: list[dict[str, Any]], offset: int
) -> list[DataAnomalyV1]:
    anomalies: list[DataAnomalyV1] = []
    seen: dict[tuple[str, str, str, str, int, int], str] = {}
    for record in records:
        if set(record) != REQUIRED_RECORD_FIELDS:
            continue
        identity = _event_identity(record)
        record_id = require_identifier(record["record_id"], "record_id")
        prior = seen.get(identity)
        if prior is None:
            seen[identity] = record_id
            continue
        event_time = require_text(record["event_time"], "event_time")
        anomalies.append(
            _anomaly(
                offset + len(anomalies) + 1,
                "DUPLICATE",
                (prior, record_id),
                event_time,
                event_time,
            )
        )
    return anomalies


def _ordering_anomalies(
    records: list[dict[str, Any]], offset: int
) -> list[DataAnomalyV1]:
    anomalies: list[DataAnomalyV1] = []
    latest: dict[tuple[str, str, str], tuple[datetime, int, int, str]] = {}
    for record in records:
        if set(record) != REQUIRED_RECORD_FIELDS:
            continue
        key = _record_key(record)
        current = (
            parse_utc_timestamp(record["event_time"], "event_time"),
            require_integer(record["sequence_id"], "sequence_id", minimum=0),
            require_integer(record["revision_id"], "revision_id", minimum=0),
            require_identifier(record["record_id"], "record_id"),
        )
        previous = latest.get(key)
        if previous is not None and current[:3] < previous[:3]:
            anomalies.append(
                _anomaly(
                    offset + len(anomalies) + 1,
                    "OUT_OF_ORDER",
                    (previous[3], current[3]),
                    record["event_time"],
                    previous[0].isoformat().replace("+00:00", "Z"),
                )
            )
        if previous is None or current[:3] > previous[:3]:
            latest[key] = current
    return anomalies


def _missing_interval_anomalies(
    records: list[dict[str, Any]],
    timeframe_seconds: dict[str, int],
    offset: int,
) -> list[DataAnomalyV1]:
    anomalies: list[DataAnomalyV1] = []
    grouped: dict[tuple[str, str, str], list[tuple[datetime, str]]] = {}
    for record in records:
        if set(record) != REQUIRED_RECORD_FIELDS:
            continue
        grouped.setdefault(_record_key(record), []).append(
            (
                parse_utc_timestamp(record["event_time"], "event_time"),
                record["record_id"],
            )
        )
    for key, values in sorted(grouped.items()):
        step = timeframe_seconds.get(key[2])
        if step is None:
            raise MarketDataQualityError(
                f"missing interval definition for timeframe {key[2]}"
            )
        ordered = sorted(set(values))
        for previous, current in pairwise(ordered):
            delta_us = _duration_us(previous[0], current[0])
            if delta_us > step * MICROSECONDS_PER_SECOND:
                anomalies.append(
                    _anomaly(
                        offset + len(anomalies) + 1,
                        "MISSING_INTERVAL",
                        (previous[1], current[1]),
                        previous[0].isoformat().replace("+00:00", "Z"),
                        current[0].isoformat().replace("+00:00", "Z"),
                    )
                )
    return anomalies


def _record_value_anomalies(
    record: dict[str, Any],
    generated_at: datetime,
    max_staleness: int,
    offset: int,
) -> list[DataAnomalyV1]:
    record_id = require_identifier(record["record_id"], "record_id")
    event_time = require_text(record["event_time"], "event_time")
    available = parse_utc_timestamp(record["available_at"], "available_at")
    if available < parse_utc_timestamp(event_time, "event_time"):
        raise MarketDataQualityError("record available_at cannot precede event_time")
    anomalies: list[DataAnomalyV1] = []
    if _duration_us(available, generated_at) > max_staleness * MICROSECONDS_PER_SECOND:
        anomalies.append(
            _anomaly(offset + 1, "STALE_DATA", (record_id,), event_time, event_time)
        )
    open_price = decimal_from_string(record["open"], "open")
    high = decimal_from_string(record["high"], "high")
    low = decimal_from_string(record["low"], "low")
    close = decimal_from_string(record["close"], "close")
    volume = decimal_from_string(record["volume"], "volume")
    bid = decimal_from_string(record["bid"], "bid")
    ask = decimal_from_string(record["ask"], "ask")
    if high < low or high < max(open_price, close) or low > min(open_price, close):
        anomalies.append(
            _anomaly(
                offset + len(anomalies) + 1,
                "INVALID_OHLC",
                (record_id,),
                event_time,
                event_time,
            )
        )
    if volume < Decimal("0"):
        anomalies.append(
            _anomaly(
                offset + len(anomalies) + 1,
                "NEGATIVE_VOLUME",
                (record_id,),
                event_time,
                event_time,
            )
        )
    if bid < Decimal("0") or ask < Decimal("0") or bid > ask:
        anomalies.append(
            _anomaly(
                offset + len(anomalies) + 1,
                "IMPOSSIBLE_SPREAD",
                (record_id,),
                event_time,
                event_time,
            )
        )
    return anomalies


def _value_anomalies(
    records: list[dict[str, Any]],
    generated_at: datetime,
    max_staleness: int,
    offset: int,
) -> list[DataAnomalyV1]:
    anomalies: list[DataAnomalyV1] = []
    for record in records:
        if set(record) != REQUIRED_RECORD_FIELDS:
            continue
        anomalies.extend(
            _record_value_anomalies(
                record,
                generated_at,
                max_staleness,
                offset + len(anomalies),
            )
        )
    return anomalies


def detect_anomalies(config: dict[str, Any]) -> tuple[DataAnomalyV1, ...]:
    records = config["records"]
    if any(not isinstance(record, dict) for record in records):
        raise MarketDataQualityError("quality records must be objects")
    expected_schema = require_text(
        config["expected_source_schema_version"],
        "expected_source_schema_version",
    )
    anomalies = _schema_anomalies(records, expected_schema)
    anomalies.extend(_duplicate_anomalies(records, len(anomalies)))
    anomalies.extend(_ordering_anomalies(records, len(anomalies)))
    intervals = {
        require_identifier(key, "timeframe"): require_integer(
            value, "timeframe_seconds", minimum=1
        )
        for key, value in config["timeframe_seconds"].items()
    }
    anomalies.extend(_missing_interval_anomalies(records, intervals, len(anomalies)))
    anomalies.extend(
        _value_anomalies(
            records,
            parse_utc_timestamp(config["generated_at"], "generated_at"),
            require_integer(
                config["max_staleness_seconds"],
                "max_staleness_seconds",
                minimum=0,
            ),
            len(anomalies),
        )
    )
    return tuple(
        sorted(
            anomalies,
            key=lambda item: (item.anomaly_type, item.interval_start, item.anomaly_id),
        )
    )


def _coverage_components(
    valid_records: list[dict[str, Any]],
    timeframe: str,
    config: dict[str, Any],
) -> tuple[int, int, int]:
    times = sorted(
        {
            parse_utc_timestamp(record["event_time"], "event_time")
            for record in valid_records
        }
    )
    step = require_integer(
        config["timeframe_seconds"][timeframe], "timeframe_seconds", minimum=1
    )
    expected = (
        1
        if len(times) <= 1
        else _duration_us(times[0], times[-1])
        // (step * MICROSECONDS_PER_SECOND)
        + 1
    )
    observed = len(times)
    coverage = min(10_000, 10_000 * observed // max(1, expected))
    return expected, observed, coverage


def _freshness_score(
    valid_records: list[dict[str, Any]], config: dict[str, Any]
) -> int:
    generated = parse_utc_timestamp(config["generated_at"], "generated_at")
    newest_available = max(
        (
            parse_utc_timestamp(record["available_at"], "available_at")
            for record in valid_records
        ),
        default=None,
    )
    if newest_available is None:
        return 0
    max_staleness = require_integer(
        config["max_staleness_seconds"], "max_staleness_seconds", minimum=0
    )
    age_seconds = (
        max(0, _duration_us(newest_available, generated)) // MICROSECONDS_PER_SECOND
    )
    if max_staleness == 0 and age_seconds == 0:
        return 10_000
    return max(
        0,
        10_000 - (10_000 * age_seconds // max(1, max_staleness)),
    )


def _consistency_components(
    records: list[dict[str, Any]], anomalies: tuple[DataAnomalyV1, ...]
) -> tuple[int, int, int]:
    valid_count = sum(set(record) == REQUIRED_RECORD_FIELDS for record in records)
    completeness = 10_000 * valid_count // max(1, len(records))
    group_ids = {
        record.get("record_id")
        for record in records
        if isinstance(record.get("record_id"), str)
    }
    anomaly_count = sum(
        bool(group_ids.intersection(item.record_ids)) for item in anomalies
    )
    consistency = max(0, 10_000 - 1_250 * anomaly_count)
    return completeness, consistency, anomaly_count


def _quality_state_for_group(
    key: tuple[str, str, str],
    records: list[dict[str, Any]],
    anomalies: tuple[DataAnomalyV1, ...],
    config: dict[str, Any],
) -> DataQualityStateV1:
    source_id, instrument_id, timeframe = key
    valid_records = [
        record for record in records if set(record) == REQUIRED_RECORD_FIELDS
    ]
    expected, observed, coverage = _coverage_components(
        valid_records, timeframe, config
    )
    freshness = _freshness_score(valid_records, config)
    completeness, consistency, anomaly_count = _consistency_components(
        records, anomalies
    )
    quality = (coverage + freshness + completeness + consistency) // 4
    minimum = require_integer(
        config["minimum_quality_bps"], "minimum_quality_bps", minimum=0
    )
    status = "PASS" if anomaly_count == 0 and quality >= minimum else "BLOCKED"
    return DataQualityStateV1(
        source_id,
        instrument_id,
        timeframe,
        len(records),
        expected,
        observed,
        anomaly_count,
        coverage,
        freshness,
        completeness,
        consistency,
        quality,
        status,
    )


def _build_quality_states(
    config: dict[str, Any], anomalies: tuple[DataAnomalyV1, ...]
) -> tuple[DataQualityStateV1, ...]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in config["records"]:
        if not isinstance(record, dict):
            raise MarketDataQualityError("quality records must be objects")
        if not {"source_id", "instrument_id", "timeframe"}.issubset(record):
            raise MarketDataQualityError("schema drift cannot remove grouping identity")
        grouped.setdefault(_record_key(record), []).append(record)
    return tuple(
        _quality_state_for_group(key, grouped[key], anomalies, config)
        for key in sorted(grouped)
    )


def _build_veto(
    states: tuple[DataQualityStateV1, ...],
    anomalies: tuple[DataAnomalyV1, ...],
    minimum: int,
) -> DataQualityVetoV1:
    quality_known = bool(states)
    observed = min((state.quality_score_bps for state in states), default=0)
    blocking = tuple(sorted({item.anomaly_type for item in anomalies}))
    blocked = (not quality_known) or bool(blocking) or observed < minimum
    if not quality_known:
        reasons = ("DATA_QUALITY_UNKNOWN",)
    elif blocking:
        reasons = ("DATA_QUALITY_ANOMALY_PRESENT",)
    elif observed < minimum:
        reasons = ("DATA_QUALITY_SCORE_BELOW_THRESHOLD",)
    else:
        reasons = ("DATA_QUALITY_GATE_PASSED",)
    return DataQualityVetoV1(
        "BLOCK_ANALYSIS_OR_TRADING" if blocked else "ALLOW_ANALYSIS",
        quality_known,
        minimum,
        observed,
        blocking,
        reasons,
    )


def _build_run_context(config: dict[str, Any], code_commit: str) -> Lot34RunContextV1:
    return Lot34RunContextV1(
        require_identifier(config["run_id"], "run_id"),
        "DATA_GOVERNANCE_ONLY",
        require_identifier(config["config_version"], "config_version"),
        require_git_sha(code_commit),
        require_identifier(config["correlation_id"], "correlation_id"),
    )


def _build_lineage(root: Path, config: dict[str, Any]) -> Lot34LineageEnvelopeV1:
    lot33_state = load_json_object(
        root / "data/audit/timestamp_clock_and_timezone_governance_lot33.json"
    )
    lot33_audit = load_json_object(
        root / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json"
    )
    return Lot34LineageEnvelopeV1(
        require_identifier(config["lineage_id"], "lineage_id"),
        require_text(lot33_state.get("output_checksum"), "lot33_state_checksum"),
        require_text(lot33_audit.get("audit_checksum"), "lot33_audit_checksum"),
        file_checksum(root / "data/audit/canonical_time_envelopes_lot33.json"),
        require_text(config["available_at"], "available_at"),
    )


def _build_state(
    root: Path,
    config: dict[str, Any],
    code_commit: str,
    anomalies: tuple[DataAnomalyV1, ...],
    states: tuple[DataQualityStateV1, ...],
    veto: DataQualityVetoV1,
    quarantine: tuple[str, ...],
) -> MarketDataQualityEngineStateV1:
    validation_state = (
        "VALIDATED_DATA_QUALITY_ONLY"
        if veto.action == "ALLOW_ANALYSIS"
        else "BLOCKED_DATA_QUALITY"
    )
    state = MarketDataQualityEngineStateV1(
        _build_run_context(config, code_commit),
        _build_lineage(root, config),
        require_text(config["event_time"], "event_time"),
        require_text(config["available_at"], "available_at"),
        require_text(config["generated_at"], "generated_at"),
        validation_state,
        states,
        anomalies,
        quarantine,
        veto,
        Lot34MetricsV1(len(config["records"]), 0, len(anomalies), len(quarantine), 0),
        LOT34_REASON_CODES,
        lot34_safety(),
        "0" * 64,
    )
    return replace(
        state,
        output_checksum=canonical_checksum(state.payload_without_checksum()),
    )


def _build_audit(
    config_path: Path,
    code_commit: str,
    config: dict[str, Any],
    state: MarketDataQualityEngineStateV1,
    anomalies: tuple[DataAnomalyV1, ...],
    quarantine: tuple[str, ...],
) -> MarketDataQualityEngineAuditV1:
    audit = MarketDataQualityEngineAuditV1(
        code_commit,
        state.output_checksum,
        file_checksum(config_path),
        state.lineage.lot33_state_checksum,
        state.lineage.lot33_audit_checksum,
        len(config["records"]),
        len(anomalies),
        len(quarantine),
        state.veto.action,
        state.validation_state,
        lot34_safety(),
        "0" * 64,
    )
    return replace(
        audit,
        audit_checksum=canonical_checksum(audit.payload_without_checksum()),
    )


def build_lot34_artifacts(
    root: Path, code_commit: str
) -> tuple[MarketDataQualityEngineStateV1, MarketDataQualityEngineAuditV1]:
    gate = load_json_object(root / "data/audit/lot34_v3_entry_gate.json")
    config_path = root / "config/data_governance/market_data_quality_engine_v1.json"
    config = load_json_object(config_path)
    _verify_gate(gate)
    _validate_config(config)
    anomalies = detect_anomalies(config)
    states = _build_quality_states(config, anomalies)
    minimum = require_integer(
        config["minimum_quality_bps"], "minimum_quality_bps", minimum=0
    )
    veto = _build_veto(states, anomalies, minimum)
    quarantine = tuple(
        sorted({record_id for item in anomalies for record_id in item.record_ids})
    )
    state = _build_state(root, config, code_commit, anomalies, states, veto, quarantine)
    audit = _build_audit(
        config_path, code_commit, config, state, anomalies, quarantine
    )
    return state, audit


def persist_lot34_artifacts(
    root: Path,
    state: MarketDataQualityEngineStateV1,
    audit: MarketDataQualityEngineAuditV1,
) -> None:
    atomic_write_json(
        root / "data/audit/market_data_quality_engine_lot34.json",
        state.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/market_data_quality_engine_audit_lot34.json",
        audit.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/data_quality_states_lot34.json",
        {
            "schema_version": "data-quality-state-collection-v1",
            "records": [item.to_dict() for item in state.quality_states],
        },
    )
    atomic_write_json(
        root / "data/audit/data_anomalies_lot34.json",
        {
            "schema_version": "data-anomaly-collection-v1",
            "records": [item.to_dict() for item in state.anomalies],
        },
    )
    atomic_write_json(
        root / "data/audit/data_quality_veto_lot34.json",
        state.veto.to_dict(),
    )
