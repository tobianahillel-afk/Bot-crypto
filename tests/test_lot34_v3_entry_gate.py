from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_lot34_entry_gate import (
    EXPECTED_CHECKSUM,
    Lot34EntryGateError,
    canonical_checksum,
    validate,
    validate_gate_checksum,
    validate_quality_and_safety,
    validate_scope,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot34_v3_entry_gate.json"


def load_gate() -> dict[str, object]:
    value = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot34_entry_gate_validator_passes() -> None:
    assert validate() == {
        "schema_version": "lot34-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT34_IMPLEMENTATION_ENTRY",
        "output_checksum": EXPECTED_CHECKSUM,
        "next_locked_lot": 35,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def test_lot34_gate_checksum_recomputes() -> None:
    gate = load_gate()
    checksum = gate.pop("output_checksum")
    assert checksum == EXPECTED_CHECKSUM
    assert canonical_checksum(gate) == checksum


def test_lot34_gate_authorizes_all_eight_anomaly_families() -> None:
    allowed = set(load_gate()["allowed_scope"])
    assert {
        "MISSING_INTERVAL_DETECTION",
        "DUPLICATE_DETECTION",
        "OUT_OF_ORDER_DETECTION",
        "STALE_DATA_DETECTION",
        "INVALID_OHLC_DETECTION",
        "NEGATIVE_VOLUME_DETECTION",
        "IMPOSSIBLE_SPREAD_DETECTION",
        "SCHEMA_DRIFT_DETECTION",
    } <= allowed


def test_lot34_gate_keeps_raw_data_and_future_capabilities_locked() -> None:
    gate = load_gate()
    safety = gate["safety"]
    assert isinstance(safety, dict)
    assert safety["raw_data_mutation_allowed"] is False
    assert safety["market_event_publication_allowed"] is False
    assert safety["external_connectivity_allowed"] is False
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0
    assert gate["next_lot"] == 35
    assert gate["next_lot_status"] == "PLANNED_LOCKED"


def test_lot34_gate_rejects_checksum_tamper() -> None:
    gate = load_gate()
    gate["owner"] = "WrongOwner"
    with pytest.raises(Lot34EntryGateError, match="checksum"):
        validate_gate_checksum(gate)


def test_lot34_gate_rejects_scope_expansion_even_with_recomputed_checksum() -> None:
    gate = load_gate()
    gate["allowed_scope"] = [*gate["allowed_scope"], "FORECAST_GENERATION"]
    gate.pop("output_checksum")
    gate["output_checksum"] = canonical_checksum(gate)
    with pytest.raises(Lot34EntryGateError, match="allowed scope"):
        validate_scope(gate)


def test_lot34_gate_rejects_raw_mutation_permission() -> None:
    gate = load_gate()
    safety = dict(gate["safety"])
    safety["raw_data_mutation_allowed"] = True
    gate["safety"] = safety
    with pytest.raises(Lot34EntryGateError, match="safety"):
        validate_quality_and_safety(gate)


def test_lot34_gate_rejects_lower_quality_thresholds() -> None:
    gate = load_gate()
    quality = dict(gate["quality_gates"])
    quality["mutation_score_min_percent"] = 0
    gate["quality_gates"] = quality
    with pytest.raises(Lot34EntryGateError, match="quality"):
        validate_quality_and_safety(gate)
