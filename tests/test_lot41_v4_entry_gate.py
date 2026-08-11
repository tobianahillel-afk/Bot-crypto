from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import scripts.validate_lot41_entry_gate as gate_validator
from scripts.validate_lot41_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_INPUTS,
    EXPECTED_OUTPUTS,
    Lot41EntryGateError,
    canonical_checksum,
    roadmap_record,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot41_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot41_v4_entry_gate_v1.schema.json"


@pytest.fixture(autouse=True)
def _isolate_historical_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replay immutable gate facts without requiring Lot 41 absence after gate merge."""
    monkeypatch.setattr(
        gate_validator,
        "validate_lot40_post_merge",
        lambda: {
            "status": "PASS",
            "verdict": "GO_LOT40_POST_MERGE",
            "project_version": "0.40.0",
            "latest_implemented_lot": 40,
            "next_lot": 41,
            "next_lot_status": "PLANNED_LOCKED",
        },
    )
    monkeypatch.setattr(gate_validator, "LOT41_FORBIDDEN_IMPLEMENTATION_PATHS", ())


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _install_tampered_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    body = dict(payload)
    body.pop("output_checksum", None)
    payload["output_checksum"] = canonical_checksum(body)
    path = tmp_path / "gate.json"
    _write_json(path, payload)
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(gate_validator, "EXPECTED_GATE_CHECKSUM", payload["output_checksum"])


def test_lot41_entry_gate_passes_exact_audited_state() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["gate_status"] == "GO_LOT41_IMPLEMENTATION_ENTRY"
    assert result["base_commit"] == "20975b505c7f8b527751fb5d3bce034c6e55dcc2"
    assert result["current_version"] == "0.40.0"
    assert result["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert result["target_lot"] == 41
    assert result["next_locked_lot"] == 42
    assert result["next_lot_status"] == "PLANNED_LOCKED"
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0


def test_lot41_gate_checksum_is_canonical_and_tamper_evident() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    body = dict(gate)
    checksum = body.pop("output_checksum")
    assert checksum == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(body) == checksum
    body["implementation_started"] = True
    assert canonical_checksum(body) != checksum


def test_lot41_and_lot42_canonical_roadmap_rows_are_exact() -> None:
    lot41 = roadmap_record(42)
    lot42 = roadmap_record(43)
    assert lot41["lot_id"] == "Lot 41"
    assert lot41["lot_number"] == 41
    assert lot41["title"] == "Spread, Depth & Imbalance Engine"
    assert lot41["responsible_component"] == "MicrostructureDomain"
    assert lot41["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert set(lot41["input_contracts"]) == EXPECTED_INPUTS
    assert set(lot41["output_contracts"]) == EXPECTED_OUTPUTS
    assert lot42["lot_id"] == "Lot 42"
    assert lot42["title"] == "Liquidity Zones, Walls & Voids Engine"
    assert lot42["status"] == "PLANNED_LOCKED"


def test_lot41_gate_schema_is_closed_and_lot42_locked() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    props = schema["properties"]
    assert props["target_lot"]["const"] == 41
    assert props["base_commit"]["const"] == "20975b505c7f8b527751fb5d3bce034c6e55dcc2"
    assert props["current_version"]["const"] == "0.40.0"
    assert props["next_lot"]["const"] == 42
    assert props["next_lot_status"]["const"] == "PLANNED_LOCKED"
    assert props["prerequisites"]["additionalProperties"] is False
    safety = props["safety"]
    assert safety["additionalProperties"] is False
    assert safety["properties"]["trade_allowed"]["const"] is False
    assert safety["properties"]["execution_allowed"]["const"] is False
    assert safety["properties"]["approved_size"]["const"] == 0


def test_lot41_historical_gate_keeps_lot42_locked() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert gate["implementation_started"] is False
    assert gate["next_lot"] == 42
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    for path in gate_validator.LOT42_FORBIDDEN_IMPLEMENTATION_PATHS:
        assert not path.exists()


def test_lot41_gate_rejects_lot42_scope_unlock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["forbidden_scope"].remove("LIQUIDITY_ZONE_WALL_VOID_INFERENCE")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot41EntryGateError, match="forbidden scope"):
        validate()


def test_lot41_gate_rejects_trading_permission(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["safety"]["trade_allowed"] = True
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot41EntryGateError, match="safety boundary"):
        validate()


def test_lot41_gate_rejects_roadmap_binding_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["canonical_roadmap"]["source_line"] = 41
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot41EntryGateError, match="roadmap line binding"):
        validate()


def test_lot41_gate_rejects_lot40_prerequisite_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["prerequisites"]["mutation_score_percent"] = 99.99
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot41EntryGateError, match="prerequisite evidence"):
        validate()


def test_lot41_gate_rejects_required_output_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["required_outputs"].remove("BookFeatureStateV1")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot41EntryGateError, match="gate outputs"):
        validate()
