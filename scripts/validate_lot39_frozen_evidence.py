#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "203a2b2d3d69644bd67c0e583df9d0405941def6"
EVIDENCE_HEAD = "b1bf9605fe20cacca76861e3fc6941ad38ea8f23"
STATE_PATH = ROOT / "data/audit/order_book_delta_and_sequence_reconstructor_lot39.json"
AUDIT_PATH = ROOT / "data/audit/order_book_delta_and_sequence_reconstructor_audit_lot39.json"
BOOK_PATH = ROOT / "data/audit/reconstructed_order_book_lot39.json"
COVERAGE_PATH = ROOT / "reports/lot39/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot39/mutation_summary.json"
EXPECTED_STATE = "d21d1c2e2e3ea2a05a4ab156fb4377e865da90808ecdcfbc8161abf99bc796f0"
EXPECTED_AUDIT = "1e29d0b8695a1b8825e1fc91728a6254ad93c689e1f961cfa424e6d5fed8ed41"
EXPECTED_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"


class Lot39FrozenEvidenceError(RuntimeError):
    """Raised when frozen Lot 39 evidence no longer matches certification."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot39FrozenEvidenceError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def checksum(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(actual == expected, f"{label} certified checksum changed")
    require(checksum(body) == expected, f"{label} checksum mismatch")


def expected_safety() -> dict[str, object]:
    return {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "participant_behavior_inference_explicitly_labeled": True,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "scenario_score_is_signal": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }


def validate_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = load(STATE_PATH)
    audit = load(AUDIT_PATH)
    book = load(BOOK_PATH)
    verify(state, "output_checksum", EXPECTED_STATE, "Lot 39 state")
    verify(audit, "audit_checksum", EXPECTED_AUDIT, "Lot 39 audit")
    verify(book, "book_checksum", EXPECTED_BOOK, "Lot 39 reconstructed book")
    require(state["reconstructed_book"] == book, "state/book payload mismatch")
    require(state["sequence_gap_event"] is None, "healthy state cannot persist gap evidence")
    require(state["synchronization_state"] == "SYNCED", "Lot 39 state not SYNCED")
    require(audit["synchronization_state"] == "SYNCED", "Lot 39 audit not SYNCED")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "state/audit link changed")
    require(audit["reconstructed_book_checksum"] == EXPECTED_BOOK, "book/audit link changed")
    require(audit["sequence_gap_event_checksum"] is None, "audit unexpectedly links gap")
    require(state["delta_fixture_checksum"] == EXPECTED_FIXTURE, "fixture checksum changed")
    require(audit["delta_fixture_checksum"] == EXPECTED_FIXTURE, "audit fixture link changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["safety"] == expected_safety(), "state safety boundary changed")
    require(audit["safety"] == expected_safety(), "audit safety boundary changed")
    require("LOT40_REMAINS_LOCKED" in state["reason_codes"], "Lot 40 lock reason missing")
    return state, audit, book


def validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load(COVERAGE_PATH)
    mutation = load(MUTATION_PATH)
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 99.24, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 96.97, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["total_mutants"] == 2018, "mutation total changed")
    require(mutation["evaluated_mutants"] == 2018, "mutation evaluated count changed")
    require(mutation["killed_mutants"] == 1651, "mutation killed count changed")
    require(mutation["survived_mutants"] == 367, "mutation survivor count changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "mutation suspicious count changed")
    require(mutation["mutation_score_percent"] == 81.81, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation score below threshold")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    return coverage, mutation


def validate() -> dict[str, object]:
    state, audit, book = validate_artifacts()
    coverage, mutation = validate_quality()
    result: dict[str, object] = {
        "schema_version": "lot39-frozen-evidence-validation-v1",
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "reconstructed_book_checksum": book["book_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "lot40_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot39FrozenEvidenceError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT39 FROZEN EVIDENCE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
