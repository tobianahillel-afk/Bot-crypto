from __future__ import annotations

import json
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
        "confidence_weighted_coverage",
        "delta_impulse",
        "window_checksum",
    } <= set(window["required"])


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
