from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.validate_lot44_entry_gate as gate_validator
from scripts.validate_lot44_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_INPUTS,
    EXPECTED_OUTPUTS,
    Lot44EntryGateError,
    canonical_checksum,
    roadmap_record,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot44_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot44_v4_entry_gate_v1.schema.json"
LOT45_GATE_PATH = ROOT / "data/audit/lot45_v4_entry_gate.json"
LOT45_GATE_CHECKSUM = "15ca4d69e59a0898f32eb9cbe558571ecf00ae496ec5d41075da1124393d4468"


@pytest.fixture(autouse=True)
def _isolate_historical_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gate_validator,
        "validate_lot43_post_merge",
        lambda: {
            "status": "PASS",
            "verdict": "GO_LOT43_POST_MERGE",
            "release": "0.43.0",
            "post_merge_audit_checksum": gate_validator.EXPECTED_POST_MERGE_CHECKSUM,
            "lot44_status": "PLANNED_LOCKED",
            "lot44_implementation_started": False,
            "trade_allowed": False,
            "execution_allowed": False,
            "approved_size": 0,
        },
    )
    monkeypatch.setattr(gate_validator, "LOT44_FORBIDDEN_IMPLEMENTATION_PATHS", ())
    monkeypatch.setattr(gate_validator, "LOT45_FORBIDDEN_IMPLEMENTATION_PATHS", ())


def _tamper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutate) -> None:
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    mutate(payload)
    body = dict(payload)
    body.pop("output_checksum", None)
    payload["output_checksum"] = canonical_checksum(body)
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(gate_validator, "EXPECTED_GATE_CHECKSUM", payload["output_checksum"])


def test_exact_gate_passes() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["gate_status"] == "GO_LOT44_IMPLEMENTATION_ENTRY"
    assert result["base_commit"] == "7a207a16e7aa543f9f7c241828f8ea5ae9ed0407"
    assert result["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert result["target_lot"] == 44
    assert result["next_locked_lot"] == 45
    assert result["future_locked_lot"] == 46
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0


def test_checksum_is_canonical_and_tamper_evident() -> None:
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    body = dict(payload)
    actual = body.pop("output_checksum")
    assert actual == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(body) == actual
    body["implementation_started"] = True
    assert canonical_checksum(body) != actual


def test_canonical_roadmap_rows_are_exact() -> None:
    lot44 = roadmap_record(45)
    lot45 = roadmap_record(46)
    lot46 = roadmap_record(47)
    assert lot44["title"] == "Trades & Aggressor Classification Schema"
    assert lot44["status"] == "PLANNED_LOCKED"
    assert set(lot44["input_contracts"]) == EXPECTED_INPUTS
    assert set(lot44["output_contracts"]) == EXPECTED_OUTPUTS
    assert lot45["title"] == "Order Flow, Delta & CVD Engine"
    assert lot45["status"] == "PLANNED_LOCKED"
    assert lot46["title"] == "Trade Classification Confidence Engine"
    assert lot46["status"] == "PLANNED_LOCKED"


def test_schema_is_closed_and_safety_locked() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    props = schema["properties"]
    assert schema["additionalProperties"] is False
    assert props["target_lot"]["const"] == 44
    assert props["next_lot"]["const"] == 45
    assert props["prerequisites"]["additionalProperties"] is False
    safety = props["safety"]
    assert safety["additionalProperties"] is False
    assert safety["properties"]["trade_allowed"]["const"] is False
    assert safety["properties"]["execution_allowed"]["const"] is False
    assert safety["properties"]["approved_size"]["const"] == 0


def test_scope_distinguishes_lot44_confidence_state_from_lot46_engine() -> None:
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert "AGGRESSOR_CONFIDENCE_STATE_V1" in payload["allowed_scope"]
    assert "TRADE_CLASSIFICATION_CONFIDENCE_ENGINE" in payload["forbidden_scope"]
    assert "ORDER_FLOW_DELTA_CVD_ENGINE" in payload["forbidden_scope"]
    assert "UNKNOWN_VOLUME_SUPPRESSION" in payload["forbidden_scope"]
    assert "PARTICIPANT_INTENT_AS_FACT" in payload["forbidden_scope"]


def test_lot43_historical_gate_isolated_from_authorized_lot44_current_tree() -> None:
    historical_test = (ROOT / "tests/test_lot43_v4_entry_gate.py").read_text(encoding="utf-8")
    assert 'monkeypatch.setattr(gate_validator, "LOT44_FORBIDDEN_IMPLEMENTATION_PATHS", ())' in historical_test


def test_authorized_lot45_current_tree_is_isolated_from_historical_gate() -> None:
    payload = json.loads(LOT45_GATE_PATH.read_text(encoding="utf-8"))
    body = dict(payload)
    actual = body.pop("gate_checksum")
    assert actual == LOT45_GATE_CHECKSUM
    assert canonical_checksum(body) == actual
    assert payload["gate_status"] == "GO_LOT45_IMPLEMENTATION_ENTRY"
    assert payload["post_merge_verdict"] == "GO_LOT44_POST_MERGE"
    assert payload["next_lot"] == 46
    assert payload["next_lot_status"] == "PLANNED_LOCKED"


def test_lot46_implementation_remains_absent_from_canonical_roadmap() -> None:
    lot46 = roadmap_record(47)
    implementation_files = lot46["implementation_files"]
    assert len(implementation_files) == 9
    for relative in implementation_files:
        assert not (ROOT / relative).exists()


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda p: p["forbidden_scope"].remove("ORDER_FLOW_DELTA_CVD_ENGINE"), "forbidden scope"),
        (lambda p: p["forbidden_scope"].remove("UNKNOWN_VOLUME_SUPPRESSION"), "forbidden scope"),
        (lambda p: p["forbidden_scope"].remove("PARTICIPANT_INTENT_AS_FACT"), "forbidden scope"),
        (lambda p: p["safety"].__setitem__("trade_allowed", True), "safety boundary"),
        (lambda p: p["canonical_roadmap"].__setitem__("source_line", 44), "roadmap line binding"),
        (lambda p: p["prerequisites"].__setitem__("mutation_score_percent", 99.99), "prerequisite evidence"),
        (lambda p: p["required_outputs"].remove("ClassifiedTradeV1"), "gate outputs"),
    ],
)
def test_gate_rejects_tampering(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutate, match: str) -> None:
    _tamper(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot44EntryGateError, match=match):
        validate()
