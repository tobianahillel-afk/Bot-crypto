#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    load_json_object,
)

SOURCE_HEAD = "dccea5dcd03414064ead4e6979d53df98dfdda6f"
CERTIFICATION_ANCHOR = "f9ea774f9f59b4fc7af55dcb911e085797c42a34"
EVIDENCE_HEAD = "c58321c9817117623adcff9949348b4b4624d483"
GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
VALIDATION_PROOF = (
    31620295621,
    9150976691,
    "sha256:a4bbf31d1b83f94bbfec52e8dbb0a926d2a87fdf215c9ef17f3353875f18d41c",
)
MUTATION_PROOF = (
    31620295636,
    9151065443,
    "sha256:95274da9fc4dd916a78a5c2cf14ef1103c627a406acdb6ba005c479a2eea545a",
)

STATE = ROOT / "data/audit/book_resilience_and_replenishment_engine_lot43.json"
AUDIT = ROOT / "data/audit/book_resilience_and_replenishment_engine_audit_lot43.json"
RESILIENCE = ROOT / "data/audit/book_resilience_state_lot43.json"
COVERAGE = ROOT / "reports/lot43/coverage_summary.json"
MUTATION = ROOT / "reports/lot43/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "310ceae2eaa25028603edb83406213f0aecb3bd04d2ec28439c03f2d0219a12e",
    AUDIT: "018359f62ebd864e100a21f8df60d2a21380f9c5988c9d00414f373c323dff31",
    RESILIENCE: "c39e0426c6b6635b60e72865ef9596cd4b056ff7e3bad5b7bd5ba646c219ba4b",
    COVERAGE: "76e8f914defd25f86e41c1aa515c71258a1cfb361901051522b36ce72f08e6bb",
    MUTATION: "b40709a4ea0ffd68d305812fd09e614f63c0444f6c6a601513d884d65b1b8e93",
}
EXPECTED_STATE = "797bd974b37b4806bfada6b6b938d189401dc915998aa97e68473b1226da4a3d"
EXPECTED_AUDIT = "553b0747c66275cefb4636b3d84ea664230ae765476126711bf15b768ac92ec4"
EXPECTED_RESILIENCE = "297bec6000bc40f2df428c942ee60f7b170cfc01ddba992503da9c259e6e551f"
EXPECTED_LINEAGE = {
    "entry_gate_checksum": "4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d",
    "config_checksum": "a170aab2e8f71dd6f6420a308edd7aa22f6200a25f39ac1eacefb7ac1aa431a1",
    "lot42_state_checksum": "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0",
    "lot42_audit_checksum": "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f",
    "lot42_zone_set_checksum": "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89",
    "lot39_book_checksum": "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde",
    "lot39_delta_fixture_checksum": "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97",
    "lot38_snapshot_checksum": "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16",
}
LOT44_FORBIDDEN = (
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
    "config/microstructure/trades_and_aggressor_classification_schema_v1.json",
    "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    "scripts/validate_lot44.py",
    "tests/test_lot44_trades_and_aggressor_classification_schema.py",
    "docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_44.md",
)


class Lot43FrozenEvidenceError(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise Lot43FrozenEvidenceError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_checksum(payload: dict[str, Any], field: str, expected: str) -> None:
    body = dict(payload)
    require(body.pop(field, None) == expected, f"{field} changed")
    require(canonical_checksum(body) == expected, f"{field} canonical mismatch")


def verify_files() -> None:
    for path, expected in EXPECTED_HASHES.items():
        require(path.is_file(), f"missing frozen evidence: {path}")
        require(sha256(path) == expected, f"frozen evidence drifted: {path}")


def verify_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = load_json_object(STATE)
    audit = load_json_object(AUDIT)
    resilience = load_json_object(RESILIENCE)
    verify_checksum(state, "output_checksum", EXPECTED_STATE)
    verify_checksum(audit, "audit_checksum", EXPECTED_AUDIT)
    verify_checksum(resilience, "resilience_checksum", EXPECTED_RESILIENCE)
    require(state["book_resilience"] == resilience, "state/resilience payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["resilience_checksum"] == EXPECTED_RESILIENCE, "audit/resilience link changed")
    for payload in (state, audit):
        require(payload["run_context"]["code_commit"] == SOURCE_HEAD, "source head changed")
        for field, expected in EXPECTED_LINEAGE.items():
            require(payload["lineage"][field] == expected, f"lineage changed: {field}")
        safety = payload["safety"]
        require(safety["analysis_only"] is True, "analysis-only changed")
        require(safety["trade_allowed"] is False, "trade permission changed")
        require(safety["execution_allowed"] is False, "execution permission changed")
        require(safety["approved_size"] == 0, "approved size changed")
    require(state["lineage"] == audit["lineage"], "state/audit lineage diverged")
    require(resilience["history_sequence_ids"] == [1001, 1002, 1003], "history changed")
    require(resilience["sequence_id"] == 1003, "reference sequence changed")
    require(resilience["volatility_measure_bps"] == "0", "reference volatility changed")
    require(resilience["volatility_regime"] == "QUIET", "reference regime changed")
    events = resilience["depletion_events"]
    require(len(events) == 1, "reference event count changed")
    require(events[0]["side"] == "BID", "reference side changed")
    require(events[0]["depleted_price"] == "50024.8", "reference price changed")
    require(events[0]["max_window_status"] == "EXPIRED_NO_REPLENISHMENT", "status changed")
    statuses = {(item["side"], item["horizon_us"]): item["resilience_status"] for item in resilience["resilience_slices"]}
    require(statuses == {
        ("BID", 10000): "FRAGILE",
        ("BID", 25000): "FRAGILE",
        ("ASK", 10000): "NO_EVENTS",
        ("ASK", 25000): "NO_EVENTS",
    }, "reference slice statuses changed")
    return state, audit, resilience


def verify_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load_json_object(COVERAGE)
    mutation = load_json_object(MUTATION)
    require(coverage["status"] == "PASS", "coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source changed")
    require(coverage["line_coverage_percent"] == 98.91, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 98.59, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake changed")
    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 82.42, "mutation score changed")
    require(mutation["killed_mutants"] == 2217, "killed mutants changed")
    require(mutation["survived_mutants"] == 473, "survived mutants changed")
    require(mutation["total_mutants"] == 2690, "total mutants changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout present")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutation present")
    return coverage, mutation


def validate() -> dict[str, object]:
    verify_files()
    state, audit, resilience = verify_artifacts()
    coverage, mutation = verify_quality()
    for relative in LOT44_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"Lot 44 must remain locked: {relative}")
    return {
        "schema_version": "lot43-frozen-evidence-validation-v1",
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
        "gate_merge": GATE_MERGE,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "resilience_checksum": resilience["resilience_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "validation_run": VALIDATION_PROOF[0],
        "validation_artifact": VALIDATION_PROOF[1],
        "validation_artifact_digest": VALIDATION_PROOF[2],
        "mutation_run": MUTATION_PROOF[0],
        "mutation_artifact": MUTATION_PROOF[1],
        "mutation_artifact_digest": MUTATION_PROOF[2],
        "lot44_status": "PLANNED_LOCKED",
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
