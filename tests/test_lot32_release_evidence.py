from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json"
AUDIT_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"
SOURCE_REGISTRY_PATH = ROOT / "data/audit/source_registry_lot31.json"
LOT31_STATE_PATH = ROOT / "data/audit/market_data_governance_scope_and_source_registry_lot31.json"
LOT31_AUDIT_PATH = (
    ROOT / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
)
COVERAGE_PATH = ROOT / "reports/lot32/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot32/mutation_summary.json"
IMPLEMENTATION_COMMIT = "cd9ffa91a4a64c36a71a40e746cf575fe438d59b"


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field)
    assert isinstance(checksum, str)
    assert canonical_checksum(content) == checksum
    return checksum


def test_lot32_release_artifacts_are_linked_and_fail_closed() -> None:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    registry = load(REGISTRY_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    payload_checksum(audit, "audit_checksum")
    assert state["instrument_registry"] == registry
    assert audit["state_output_checksum"] == state_checksum
    assert state["lineage"] == {
        "available_at": "2026-08-06T19:15:00Z",
        "lineage_id": "lot32-from-certified-lot31-source-registry",
        "lot31_audit_checksum": file_checksum(LOT31_AUDIT_PATH),
        "lot31_state_checksum": file_checksum(LOT31_STATE_PATH),
        "schema_version": "lot32-lineage-envelope-v1",
        "source_registry_checksum": file_checksum(SOURCE_REGISTRY_PATH),
        "source_registry_path": "data/audit/source_registry_lot31.json",
    }
    assert audit["source_registry_checksum"] == file_checksum(SOURCE_REGISTRY_PATH)
    assert state["validation_state"] == "VALIDATED_NORMALIZATION_ONLY"
    assert audit["validation_state"] == "VALIDATED_NORMALIZATION_ONLY"
    assert audit["instrument_count"] == 1
    assert audit["venue_alias_count"] == 3
    assert audit["round_trip_count"] == 6
    assert audit["frozen_instrument_count"] == 0
    expected_safety = {
        "analysis_only": True,
        "used_for_decision": False,
        "external_connectivity_allowed": False,
        "network_ingestion_allowed": False,
        "real_credentials_allowed": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected_safety.items():
        assert state[field] == value
        assert audit[field] == value
    code_commit = state["run_context"]["code_commit"]
    assert isinstance(code_commit, str)
    assert len(code_commit) == 40
    assert set(code_commit) <= set("0123456789abcdef")
    assert audit["code_commit"] == code_commit


def test_lot32_registry_preserves_exact_round_trips() -> None:
    registry = load(REGISTRY_PATH)
    instruments = registry["instruments"]
    assert len(instruments) == 1
    instrument = instruments[0]
    assert instrument["canonical_symbol"] == "BTC/EUR:SPOT"
    assert instrument["market_type"] == "SPOT"
    assert all(
        instrument[field] is None
        for field in ("contract_size", "expiry_time", "strike_price", "option_type")
    )
    expected = {
        "BITSTAMP": "btceur",
        "COINBASE": "BTC-EUR",
        "KRAKEN": "XBTEUR",
    }
    aliases = instrument["aliases"]
    assert {item["venue"]: item["exchange_symbol"] for item in aliases} == expected
    assert all(item["validation_state"] == "VALIDATED_METADATA_ONLY" for item in aliases)
    assert all(item["margin_mode"] is None for item in aliases)
    assert all(item["leverage_policy"] == "FORBIDDEN" for item in aliases)


def test_lot32_certified_quality_thresholds_remain_satisfied() -> None:
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    assert coverage["evidence_commit"] == IMPLEMENTATION_COMMIT
    assert coverage["status"] == "PASS"
    assert coverage["test_count"] == 57
    assert coverage["line_coverage_percent"] >= coverage["line_minimum_percent"] >= 95.0
    assert coverage["branch_coverage_percent"] >= coverage["branch_minimum_percent"] >= 90.0
    assert mutation["evidence_commit"] == IMPLEMENTATION_COMMIT
    assert mutation["status"] == "PASS"
    assert mutation["evaluated_mutants"] == (
        mutation["killed_mutants"]
        + mutation["survived_mutants"]
        + mutation["timeout_mutants"]
    )
    assert mutation["mutation_score_percent"] >= mutation["minimum_score_percent"] >= 80.0
