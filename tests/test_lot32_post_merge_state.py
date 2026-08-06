from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MERGED_COMMIT = "7187f2ebfebeb67292c8a521e7e8bdbc653c3086"
IMPLEMENTATION_COMMIT = "cd9ffa91a4a64c36a71a40e746cf575fe438d59b"
STATE_CHECKSUM = "da269de9a3a94f83b3dd437362ae565bd38a098cbe0dc81190887347c7fce240"
AUDIT_CHECKSUM = "b69aa85d72851470f9f807d05ae27127651e6ac8d12623aed8d3f5d96f94659a"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_checksum(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def load_json(relative: str) -> dict[str, Any]:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_lot32_post_merge_release_and_lifecycle_are_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = load_json("data/audit/roadmap_lifecycle_overlay_lot32.json")
    assert project["version"] == "0.32.0"
    assert overlay["latest_implemented_lot"] == 32
    assert overlay["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot31.json"
    lots = overlay["lots"]
    lot32 = lots["32"]
    assert lot32["status"] == "IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY"
    assert lot32["implementation_commit"] == IMPLEMENTATION_COMMIT
    assert lot32["merged_commit"] == MERGED_COMMIT
    assert lot32["pull_request"] == 21
    assert lot32["runtime_mode"] == "DATA_GOVERNANCE_ONLY"
    assert lot32["external_connectivity_allowed"] is False
    assert lot32["network_ingestion_allowed"] is False
    assert lot32["trade_allowed"] is False
    assert lot32["execution_allowed"] is False
    assert lots["33"] == {"implementation_started": False, "status": "PLANNED_LOCKED"}


def test_lot32_post_merge_artifacts_are_independently_linked() -> None:
    state = load_json("data/audit/instrument_symbol_and_contract_normalization_lot32.json")
    audit = load_json("data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json")
    registry = load_json("data/audit/instrument_registry_lot32.json")
    state_payload = dict(state)
    state_checksum = state_payload.pop("output_checksum")
    audit_payload = dict(audit)
    audit_checksum = audit_payload.pop("audit_checksum")
    assert canonical_checksum(state_payload) == state_checksum == STATE_CHECKSUM
    assert canonical_checksum(audit_payload) == audit_checksum == AUDIT_CHECKSUM
    assert state["instrument_registry"] == registry
    assert audit["state_output_checksum"] == state_checksum
    assert audit["code_commit"] == state["run_context"]["code_commit"]
    assert COMMIT_PATTERN.fullmatch(audit["code_commit"])
    lineage = state["lineage"]
    assert lineage["source_registry_checksum"] == file_checksum(
        "data/audit/source_registry_lot31.json"
    )
    assert lineage["lot31_state_checksum"] == file_checksum(
        "data/audit/market_data_governance_scope_and_source_registry_lot31.json"
    )
    assert lineage["lot31_audit_checksum"] == file_checksum(
        "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )


def test_lot32_post_merge_registry_and_quality_remain_certified() -> None:
    state = load_json("data/audit/instrument_symbol_and_contract_normalization_lot32.json")
    audit = load_json("data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json")
    coverage = load_json("reports/lot32/coverage_summary.json")
    mutation = load_json("reports/lot32/mutation_summary.json")
    instrument = state["instrument_registry"]["instruments"][0]
    assert instrument["canonical_symbol"] == "BTC/EUR:SPOT"
    assert instrument["market_type"] == "SPOT"
    assert all(
        instrument[field] is None
        for field in ("contract_size", "expiry_time", "strike_price", "option_type")
    )
    assert {alias["venue"]: alias["exchange_symbol"] for alias in instrument["aliases"]} == {
        "BITSTAMP": "btceur",
        "COINBASE": "BTC-EUR",
        "KRAKEN": "XBTEUR",
    }
    assert audit["instrument_count"] == 1
    assert audit["venue_alias_count"] == 3
    assert audit["round_trip_count"] == 6
    assert audit["frozen_instrument_count"] == 0
    assert coverage["status"] == "PASS"
    assert coverage["test_count"] == 57
    assert coverage["line_coverage_percent"] >= 95.0
    assert coverage["branch_coverage_percent"] >= 90.0
    assert mutation["status"] == "PASS"
    assert mutation["mutation_score_percent"] >= 80.0
    assert mutation["killed_mutants"] == 175
    assert mutation["evaluated_mutants"] == 208


def test_lot32_post_merge_safety_and_docs_remain_fail_closed() -> None:
    state = load_json("data/audit/instrument_symbol_and_contract_normalization_lot32.json")
    audit = load_json("data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json")
    expected = {
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
    for field, value in expected.items():
        assert state[field] == value
        assert audit[field] == value
    document = (ROOT / "docs/LOT_32_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "GO_LOT32_POST_MERGE_AUDIT" in document
    assert "Lot 32 : `IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY`" in roadmap
    assert "Lot 33" in roadmap and "PLANNED_LOCKED" in roadmap
    assert "Lot 32 — Instrument, Symbol & Contract Normalization" in readme
