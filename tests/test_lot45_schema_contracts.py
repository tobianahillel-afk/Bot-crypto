from __future__ import annotations

import json
import re
from pathlib import Path

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_GATE_MERGE,
    EXPECTED_LOT44_AUDIT,
    EXPECTED_LOT44_CONFIDENCE,
    EXPECTED_LOT44_POST_MERGE,
    EXPECTED_LOT44_STATE,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    lot45_safety,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "contracts/schemas"
NONNEGATIVE_DECIMAL = r"^(?:0|[1-9][0-9]*(?:\.[0-9]*[1-9])?|0\.[0-9]*[1-9])$"
POSITIVE_DECIMAL = r"^(?:[1-9][0-9]*(?:\.[0-9]*[1-9])?|0\.[0-9]*[1-9])$"
SIGNED_DECIMAL = r"^(?:0|-?[1-9][0-9]*(?:\.[0-9]*[1-9])?|-?0\.[0-9]*[1-9])$"
UNIT_RATIO = r"^(?:0|1|0\.[0-9]*[1-9])$"
SIGNED_UNIT_RATIO = r"^(?:0|1|-1|0\.[0-9]*[1-9]|-0\.[0-9]*[1-9])$"
UTC_TIMESTAMP = (
    r"^(?!0000-)(?:"
    r"(?:[0-9]{4}-(?:(?:01|03|05|07|08|10|12)-(?:0[1-9]|[12][0-9]|3[01])"
    r"|(?:04|06|09|11)-(?:0[1-9]|[12][0-9]|30)|02-(?:0[1-9]|1[0-9]|2[0-8])))"
    r"|(?:(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|(?:[02468][048]|[13579][26])00)-02-29)"
    r")T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z$"
)
WINDOWABLE_EVENT_TIMESTAMP = (
    r"^(?!0000-)(?!9999-12-31T23:59:59\.)(?:"
    r"(?:[0-9]{4}-(?:(?:01|03|05|07|08|10|12)-(?:0[1-9]|[12][0-9]|3[01])"
    r"|(?:04|06|09|11)-(?:0[1-9]|[12][0-9]|30)|02-(?:0[1-9]|1[0-9]|2[0-8])))"
    r"|(?:(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|(?:[02468][048]|[13579][26])00)-02-29)"
    r")T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z$"
)


def _schema(name: str) -> dict[str, object]:
    value = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot45_engine_state_schema_is_closed_and_lineage_bound() -> None:
    schema = _schema("order_flow_delta_cvd_engine_state_v1.schema.json")
    assert schema["additionalProperties"] is False
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["schema_version"]["const"] == "order-flow-delta-cvd-engine-state-v1"
    assert properties["validation_state"]["const"] == "VALIDATED_OFFLINE_ORDER_FLOW_DELTA_CVD_ONLY"
    assert properties["policy_version"]["const"] == "lot45-order-flow-delta-cvd-policy-v1"
    assert properties["window_policy_version"]["const"] == "lot45-event-time-tumbling-v1"
    assert properties["session_policy_version"]["const"] == "lot45-utc-day-session-v1"

    lineage = properties["lineage"]
    assert lineage["additionalProperties"] is False
    lineage_props = lineage["properties"]
    assert lineage_props["entry_gate_merge_commit"]["const"] == EXPECTED_GATE_MERGE
    assert lineage_props["lot44_state_checksum"]["const"] == EXPECTED_LOT44_STATE
    assert lineage_props["lot44_audit_checksum"]["const"] == EXPECTED_LOT44_AUDIT
    assert lineage_props["lot44_confidence_checksum"]["const"] == EXPECTED_LOT44_CONFIDENCE
    assert lineage_props["lot44_post_merge_checksum"]["const"] == EXPECTED_LOT44_POST_MERGE


def test_lot45_engine_state_schema_encodes_exact_fail_closed_safety() -> None:
    schema = _schema("order_flow_delta_cvd_engine_state_v1.schema.json")
    properties = schema["properties"]
    assert isinstance(properties, dict)
    safety = properties["safety"]
    assert safety["additionalProperties"] is False
    assert set(safety["required"]) == set(lot45_safety())
    for field, expected in lot45_safety().items():
        assert safety["properties"][field]["const"] == expected


def test_lot45_audit_schema_is_closed_and_frozen_to_upstream_proofs() -> None:
    schema = _schema("order_flow_delta_cvd_engine_audit_v1.schema.json")
    assert schema["additionalProperties"] is False
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["schema_version"]["const"] == "order-flow-delta-cvd-engine-audit-v1"
    assert properties["entry_gate_checksum"]["const"] == EXPECTED_GATE_CHECKSUM
    assert properties["lot44_state_checksum"]["const"] == EXPECTED_LOT44_STATE
    assert properties["lot44_audit_checksum"]["const"] == EXPECTED_LOT44_AUDIT
    assert properties["lot44_confidence_checksum"]["const"] == EXPECTED_LOT44_CONFIDENCE
    assert properties["lot44_post_merge_checksum"]["const"] == EXPECTED_LOT44_POST_MERGE
    assert properties["validation_state"]["const"] == "VALIDATED_OFFLINE_ORDER_FLOW_DELTA_CVD_ONLY"


def test_order_flow_schema_requires_unknown_and_conservation_observables() -> None:
    schema = _schema("order_flow_state_v1.schema.json")
    assert schema["additionalProperties"] is False
    required = set(schema["required"])
    assert {
        "unknown_trades_total",
        "unknown_volume",
        "unknown_volume_ratio",
        "classification_coverage",
        "confidence_weighted_volume",
        "confidence_weighted_coverage",
        "signed_delta",
        "order_flow_checksum",
    } <= required
    window = schema["properties"]["windows"]["items"]
    assert window["additionalProperties"] is False
    assert {
        "unknown_volume",
        "signed_delta",
        "signed_imbalance",
        "classification_coverage",
        "confidence_weighted_volume",
        "confidence_weighted_coverage",
        "delta_impulse",
        "window_checksum",
    } <= set(window["required"])


def test_decimal_schema_fields_are_canonical_and_bounded() -> None:
    schema = _schema("order_flow_state_v1.schema.json")
    properties = schema["properties"]
    window_properties = properties["windows"]["items"]["properties"]

    assert properties["total_volume"]["pattern"] == POSITIVE_DECIMAL
    for field in (
        "buy_volume",
        "sell_volume",
        "unknown_volume",
        "confidence_weighted_volume",
    ):
        assert properties[field]["pattern"] == NONNEGATIVE_DECIMAL
    assert properties["signed_delta"]["pattern"] == SIGNED_DECIMAL
    for field in ("unknown_volume_ratio", "classification_coverage", "confidence_weighted_coverage"):
        assert properties[field]["pattern"] == UNIT_RATIO

    assert window_properties["total_volume"]["pattern"] == POSITIVE_DECIMAL
    for field in (
        "buy_volume",
        "sell_volume",
        "unknown_volume",
        "confidence_weighted_volume",
    ):
        assert window_properties[field]["pattern"] == NONNEGATIVE_DECIMAL
    for field in ("signed_delta", "delta_impulse"):
        assert window_properties[field]["pattern"] == SIGNED_DECIMAL
    assert window_properties["signed_imbalance"]["pattern"] == SIGNED_UNIT_RATIO
    for field in ("classification_coverage", "confidence_weighted_coverage"):
        assert window_properties[field]["pattern"] == UNIT_RATIO

    cvd_schema = _schema("cvd_series_v1.schema.json")
    point_properties = cvd_schema["properties"]["points"]["items"]["properties"]
    assert point_properties["signed_delta"]["pattern"] == SIGNED_DECIMAL
    assert point_properties["cvd"]["pattern"] == SIGNED_DECIMAL

    for invalid in ("garbage", "NaN", "Infinity", "1e3", "-0", "01", "1.0", "0.10"):
        assert re.fullmatch(SIGNED_DECIMAL, invalid) is None
    for invalid in ("-1", "1.1", "2", "NaN", "0.10"):
        assert re.fullmatch(UNIT_RATIO, invalid) is None
    for invalid in ("-1.1", "1.1", "2", "NaN", "-0"):
        assert re.fullmatch(SIGNED_UNIT_RATIO, invalid) is None
    for valid in ("0", "1", "-1", "0.125", "-0.125", "123.45", "-123.45"):
        assert re.fullmatch(SIGNED_DECIMAL, valid) is not None


def _timestamp_schema_nodes() -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    state_schema = _schema("order_flow_delta_cvd_engine_state_v1.schema.json")
    state_properties = state_schema["properties"]
    flow_schema = _schema("order_flow_state_v1.schema.json")
    window_properties = flow_schema["properties"]["windows"]["items"]["properties"]
    cvd_schema = _schema("cvd_series_v1.schema.json")
    point_properties = cvd_schema["properties"]["points"]["items"]["properties"]
    general_nodes = (
        state_properties["receive_time"],
        state_properties["generated_at"],
        state_properties["lineage"]["properties"]["available_at"],
        window_properties["window_start"],
        window_properties["window_end"],
        window_properties["receive_time"],
    )
    event_nodes = (
        state_properties["event_time"],
        window_properties["event_time"],
        point_properties["event_time"],
    )
    return general_nodes, event_nodes


def test_timestamp_schema_fields_use_calendar_valid_canonical_utc_text() -> None:
    general_nodes, event_nodes = _timestamp_schema_nodes()
    for node in general_nodes:
        assert node["pattern"] == UTC_TIMESTAMP
        assert node["format"] == "date-time"
    for node in event_nodes:
        assert node["pattern"] == WINDOWABLE_EVENT_TIMESTAMP
        assert node["format"] == "date-time"

    for invalid in (
        "garbageZ",
        "0000-01-01T00:00:00.000000Z",
        "2026-08-06T19:18:40Z",
        "2026-08-06T19:18:40.000000+00:00",
        "2026-08-06 19:18:40.000000Z",
        "2026-08-06T25:18:40.000000Z",
        "2026-08-06T19:18:40.000000z",
        "2026-02-29T19:18:40.000000Z",
        "2026-02-31T19:18:40.000000Z",
        "2026-04-31T19:18:40.000000Z",
        "1900-02-29T19:18:40.000000Z",
        "2100-02-29T19:18:40.000000Z",
    ):
        assert re.fullmatch(UTC_TIMESTAMP, invalid) is None
        assert re.fullmatch(WINDOWABLE_EVENT_TIMESTAMP, invalid) is None

    for valid in (
        "2026-08-06T19:18:40.000000Z",
        "2024-02-29T00:00:00.000000Z",
        "2000-02-29T23:59:59.999999Z",
        "2400-02-29T00:00:00.000001Z",
        "9999-12-31T23:59:59.999999Z",
    ):
        assert re.fullmatch(UTC_TIMESTAMP, valid) is not None

    for invalid_event in (
        "9999-12-31T23:59:59.000000Z",
        "9999-12-31T23:59:59.100000Z",
        "9999-12-31T23:59:59.999999Z",
    ):
        assert re.fullmatch(WINDOWABLE_EVENT_TIMESTAMP, invalid_event) is None

    assert re.fullmatch(
        WINDOWABLE_EVENT_TIMESTAMP,
        "9999-12-31T23:59:58.999999Z",
    ) is not None


def test_cvd_schema_fixes_session_policy_and_checksum() -> None:
    schema = _schema("cvd_series_v1.schema.json")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["session_policy_version"]["const"] == "lot45-utc-day-session-v1"
    assert "cvd_checksum" in schema["required"]
    point = schema["properties"]["points"]["items"]
    assert point["additionalProperties"] is False
    assert {"event_time", "session_id", "window_checksum", "signed_delta", "cvd"} <= set(point["required"])


def test_all_lot45_schemas_are_valid_json_objects() -> None:
    for name in (
        "order_flow_delta_cvd_engine_state_v1.schema.json",
        "order_flow_delta_cvd_engine_audit_v1.schema.json",
        "order_flow_state_v1.schema.json",
        "cvd_series_v1.schema.json",
    ):
        schema = _schema(name)
        assert schema["type"] == "object"
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
