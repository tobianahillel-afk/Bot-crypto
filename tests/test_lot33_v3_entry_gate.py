from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import scripts.validate_lot33_entry_gate as gate_validator
from scripts.validate_lot33_entry_gate import (
    EXPECTED_CHECKSUM,
    EXPECTED_FIELDS,
    Lot33EntryGateError,
    canonical_checksum,
    load_json,
    validate_gate,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot33_v3_entry_gate.json"


def recompute(gate: dict[str, object]) -> str:
    payload = dict(gate)
    payload.pop("output_checksum", None)
    checksum = canonical_checksum(payload)
    gate["output_checksum"] = checksum
    return checksum


def test_lot33_entry_gate_is_valid_and_fail_closed() -> None:
    result = validate_gate(load_json(GATE_PATH))
    assert result == {
        "schema_version": "lot33-entry-gate-validation-v1",
        "status": "PASS",
        "target_lot": 33,
        "gate_status": "GO_LOT33_IMPLEMENTATION_ENTRY",
        "timestamp_field_count": 14,
        "temporal_invariant_count": 14,
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "output_checksum": EXPECTED_CHECKSUM,
    }


def test_lot33_entry_gate_checksum_is_independently_recomputed() -> None:
    gate = load_json(GATE_PATH)
    payload = dict(gate)
    checksum = payload.pop("output_checksum")
    assert checksum == EXPECTED_CHECKSUM
    assert canonical_checksum(payload) == EXPECTED_CHECKSUM


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("gate_status",), "NO_GO", "gate field"),
        (("target_lot",), 34, "gate field"),
        (("runtime_mode",), "LIVE", "gate field"),
        (("human_decision",), "UNKNOWN", "gate field"),
        (("implementation_started",), True, "gate field"),
        (("next_lot_status",), "IMPLEMENTATION_STARTED", "gate field"),
        (("safety", "external_connectivity_allowed"), True, "external_connectivity"),
        (("safety", "network_ingestion_allowed"), True, "network_ingestion"),
        (("safety", "trade_allowed"), True, "trade_allowed"),
        (("safety", "execution_allowed"), True, "execution_allowed"),
        (("safety", "approved_size"), 1, "approved size"),
    ],
)
def test_lot33_entry_gate_rejects_scope_or_permission_changes(
    path: tuple[str, ...],
    value: object,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = copy.deepcopy(load_json(GATE_PATH))
    target = gate
    for key in path[:-1]:
        nested = target[key]
        assert isinstance(nested, dict)
        target = nested
    target[path[-1]] = value
    semantic_checksum = recompute(gate)
    monkeypatch.setattr(gate_validator, "EXPECTED_CHECKSUM", semantic_checksum)
    with pytest.raises(Lot33EntryGateError, match=message):
        validate_gate(gate)


def test_lot33_entry_gate_rejects_unrecomputed_tampering() -> None:
    gate = load_json(GATE_PATH)
    gate["target_lot"] = 34
    with pytest.raises(Lot33EntryGateError, match="checksum"):
        validate_gate(gate)


def test_lot33_timestamp_fields_are_exact_and_unique() -> None:
    gate = load_json(GATE_PATH)
    assert tuple(gate["required_timestamp_fields"]) == EXPECTED_FIELDS
    assert len(set(gate["required_timestamp_fields"])) == 14
    assert len(set(gate["required_temporal_invariants"])) == 14


def test_lot33_gate_schema_and_docs_are_strict() -> None:
    schema = json.loads(
        (ROOT / "contracts/schemas/lot33_v3_entry_gate_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    document = (ROOT / "docs/LOT_33_V3_ENTRY_GATE.md").read_text(encoding="utf-8")
    report = (ROOT / "reports/lot_33_v3_entry_gate_report.md").read_text(encoding="utf-8")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["safety"]["additionalProperties"] is False
    assert "GO_LOT33_IMPLEMENTATION_ENTRY" in document
    assert "timezone-naive" in document
    assert "Lot 34 remains `PLANNED_LOCKED`" in report
