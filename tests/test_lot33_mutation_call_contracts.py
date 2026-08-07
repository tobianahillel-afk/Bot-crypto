from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

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


def wrap(
    monkeypatch: Any,
    name: str,
    calls: list[tuple[object, ...]],
) -> Callable[..., object]:
    original = getattr(engine, name)

    def spy(*args: object, **kwargs: object) -> object:
        calls.append((*args, *(tuple(sorted(kwargs.items())) if kwargs else ())))
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, name, spy)
    return original


def test_build_raw_uses_every_exact_input_field(monkeypatch: object) -> None:
    string_calls: list[tuple[object, ...]] = []
    integer_calls: list[tuple[object, ...]] = []
    nullable_string_calls: list[tuple[object, ...]] = []
    nullable_integer_calls: list[tuple[object, ...]] = []
    metadata_calls: list[tuple[object, ...]] = []
    wrap(monkeypatch, "require_string", string_calls)
    wrap(monkeypatch, "require_integer", integer_calls)
    wrap(monkeypatch, "_nullable_string", nullable_string_calls)
    wrap(monkeypatch, "_nullable_integer", nullable_integer_calls)
    wrap(monkeypatch, "_validate_raw_metadata", metadata_calls)

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
    assert metadata_calls == [(envelope,)]


def test_raw_metadata_validates_timezone_and_every_declared_precision(
    monkeypatch: object,
) -> None:
    envelope = engine._build_raw(first_raw())
    timezone_calls: list[tuple[object, ...]] = []
    precision_calls: list[tuple[object, ...]] = []
    wrap(monkeypatch, "validate_source_timezone", timezone_calls)
    wrap(monkeypatch, "validate_precision", precision_calls)

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
    monkeypatch: object,
) -> None:
    envelope = engine._build_raw(first_raw())
    canonical_calls: list[tuple[object, ...]] = []
    signed_calls: list[tuple[object, ...]] = []
    duration_calls: list[tuple[object, ...]] = []
    wrap(monkeypatch, "canonical_utc", canonical_calls)
    wrap(monkeypatch, "signed_duration_us", signed_calls)
    wrap(monkeypatch, "duration_us", duration_calls)

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
    assert signed_calls == [(normalized.source_time_utc, normalized.exchange_time_utc)]
    assert duration_calls == [
        (normalized.event_time_utc, normalized.receive_time_utc, "transport_latency"),
        (normalized.receive_time_utc, normalized.process_time_utc, "processing_latency"),
        (normalized.event_time_utc, normalized.process_time_utc, "total_latency"),
    ]
    assert normalized.out_of_order_delay_us == 17


def test_config_validation_uses_exact_three_causal_timestamps(
    monkeypatch: object,
) -> None:
    config = load(CONFIG_PATH)
    string_calls: list[tuple[object, ...]] = []
    parse_calls: list[tuple[object, ...]] = []
    wrap(monkeypatch, "require_string", string_calls)
    wrap(monkeypatch, "parse_aware_timestamp", parse_calls)

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


def test_run_context_lineage_and_allowed_sources_use_exact_dependencies(
    monkeypatch: object,
) -> None:
    config = load(CONFIG_PATH)
    registry = load(REGISTRY_PATH)
    string_calls: list[tuple[object, ...]] = []
    checksum_calls: list[tuple[object, ...]] = []
    wrap(monkeypatch, "require_string", string_calls)
    wrap(monkeypatch, "file_checksum", checksum_calls)

    context = engine._build_run_context(config, VALID_SHA)
    lineage = engine._build_lineage(config, ROOT)
    instrument_id, sources = engine._allowed_sources(registry)

    assert context.to_dict() == {
        "schema_version": "run-context-v1",
        "run_id": config["run_id"],
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "config_version": config["config_version"],
        "code_commit": VALID_SHA,
        "correlation_id": config["correlation_id"],
    }
    assert string_calls[:3] == [
        (config["run_id"], "run_id"),
        (config["config_version"], "config_version"),
        (config["correlation_id"], "correlation_id"),
    ]
    assert string_calls[3] == (config["lineage_id"], "lineage_id")
    assert string_calls[4] == (config["available_at"], "available_at")
    assert checksum_calls == [
        (ROOT / "data/audit/instrument_registry_lot32.json",),
        (ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json",),
        (
            ROOT
            / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json",
        ),
    ]
    assert lineage.instrument_registry_path == "data/audit/instrument_registry_lot32.json"
    assert instrument_id == "btc-eur-spot"
    assert sources == {
        "bitstamp-public-spot-metadata",
        "coinbase-public-spot-metadata",
        "kraken-public-spot-metadata",
    }
