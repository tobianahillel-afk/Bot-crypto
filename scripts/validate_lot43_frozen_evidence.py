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

SOURCE_HEAD = "db91a6700fb7b76133ad896714af6ed82da7c5da"
EVIDENCE_HEAD = "849933f49ec0290a4852b6616f5034f807fcc318"
GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
VALIDATION_RUN = 31607906919
VALIDATION_ARTIFACT = 9145948793
VALIDATION_DIGEST = "sha256:938b89da8af0513625cd057f34960141ec0994249895773287245361af0d2d2f"
MUTATION_RUN = 31607906902
MUTATION_ARTIFACT = 9146057739
MUTATION_DIGEST = "sha256:68e76f978a174c938190babc882c194bd0e8d0a2bdf74822b81272b5ee79c399"

STATE_PATH = ROOT / "data/audit/book_resilience_and_replenishment_engine_lot43.json"
AUDIT_PATH = ROOT / "data/audit/book_resilience_and_replenishment_engine_audit_lot43.json"
RESILIENCE_PATH = ROOT / "data/audit/book_resilience_state_lot43.json"
COVERAGE_PATH = ROOT / "reports/lot43/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot43/mutation_summary.json"

EXPECTED_STATE = "11224c071228af9bffbf8a6f53ffc26b4fe836fec380e35b7e489677988f6919"
EXPECTED_AUDIT = "5ff7cbfeec20c6a20ea08dee0b6aeb39de446fe0a51ab987841d9b6b38910ac5"
EXPECTED_RESILIENCE = "297bec6000bc40f2df428c942ee60f7b170cfc01ddba992503da9c259e6e551f"
EXPECTED_GATE = "4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d"
EXPECTED_CONFIG = "a170aab2e8f71dd6f6420a308edd7aa22f6200a25f39ac1eacefb7ac1aa431a1"
EXPECTED_LOT42_STATE = "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0"
EXPECTED_LOT42_AUDIT = "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f"
EXPECTED_LOT42_ZONE_SET = "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_DELTA_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"
EXPECTED_LOT38_SNAPSHOT = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
VALIDATION_STATE = "VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY"
RECOVERY_THRESHOLD = "0.25"

EXPECTED_FILE_SHA256 = {
    STATE_PATH: "04e456beb82248ca99c5fc8ca2e267d821fde71b8abea60938a108785cd310ed",
    AUDIT_PATH: "9665c8b8f7a24f651cf83f9623d879babe14b58cf1561cedca31c495434b2318",
    RESILIENCE_PATH: "c39e0426c6b6635b60e72865ef9596cd4b056ff7e3bad5b7bd5ba646c219ba4b",
    COVERAGE_PATH: "539d3830130cb3b91098941215b48c33c9d410d43bddec29ec5e1b02c9798c18",
    MUTATION_PATH: "a78875b291644d3b307197d340db9d2eacfcce015a83f757f7910681983f8fb9",
}

LOT44_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
    ROOT / "config/microstructure/trades_and_aggressor_classification_schema_v1.json",
    ROOT / "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "scripts/validate_lot44.py",
    ROOT / "tests/test_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_44.md",
)


class Lot43FrozenEvidenceError(RuntimeError):
    """Raised when frozen Lot 43 evidence no longer matches certification."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot43FrozenEvidenceError(message)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(actual == expected, f"{label} certified checksum changed")
    require(canonical_checksum(body) == expected, f"{label} checksum mismatch")


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


def verify_files() -> None:
    for path, expected in EXPECTED_FILE_SHA256.items():
        require(path.is_file(), f"Lot 43 frozen evidence missing: {path}")
        require(file_sha256(path) == expected, f"Lot 43 frozen evidence drifted: {path}")


def verify_lineage(state: dict[str, Any], audit: dict[str, Any]) -> None:
    expected = {
        "entry_gate_checksum": EXPECTED_GATE,
        "config_checksum": EXPECTED_CONFIG,
        "lot42_state_checksum": EXPECTED_LOT42_STATE,
        "lot42_audit_checksum": EXPECTED_LOT42_AUDIT,
        "lot42_zone_set_checksum": EXPECTED_LOT42_ZONE_SET,
        "lot39_book_checksum": EXPECTED_LOT39_BOOK,
        "lot39_delta_fixture_checksum": EXPECTED_DELTA_FIXTURE,
        "lot38_snapshot_checksum": EXPECTED_LOT38_SNAPSHOT,
    }
    for field, value in expected.items():
        require(state["lineage"][field] == value, f"Lot 43 lineage changed: {field}")
        require(audit["lineage"][field] == value, f"Lot 43 audit lineage changed: {field}")
    require(state["lineage"] == audit["lineage"], "Lot 43 state/audit lineage diverged")


def verify_reference_event(resilience: dict[str, Any]) -> None:
    events = resilience["depletion_events"]
    require(len(events) == 1, "reference depletion event count changed")
    event = events[0]
    expected = {
        "side": "BID",
        "depleted_price": "50024.8",
        "previous_quantity": "1.25",
        "post_depletion_quantity": "0",
        "depleted_quantity": "1.25",
        "depletion_sequence_id": 1003,
        "replenishment_kind": "NONE",
        "max_window_status": "EXPIRED_NO_REPLENISHMENT",
        "participant_intent": "NOT_INFERRED",
    }
    for field, value in expected.items():
        require(event[field] == value, f"reference depletion changed: {field}")


def verify_reference_slices(resilience: dict[str, Any]) -> None:
    slices = resilience["resilience_slices"]
    require(len(slices) == 4, "reference slice count changed")
    require(
        all(item["replenishment_min_recovery_ratio"] == RECOVERY_THRESHOLD for item in slices),
        "versioned recovery threshold changed",
    )
    bid = [item for item in slices if item["side"] == "BID"]
    ask = [item for item in slices if item["side"] == "ASK"]
    require([item["horizon_us"] for item in bid] == [10000, 25000], "BID horizons changed")
    require([item["resilience_status"] for item in bid] == ["FRAGILE", "FRAGILE"], "BID resilience changed")
    require([item["horizon_us"] for item in ask] == [10000, 25000], "ASK horizons changed")
    require([item["resilience_status"] for item in ask] == ["NO_EVENTS", "NO_EVENTS"], "ASK resilience changed")


def verify_reference_metrics(state: dict[str, Any]) -> None:
    metrics = state["metrics"]
    expected = {
        "lot_43_observations_total": 3,
        "lot_43_depletion_events_total": 1,
        "lot_43_expired_max_window_events_total": 1,
        "lot_43_same_price_replenishments_total": 0,
        "lot_43_adjacent_price_replenishments_total": 0,
        "lot_43_mid_shift_events_total": 0,
        "lot_43_pending_max_window_events_total": 0,
    }
    for field, value in expected.items():
        require(metrics[field] == value, f"reference metric changed: {field}")


def verify_reference(resilience: dict[str, Any], state: dict[str, Any]) -> None:
    require(resilience["sequence_id"] == 1003, "reference sequence changed")
    require(resilience["history_sequence_ids"] == [1001, 1002, 1003], "reference history changed")
    require(resilience["observed_book_only"] is True, "observed-book-only changed")
    require(resilience["participant_intent_inferred"] is False, "participant intent inference enabled")
    require(resilience["volatility_measure_bps"] == "0", "reference volatility changed")
    require(resilience["volatility_regime"] == "QUIET", "reference volatility regime changed")
    verify_reference_event(resilience)
    verify_reference_slices(resilience)
    verify_reference_metrics(state)


def verify_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    verify_files()
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    resilience = load_json_object(RESILIENCE_PATH)
    verify_checksum(state, "output_checksum", EXPECTED_STATE, "Lot 43 state")
    verify_checksum(audit, "audit_checksum", EXPECTED_AUDIT, "Lot 43 audit")
    verify_checksum(resilience, "resilience_checksum", EXPECTED_RESILIENCE, "BookResilienceStateV1")
    require(state["book_resilience"] == resilience, "state/resilience payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["resilience_checksum"] == EXPECTED_RESILIENCE, "audit/resilience link changed")
    require(state["validation_state"] == VALIDATION_STATE, "validation state changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["run_context"]["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["safety"] == expected_safety(), "state safety boundary changed")
    require(audit["safety"] == expected_safety(), "audit safety boundary changed")
    verify_lineage(state, audit)
    verify_reference(resilience, state)
    return state, audit, resilience


def verify_coverage(coverage: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 98.89, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 98.56, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")


def verify_mutation(mutation: dict[str, Any]) -> None:
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["mutation_score_percent"] == 82.55, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation below threshold")
    require(mutation["killed_mutants"] == 2185, "mutation killed count changed")
    require(mutation["survived_mutants"] == 462, "mutation survivor count changed")
    require(mutation["evaluated_mutants"] == 2647, "mutation evaluated count changed")
    require(mutation["completed_mutants"] == 2647, "mutation completed count changed")
    require(mutation["total_mutants"] == 2647, "mutation total changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "mutation suspicious count changed")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    require(mutation["mutmut_run_exit_code"] == 0, "mutmut run failed")
    require(mutation["mutmut_results_exit_code"] == 0, "mutmut results failed")


def verify_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load_json_object(COVERAGE_PATH)
    mutation = load_json_object(MUTATION_PATH)
    verify_coverage(coverage)
    verify_mutation(mutation)
    return coverage, mutation


def verify_lot44_lock() -> None:
    for path in LOT44_FORBIDDEN:
        require(not path.exists(), f"Lot 44 must remain locked: {path}")


def validate() -> dict[str, object]:
    state, audit, resilience = verify_artifacts()
    coverage, mutation = verify_quality()
    verify_lot44_lock()
    return {
        "schema_version": "lot43-frozen-evidence-validation-v1",
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "gate_merge": GATE_MERGE,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "resilience_checksum": resilience["resilience_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "validation_run": VALIDATION_RUN,
        "validation_artifact": VALIDATION_ARTIFACT,
        "validation_artifact_digest": VALIDATION_DIGEST,
        "mutation_run": MUTATION_RUN,
        "mutation_artifact": MUTATION_ARTIFACT,
        "mutation_artifact_digest": MUTATION_DIGEST,
        "lot44_status": "PLANNED_LOCKED",
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
