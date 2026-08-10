from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "contracts/schemas"


def _load(name: str) -> dict[str, object]:
    payload = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_detector_state_nested_contracts_are_closed() -> None:
    schema = _load("book_integrity_desynchronization_detector_state_v1.schema.json")
    assert schema["additionalProperties"] is False
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    for name in ("run_context", "lineage", "metrics", "safety"):
        nested = definitions[name]
        assert isinstance(nested, dict)
        assert nested["additionalProperties"] is False
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["book_integrity"] == {
        "$ref": "book_integrity_state_v1.schema.json"
    }
    assert properties["book_health_veto"] == {
        "$ref": "book_health_veto_v1.schema.json"
    }


def test_audit_safety_contract_is_closed() -> None:
    schema = _load("book_integrity_desynchronization_detector_audit_v1.schema.json")
    assert schema["additionalProperties"] is False
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    safety = definitions["safety"]
    assert isinstance(safety, dict)
    assert safety["additionalProperties"] is False
    properties = safety["properties"]
    assert isinstance(properties, dict)
    assert properties["trade_allowed"] == {"const": False}
    assert properties["execution_allowed"] == {"const": False}
    assert properties["approved_size"] == {"const": 0}


def test_score_schema_rejects_values_above_100() -> None:
    schema = _load("book_integrity_state_v1.schema.json")
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    score = definitions["score"]
    assert isinstance(score, dict)
    pattern = score["pattern"]
    assert isinstance(pattern, str)
    for accepted in ("0", "0.5", "85", "99.999", "100", "100.0", "100.00"):
        assert re.fullmatch(pattern, accepted) is not None
    for rejected in ("-1", "100.1", "101", "1e2", "NaN", "Infinity"):
        assert re.fullmatch(pattern, rejected) is None


def test_veto_uses_same_bounded_score_contract() -> None:
    schema = _load("book_health_veto_v1.schema.json")
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    score = definitions["score"]
    assert isinstance(score, dict)
    pattern = score["pattern"]
    assert isinstance(pattern, str)
    assert re.fullmatch(pattern, "100") is not None
    assert re.fullmatch(pattern, "100.01") is None
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["critical_failure_consequence"] == {"const": "BLOCK"}
    assert properties["system_threshold_consequence"] == {"const": "PAUSE"}
