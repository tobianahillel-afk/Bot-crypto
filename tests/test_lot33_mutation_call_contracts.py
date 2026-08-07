from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance as engine

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/data_governance/timestamp_clock_timezone_governance_v1.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"
VALID_SHA = "e" * 40


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def first_raw() -> dict[str, Any]:
    records = load(CONFIG_PATH)["records"]
    assert isinstance(records, list)
    value = records[0]
    assert isinstance(value, dict)
    return value


def test_build_raw_uses_every_exact_input_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    string_calls: list[tuple[object, str]] = []
    integer_calls: list[tuple[object, str]] = []
    nullable_string_calls: list[tuple[dict[str, Any], str]] = []
    nullable_integer_calls: list[tuple[dict[str, Any], str]] = []
    metadata_calls: list[object] = []

    def require_string(value: object, field: str) -> str:
        string_calls.append((value, field))
        assert isinstance(value, str)
        return value

    def require_integer(value: object, field: str) -> int:
        integer_calls.append((value, field))
        assert isinstance(value, int)
        return value

    def nullable_string(raw: dict[str, Any], field: str) -> str | None:
        nullable_string_calls.append((raw, field))
        value = raw[field]
        assert value is None or isinstance(value, str)
        return value

    def nullable_integer(raw: dict[str, Any], field: str) -> int | None:
        nullable_integer_calls.append((raw, field))
        value = raw[field]
        assert value is None or isinstance(value, int)
        return value

    def validate_metadata(value: object) -> None:
        metadata_calls.append(value)

    monkeypatch.setattr(engine, "require_string", require_string)
    monkeypatch.setattr(engine, "require_integer", require_integer)
    monkeypatch.setattr(engine, "_nullable_string", nullable_string)
    monkeypatch.setattr(engine, "_nullable_integer", nullable_integer)
    monkeypatch.setattr(engine, "_validate_raw_metadata", validate_metadata)

    raw = first_raw()
    envelope = engine._build_raw(raw)

    assert string_calls == [
        (raw["record_id"], "record_id"),
        (raw["instrument_id"], "instrument_id"),
        (raw["source_id"], "source_id"),
        (raw["raw_timestamp"], "raw_timestamp"),
        (raw["source_timezone"], "source_timezone"),
        (raw["timestamp_precision"], "timestamp_precision"),
        (raw["source_time"], "source_time"),
        (raw["event_time"], "event_time"),
        (raw["receive_time"], "receive_time"),
        (raw["process_time"], "process_time"),
        (raw["available_at"], "available_at"),
        (raw["usable_from"], "usable_from"),
        (raw["clock_domain"], "clock_domain"),
    ]
    assert integer_calls == [
        (raw["sequence_id"], "sequence_id"),
        (raw["revision_id"], "revision_id"),
    ]
    assert nullable_string_calls == [(raw, "exchange_time")]
    assert nullable_integer_calls == [(raw, "monotonic_time")]
    assert metadata_calls == [envelope]


def test_raw_metadata_validates_timezone_and_every_declared_precision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = engine._build_raw(first_raw())
    timezone_calls: list[tuple[str, str]] = []
    precision_calls: list[tuple[str, str, str]] = []

    def validate_timezone(value: str, timezone_name: str) -> None:
        timezone_calls.append((value, timezone_name))

    def validate_precision(value: str, precision: str, field: str) -> None:
        precision_calls.append((value, precision, field))

    monkeypatch.setattr(engine, "validate_source_timezone", validate_timezone)
    monkeypatch.setattr(engine, "validate_precision", validate_precision)

    engine._validate_raw_metadata(envelope)

    assert timezone_calls == [(envelope.raw_timestamp, envelope.source_timezone)]
    assert precision_calls == [
        (envelope.source_time, envelope.timestamp_precision, "source_time"),
        (envelope.event_time, envelope.timestamp_precision, "event_time"),
        (envelope.receive_time, envelope.timestamp_precision, "receive_time"),
        (envelope.process_time, envelope.timestamp_precision, "process_time"),
        (envelope.available_at, envelope.timestamp_precision, "available_at"),
        (envelope.usable_from, envelope.timestamp_precision, "usable_from"),
        (envelope.exchange_time, envelope.timestamp_precision, "exchange_time"),
    ]


def test_normalize_raw_uses_exact_timestamp_and_latency_contracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = engine._build_raw(first_raw())
    canonical_calls: list[tuple[str, str, str]] = []
    signed_calls: list[tuple[str, str]] = []
    duration_calls: list[tuple[str, str, str]] = []
    canonical_values = {
        "source_time": "2026-08-06T19:15:00.100000Z",
        "exchange_time": "2026-08-06T19:15:00.101000Z",
        "event_time": "2026-08-06T19:15:00.101000Z",
        "receive_time": "2026-08-06T19:15:00.151000Z",
        "process_time": "2026-08-06T19:15:00.171000Z",
        "available_at": "2026-08-06T19:15:00.171000Z",
        "usable_from": "2026-08-06T19:15:00.171000Z",
    }
    latency_values = {
        "transport_latency": 50_000,
        "processing_latency": 20_000,
        "total_latency": 70_000,
    }

    def canonical_utc(value: str, precision: str, field: str) -> str:
        canonical_calls.append((value, precision, field))
        return canonical_values[field]

    def signed_duration(start: str, end: str) -> int:
        signed_calls.append((start, end))
        return 1_000

    def duration(start: str, end: str, field: str) -> int:
        duration_calls.append((start, end, field))
        return latency_values[field]

    monkeypatch.setattr(engine, "canonical_utc", canonical_utc)
    monkeypatch.setattr(engine, "signed_duration_us", signed_duration)
    monkeypatch.setattr(engine, "duration_us", duration)

    normalized = engine._normalize_raw(envelope, 17)

    assert canonical_calls == [
        (envelope.source_time, envelope.timestamp_precision, "source_time"),
        (envelope.exchange_time, envelope.timestamp_precision, "exchange_time"),
        (envelope.event_time, envelope.timestamp_precision, "event_time"),
        (envelope.receive_time, envelope.timestamp_precision, "receive_time"),
        (envelope.process_time, envelope.timestamp_precision, "process_time"),
        (envelope.available_at, envelope.timestamp_precision, "available_at"),
        (envelope.usable_from, envelope.timestamp_precision, "usable_from"),
    ]
    assert signed_calls == [
        (canonical_values["source_time"], canonical_values["exchange_time"])
    ]
    assert duration_calls == [
        (
            canonical_values["event_time"],
            canonical_values["receive_time"],
            "transport_latency",
        ),
        (
            canonical_values["receive_time"],
            canonical_values["process_time"],
            "processing_latency",
        ),
        (
            canonical_values["event_time"],
            canonical_values["process_time"],
            "total_latency",
        ),
    ]
    assert normalized.clock_drift_us == 1_000
    assert normalized.transport_latency_us == 50_000
    assert normalized.processing_latency_us == 20_000
    assert normalized.total_latency_us == 70_000
    assert normalized.out_of_order_delay_us == 17


def test_config_validation_uses_exact_three_causal_timestamps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load(CONFIG_PATH)
    string_calls: list[tuple[object, str]] = []
    parse_calls: list[tuple[str, str]] = []
    base = datetime(2026, 8, 6, 19, 15, tzinfo=UTC)
    parsed_values = {
        "event_time": base,
        "available_at": base + timedelta(microseconds=1),
        "generated_at": base + timedelta(microseconds=2),
    }

    def require_string(value: object, field: str) -> str:
        string_calls.append((value, field))
        assert isinstance(value, str)
        return value

    def parse_timestamp(value: str, field: str) -> datetime:
        parse_calls.append((value, field))
        return parsed_values[field]

    monkeypatch.setattr(engine, "require_string", require_string)
    monkeypatch.setattr(engine, "parse_aware_timestamp", parse_timestamp)

    engine._validate_config(config)

    assert string_calls == [
        (config["event_time"], "event_time"),
        (config["available_at"], "available_at"),
        (config["generated_at"], "generated_at"),
    ]
    assert parse_calls == [
        (config["event_time"], "event_time"),
        (config["available_at"], "available_at"),
        (config["generated_at"], "generated_at"),
    ]


def test_run_context_uses_exact_configuration_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load(CONFIG_PATH)
    string_calls: list[tuple[object, str]] = []

    def require_string(value: object, field: str) -> str:
        string_calls.append((value, field))
        assert isinstance(value, str)
        return value

    monkeypatch.setattr(engine, "require_string", require_string)
    context = engine._build_run_context(config, VALID_SHA)

    assert string_calls == [
        (config["run_id"], "run_id"),
        (config["config_version"], "config_version"),
        (config["correlation_id"], "correlation_id"),
    ]
    assert context.to_dict() == {
        "schema_version": "run-context-v1",
        "run_id": config["run_id"],
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "config_version": config["config_version"],
        "code_commit": VALID_SHA,
        "correlation_id": config["correlation_id"],
    }


def test_lineage_uses_exact_paths_and_configuration_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load(CONFIG_PATH)
    string_calls: list[tuple[object, str]] = []
    checksum_calls: list[Path] = []
    checksum_values = {
        ROOT / "data/audit/instrument_registry_lot32.json": "a" * 64,
        ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json": "b" * 64,
        ROOT
        / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json": "c"
        * 64,
    }

    def require_string(value: object, field: str) -> str:
        string_calls.append((value, field))
        assert isinstance(value, str)
        return value

    def checksum(path: Path) -> str:
        checksum_calls.append(path)
        return checksum_values[path]

    monkeypatch.setattr(engine, "require_string", require_string)
    monkeypatch.setattr(engine, "file_checksum", checksum)
    lineage = engine._build_lineage(config, ROOT)

    assert string_calls == [
        (config["lineage_id"], "lineage_id"),
        (config["available_at"], "available_at"),
    ]
    assert checksum_calls == list(checksum_values)
    assert lineage.instrument_registry_path == "data/audit/instrument_registry_lot32.json"
    assert lineage.instrument_registry_checksum == "a" * 64
    assert lineage.lot32_state_checksum == "b" * 64
    assert lineage.lot32_audit_checksum == "c" * 64


def test_allowed_sources_uses_exact_registry_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = load(REGISTRY_PATH)
    string_calls: list[tuple[object, str]] = []

    def require_string(value: object, field: str) -> str:
        string_calls.append((value, field))
        assert isinstance(value, str)
        return value

    monkeypatch.setattr(engine, "require_string", require_string)
    instrument_id, sources = engine._allowed_sources(registry)
    instrument = registry["instruments"][0]
    aliases = instrument["aliases"]

    assert string_calls == [
        (instrument["instrument_id"], "instrument_id"),
        *((alias["source_id"], "source_id") for alias in aliases),
    ]
    assert instrument_id == "btc-eur-spot"
    assert sources == {
        "bitstamp-public-spot-metadata",
        "coinbase-public-spot-metadata",
        "kraken-public-spot-metadata",
    }
