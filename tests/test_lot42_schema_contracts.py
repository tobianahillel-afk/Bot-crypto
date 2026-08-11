from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZONE_SCHEMA = ROOT / "contracts/schemas/liquidity_zone_set_v1.schema.json"
STATE_SCHEMA = ROOT / "contracts/schemas/liquidity_zones_walls_voids_engine_state_v1.schema.json"
AUDIT_SCHEMA = ROOT / "contracts/schemas/liquidity_zones_walls_voids_engine_audit_v1.schema.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lot42_output_schemas_are_closed_at_every_critical_boundary() -> None:
    zone = _load(ZONE_SCHEMA)
    state = _load(STATE_SCHEMA)
    audit = _load(AUDIT_SCHEMA)
    assert zone["additionalProperties"] is False
    assert state["additionalProperties"] is False
    assert audit["additionalProperties"] is False
    assert zone["$defs"]["zone"]["additionalProperties"] is False
    assert zone["$defs"]["void"]["additionalProperties"] is False
    assert state["$defs"]["runContext"]["additionalProperties"] is False
    assert state["$defs"]["lineage"]["additionalProperties"] is False
    assert state["$defs"]["metrics"]["additionalProperties"] is False
    assert state["$defs"]["safety"]["additionalProperties"] is False
    assert audit["$defs"]["runContext"]["additionalProperties"] is False
    assert audit["$defs"]["lineage"]["additionalProperties"] is False
    assert audit["$defs"]["safety"]["additionalProperties"] is False


def test_lot42_schema_locks_non_intent_and_non_execution_semantics() -> None:
    zone = _load(ZONE_SCHEMA)
    state = _load(STATE_SCHEMA)
    zone_props = zone["properties"]
    liquidity_zone = zone["$defs"]["zone"]["properties"]
    liquidity_void = zone["$defs"]["void"]["properties"]
    safety = state["$defs"]["safety"]["properties"]
    assert zone_props["observed_book_only"]["const"] is True
    assert zone_props["participant_intent_inferred"]["const"] is False
    assert liquidity_zone["participant_intent"]["const"] == "NOT_INFERRED"
    assert liquidity_void["participant_intent"]["const"] == "NOT_INFERRED"
    assert safety["trade_allowed"]["const"] is False
    assert safety["execution_allowed"]["const"] is False
    assert safety["approved_size"]["const"] == 0
    assert safety["used_for_decision"]["const"] is False


def test_lot42_schema_locks_decimal_strings_and_classification_vocabulary() -> None:
    zone = _load(ZONE_SCHEMA)
    definitions = zone["$defs"]
    assert definitions["positiveDecimal"]["type"] == "string"
    assert definitions["nonNegativeDecimal"]["type"] == "string"
    classifications = definitions["zone"]["properties"]["classifications"]["items"]["enum"]
    confidence = definitions["zone"]["properties"]["confidence_status"]["enum"]
    assert classifications == ["DISPLAYED_WALL", "PERSISTENT_ZONE"]
    assert confidence == ["HIGH_CONFIDENCE", "LOW_CONFIDENCE", "NOT_APPLICABLE"]
    assert definitions["void"]["properties"]["classification"]["const"] == "LIQUIDITY_VOID"


def test_lot42_schema_locks_runtime_and_config_version() -> None:
    state = _load(STATE_SCHEMA)
    context = state["$defs"]["runContext"]["properties"]
    assert context["runtime_mode"]["const"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert context["config_version"]["const"] == "lot42-liquidity-zones-walls-voids-config-v1"
    assert state["properties"]["validation_state"]["const"] == (
        "VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY"
    )
