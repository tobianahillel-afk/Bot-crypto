from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts.validate_lot45_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_OUTPUTS,
    GATE_PATH,
    LOT45_FORBIDDEN_BEFORE_GATE,
    LOT46_FORBIDDEN,
    SCHEMA_PATH,
    Lot45EntryGateError,
    git,
    load,
    locate_gate_commit,
    validate,
    validate_gate_payload,
)


def test_lot45_entry_gate_passes() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT45_IMPLEMENTATION_ENTRY"
    assert result["post_merge_verdict"] == "GO_LOT44_POST_MERGE"
    assert result["target_lot"] == 45
    assert result["lot46_status"] == "PLANNED_LOCKED"
    assert result["gate_checksum"] == EXPECTED_GATE_CHECKSUM
    assert result["gate_commit"] == locate_gate_commit()


def test_lot45_contract_is_exact_and_fail_closed() -> None:
    gate = load(GATE_PATH)
    assert set(gate["output_contracts"]) == EXPECTED_OUTPUTS
    assert gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert gate["safety"]["analysis_only"] is True
    assert gate["safety"]["trade_allowed"] is False
    assert gate["safety"]["execution_allowed"] is False
    assert gate["safety"]["approved_size"] == 0
    assert gate["safety"]["signal_generation_allowed"] is False
    assert gate["safety"]["risk_approval_allowed"] is False
    assert gate["safety"]["order_routing_allowed"] is False


def test_gate_checksum_rejects_tampering() -> None:
    gate = load(GATE_PATH)
    tampered = copy.deepcopy(gate)
    tampered["next_lot_status"] = "IMPLEMENTED"
    with pytest.raises(Lot45EntryGateError, match="checksum"):
        validate_gate_payload(tampered)


def test_published_schema_rejects_enabled_execution_and_contract_drift() -> None:
    gate = load(GATE_PATH)
    schema = load(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    validator.validate(gate)

    unsafe = copy.deepcopy(gate)
    unsafe["safety"]["execution_allowed"] = True
    with pytest.raises(ValidationError):
        validator.validate(unsafe)

    drifted = copy.deepcopy(gate)
    drifted["output_contracts"][0] = "ArbitraryStateV1"
    with pytest.raises(ValidationError):
        validator.validate(drifted)

    empty_quality = copy.deepcopy(gate)
    empty_quality["quality"] = {}
    with pytest.raises(ValidationError):
        validator.validate(empty_quality)


def test_lot45_and_lot46_were_absent_at_frozen_gate_snapshot() -> None:
    gate_commit = locate_gate_commit()
    gate_tree = set(git("ls-tree", "-r", "--name-only", gate_commit).splitlines())
    for path in LOT45_FORBIDDEN_BEFORE_GATE | LOT46_FORBIDDEN:
        assert path not in gate_tree, path


def test_predecessor_lot44_entry_gate_is_archived() -> None:
    root = GATE_PATH.parents[2]
    workflow = (root / ".github/workflows/lot44-entry-gate.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
