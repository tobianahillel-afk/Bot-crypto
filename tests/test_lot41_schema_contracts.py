from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_SCHEMA = ROOT / "contracts/schemas/book_feature_state_v1.schema.json"
STATE_SCHEMA = ROOT / "contracts/schemas/spread_depth_imbalance_engine_state_v1.schema.json"
AUDIT_SCHEMA = ROOT / "contracts/schemas/spread_depth_imbalance_engine_audit_v1.schema.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lot41_output_schemas_are_closed() -> None:
    feature = _load(FEATURE_SCHEMA)
    state = _load(STATE_SCHEMA)
    audit = _load(AUDIT_SCHEMA)
    assert feature["additionalProperties"] is False
    assert state["additionalProperties"] is False
    assert audit["additionalProperties"] is False
    assert feature["$defs"]["topOfBook"]["additionalProperties"] is False
    assert feature["$defs"]["depthBand"]["additionalProperties"] is False
    assert feature["$defs"]["bookQuality"]["additionalProperties"] is False
    assert state["$defs"]["runContext"]["additionalProperties"] is False
    assert state["$defs"]["lineage"]["additionalProperties"] is False
    assert state["$defs"]["safety"]["additionalProperties"] is False


def test_lot41_schema_locks_runtime_safety_and_observed_only_semantics() -> None:
    feature = _load(FEATURE_SCHEMA)
    state = _load(STATE_SCHEMA)
    run_context = state["$defs"]["runContext"]["properties"]
    safety = state["$defs"]["safety"]["properties"]
    assert run_context["runtime_mode"]["const"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert safety["trade_allowed"]["const"] is False
    assert safety["execution_allowed"]["const"] is False
    assert safety["approved_size"]["const"] == 0
    assert safety["used_for_decision"]["const"] is False
    assert feature["properties"]["observed_depth_only"]["const"] is True
    assert feature["properties"]["extrapolated"]["const"] is False
    assert feature["$defs"]["depthBand"]["properties"]["coverage_status"]["const"] == "OBSERVED_LEVELS_ONLY"


def test_lot41_schema_locks_zero_denominator_representation() -> None:
    feature = _load(FEATURE_SCHEMA)
    depth_band = feature["$defs"]["depthBand"]["properties"]
    assert depth_band["imbalance_status"]["enum"] == ["DEFINED", "UNDEFINED_ZERO_DENOMINATOR"]
    assert {option.get("type") for option in depth_band["imbalance"]["oneOf"]} >= {None, "null"}
