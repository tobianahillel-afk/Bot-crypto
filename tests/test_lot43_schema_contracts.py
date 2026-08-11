from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESILIENCE_SCHEMA = ROOT / "contracts/schemas/book_resilience_state_v1.schema.json"
STATE_SCHEMA = ROOT / "contracts/schemas/book_resilience_replenishment_engine_state_v1.schema.json"
AUDIT_SCHEMA = ROOT / "contracts/schemas/book_resilience_replenishment_engine_audit_v1.schema.json"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot43_all_output_schemas_are_closed() -> None:
    for path in (RESILIENCE_SCHEMA, STATE_SCHEMA, AUDIT_SCHEMA):
        schema = _load(path)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert isinstance(schema["required"], list)
        assert schema["required"]


def test_lot43_resilience_nested_contracts_are_closed() -> None:
    schema = _load(RESILIENCE_SCHEMA)
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    depletion = definitions["depletionEvent"]
    resilience_slice = definitions["resilienceSlice"]
    assert depletion["additionalProperties"] is False
    assert resilience_slice["additionalProperties"] is False
    assert depletion["properties"]["participant_intent"]["const"] == "NOT_INFERRED"
    assert resilience_slice["properties"]["volatility_method"]["const"] == "OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS"


def test_lot43_state_schema_keeps_runtime_and_safety_closed() -> None:
    schema = _load(STATE_SCHEMA)
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    run_context = definitions["runContext"]
    lineage = definitions["lineage"]
    safety = definitions["safety"]
    assert run_context["additionalProperties"] is False
    assert lineage["additionalProperties"] is False
    assert safety["additionalProperties"] is False
    assert run_context["properties"]["runtime_mode"]["const"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert safety["properties"]["trade_allowed"]["const"] is False
    assert safety["properties"]["execution_allowed"]["const"] is False
    assert safety["properties"]["approved_size"]["const"] == 0


def test_lot43_schema_versions_and_validation_state_are_exact() -> None:
    resilience = _load(RESILIENCE_SCHEMA)
    state = _load(STATE_SCHEMA)
    audit = _load(AUDIT_SCHEMA)
    assert resilience["properties"]["schema_version"]["const"] == "book-resilience-state-v1"
    assert state["properties"]["schema_version"]["const"] == "book-resilience-replenishment-engine-state-v1"
    assert state["properties"]["validation_state"]["const"] == "VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY"
    assert audit["properties"]["schema_version"]["const"] == "book-resilience-replenishment-engine-audit-v1"


def test_lot43_replenishment_and_resilience_enums_are_closed() -> None:
    schema = _load(RESILIENCE_SCHEMA)
    definitions = schema["$defs"]
    event = definitions["depletionEvent"]
    resilience_slice = definitions["resilienceSlice"]
    assert set(event["properties"]["replenishment_kind"]["enum"]) == {
        "NONE",
        "SAME_PRICE",
        "ADJACENT_PRICE",
        "MID_SHIFT",
    }
    assert set(event["properties"]["max_window_status"]["enum"]) == {
        "REPLENISHED",
        "MID_SHIFTED",
        "EXPIRED_NO_REPLENISHMENT",
        "PENDING_WINDOW",
    }
    assert set(resilience_slice["properties"]["resilience_status"]["enum"]) == {
        "NO_EVENTS",
        "RESILIENT",
        "FRAGILE",
        "SHIFTED",
        "PENDING",
        "PARTIAL",
    }


def test_lot43_audit_schema_links_only_frozen_contracts() -> None:
    schema = _load(AUDIT_SCHEMA)
    properties = schema["properties"]
    assert properties["run_context"]["$ref"].endswith("#/$defs/runContext")
    assert properties["lineage"]["$ref"].endswith("#/$defs/lineage")
    assert properties["safety"]["$ref"].endswith("#/$defs/safety")
    assert properties["state_output_checksum"]["pattern"] == "^[0-9a-f]{64}$"
    assert properties["resilience_checksum"]["pattern"] == "^[0-9a-f]{64}$"
