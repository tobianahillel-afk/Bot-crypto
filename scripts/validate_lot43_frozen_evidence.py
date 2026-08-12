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

GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
PRIOR_FINAL_HEAD = "271e789d43700cf66e1f77597120a6042d8c8f18"
SOURCE_HEAD = "6d2106d8a6e320d33dbbefb57320e7da1cd3afbe"
CERTIFICATION_ANCHOR = "19c6dced6b5482df87579f3505eb665336352fc0"
EVIDENCE_HEAD = "5f4a5172b34081fc0b364d300c5bb1bc5d4f0520"
VALIDATION_PROOF = (
    31631419882,
    9155343144,
    "sha256:72785d9e3e3cb727c4808c991cf535d96451795d5036aebe2daaac3dc11cc51f",
)
MUTATION_PROOF = (
    31631419946,
    9155440853,
    "sha256:6c22e1db9b71010784463433150605f8a53d2ba8692756a73248767accb64eb6",
)

STATE = ROOT / "data/audit/book_resilience_and_replenishment_engine_lot43.json"
AUDIT = ROOT / "data/audit/book_resilience_and_replenishment_engine_audit_lot43.json"
RESILIENCE = ROOT / "data/audit/book_resilience_state_lot43.json"
COVERAGE = ROOT / "reports/lot43/coverage_summary.json"
MUTATION = ROOT / "reports/lot43/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "368788196f6e8f0ab2288dd93ee4b1424d8d1b824dd1cc74fae8f88eee29f7aa",
    AUDIT: "6b28835cde86260717b9a4cd66fe415535c578b2246b4bbe5c8fe5ef8ee267dc",
    RESILIENCE: "c03f3ded2661b589feb559efe5146c9555bf5830a29eab99a8c516024cb9b1d1",
    COVERAGE: "69047ac495566c21f9aa353a1ac7ac8d105b46f2c0fc18b97902a73c81edf1a6",
    MUTATION: "c183923865a87626148018042265050ba26e19fa6fa06cf1961bd8a84f26cbf4",
}
EXPECTED_STATE = "3bbfed4861caa42ee6c181d58b802fa4bd843d2465c16adc3916eca5d01870e6"
EXPECTED_AUDIT = "f92e582367f54487f575d695e35d5d88d92a30fa0736246e60b23fe9677f0539"
EXPECTED_RESILIENCE = "598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb"
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
EXPECTED_SAFETY = {
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot43FrozenEvidenceError(message)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_canonical(payload: dict[str, Any], field: str, expected: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(actual == expected, f"{field} changed")
    require(canonical_checksum(body) == expected, f"{field} canonical mismatch")


def _load_frozen() -> tuple[dict[str, Any], ...]:
    for path, expected in EXPECTED_HASHES.items():
        require(path.is_file(), f"missing frozen evidence: {path}")
        require(file_sha256(path) == expected, f"frozen evidence drifted: {path}")
    return tuple(
        load_json_object(path) for path in (STATE, AUDIT, RESILIENCE, COVERAGE, MUTATION)
    )


def _verify_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    resilience: dict[str, Any],
) -> None:
    verify_canonical(state, "output_checksum", EXPECTED_STATE)
    verify_canonical(audit, "audit_checksum", EXPECTED_AUDIT)
    verify_canonical(resilience, "resilience_checksum", EXPECTED_RESILIENCE)
    require(state["book_resilience"] == resilience, "state/resilience payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["resilience_checksum"] == EXPECTED_RESILIENCE, "audit/resilience link changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source changed")
    require(audit["run_context"]["code_commit"] == SOURCE_HEAD, "audit source changed")
    require(state["safety"] == EXPECTED_SAFETY, "state safety boundary changed")
    require(audit["safety"] == EXPECTED_SAFETY, "audit safety boundary changed")
    require(state["lineage"] == audit["lineage"], "state/audit lineage diverged")
    for field, expected in EXPECTED_LINEAGE.items():
        require(state["lineage"][field] == expected, f"lineage changed: {field}")


def _verify_reference(resilience: dict[str, Any]) -> None:
    require(resilience["history_sequence_ids"] == [1001, 1002, 1003], "history changed")
    require(resilience["sequence_id"] == 1003, "sequence changed")
    require(resilience["resilience_horizons_us"] == [10000, 25000], "horizon set changed")
    require(resilience["volatility_measure_bps"] == "0", "volatility changed")
    require(resilience["volatility_regime"] == "QUIET", "regime changed")
    require(resilience["participant_intent_inferred"] is False, "intent inference enabled")
    events = resilience["depletion_events"]
    require(len(events) == 1, "reference event count changed")
    require(events[0]["side"] == "BID", "reference side changed")
    require(events[0]["depleted_price"] == "50024.8", "reference price changed")
    require(events[0]["max_window_status"] == "EXPIRED_NO_REPLENISHMENT", "reference status changed")
    expected_slices = {
        ("BID", 10000): (1, 0, 0, 1, 0, "FRAGILE"),
        ("BID", 25000): (1, 0, 0, 1, 0, "FRAGILE"),
        ("ASK", 10000): (0, 0, 0, 0, 0, "NO_EVENTS"),
        ("ASK", 25000): (0, 0, 0, 0, 0, "NO_EVENTS"),
    }
    actual = {
        (item["side"], item["horizon_us"]): (
            item["depletion_events_total"],
            item["recovered_events_total"],
            item["mid_shift_events_total"],
            item["expired_events_total"],
            item["pending_events_total"],
            item["resilience_status"],
        )
        for item in resilience["resilience_slices"]
    }
    require(actual == expected_slices, "reference slice matrix changed")


def _verify_quality(coverage: dict[str, Any], mutation: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source changed")
    require(coverage["line_coverage_percent"] == 97.73, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 95.48, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake changed")
    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 82.4, "mutation score changed")
    require(mutation["killed_mutants"] == 2308, "killed mutants changed")
    require(mutation["survived_mutants"] == 493, "survived mutants changed")
    require(mutation["total_mutants"] == 2801, "total mutants changed")
    require(mutation["evaluated_mutants"] == 2801, "evaluated mutants changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout present")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutation present")


def _verify_downstream_lock() -> None:
    for relative in LOT44_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"Lot 44 must remain locked: {relative}")


def validate() -> dict[str, object]:
    state, audit, resilience, coverage, mutation = _load_frozen()
    _verify_links(state, audit, resilience)
    _verify_reference(resilience)
    _verify_quality(coverage, mutation)
    _verify_downstream_lock()
    return {
        "schema_version": "lot43-frozen-evidence-validation-v4",
        "status": "PASS",
        "gate_merge": GATE_MERGE,
        "prior_final_head": PRIOR_FINAL_HEAD,
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
        "state_output_checksum": EXPECTED_STATE,
        "audit_checksum": EXPECTED_AUDIT,
        "resilience_checksum": EXPECTED_RESILIENCE,
        "resilience_horizons_us": resilience["resilience_horizons_us"],
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
