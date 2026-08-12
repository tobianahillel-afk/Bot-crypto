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

SOURCE_HEAD = "8d2f99fcd7f654d18079ff8ea24f90e57cfc4086"
EVIDENCE_HEAD = "f05abfbf42577380ef536f0f4bf7865b342d8441"
GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
VALIDATION_RUN = 31587576809
VALIDATION_ARTIFACT = 9137794604
VALIDATION_DIGEST = "sha256:271a229b4da2ce5043f8966ed18a7908eeb477c8df3af9290259fde746796d2a"
MUTATION_RUN = 31587576843
MUTATION_ARTIFACT = 9137870947
MUTATION_DIGEST = "sha256:8cd93c6019961e16c8e8cc862fdf8984cac11d1613a9d4bb156989f828f06dc0"

STATE_PATH = ROOT / "data/audit/book_resilience_and_replenishment_engine_lot43.json"
AUDIT_PATH = ROOT / "data/audit/book_resilience_and_replenishment_engine_audit_lot43.json"
RESILIENCE_PATH = ROOT / "data/audit/book_resilience_state_lot43.json"
COVERAGE_PATH = ROOT / "reports/lot43/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot43/mutation_summary.json"

EXPECTED_STATE = "a32a0ed7cb563548bc29a47499e0663c6c9a24dc2952a4178d0a6a58104692be"
EXPECTED_AUDIT = "4b7aeb4d0613dfc4f03fe162dbd7e547ffbce85893182593ca2cae570810baf0"
EXPECTED_RESILIENCE = "ff314e1eecd40bca822b471f0239fdb8abb294375a8964a738131b71cba4b36e"
EXPECTED_GATE = "4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d"
EXPECTED_CONFIG = "a170aab2e8f71dd6f6420a308edd7aa22f6200a25f39ac1eacefb7ac1aa431a1"
EXPECTED_LOT42_STATE = "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0"
EXPECTED_LOT42_AUDIT = "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f"
EXPECTED_LOT42_ZONE_SET = "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_DELTA_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"
EXPECTED_LOT38_SNAPSHOT = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
VALIDATION_STATE = "VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY"

EXPECTED_FILE_SHA256 = {
    STATE_PATH: "40c5a708cc650b2bd7b46714a59064c8332013b3b5eac50a3bc7ebb9ebb35e7e",
    AUDIT_PATH: "e32c390059d7d18a880c271a8949f46ad5a4b13d486028fc708e2dfbbb07eecb",
    RESILIENCE_PATH: "b0dc74447c54ee84bb3da36a78cf3f48edb4ed54352c6837bed3823a2c898240",
    COVERAGE_PATH: "0123ace5799648026eac0f25690d60a1d90972b750544d2a0ff51b1f16685f12",
    MUTATION_PATH: "b13abd10a66a06c401af7af0133024cd34e37217c78af92b9ab86cbafd46fd34",
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


def verify_files() -> None:
    for path, expected in EXPECTED_FILE_SHA256.items():
        require(path.is_file(), f"Lot 43 frozen evidence missing: {path}")
        require(file_sha256(path) == expected, f"Lot 43 frozen evidence drifted: {path}")


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


def verify_reference_header(resilience: dict[str, Any]) -> None:
    require(resilience["sequence_id"] == 1003, "reference sequence changed")
    require(resilience["history_sequence_ids"] == [1001, 1002, 1003], "reference history changed")
    require(resilience["observed_book_only"] is True, "observed-book-only changed")
    require(resilience["participant_intent_inferred"] is False, "participant intent inference enabled")
    require(resilience["volatility_measure_bps"] == "0", "reference volatility changed")
    require(resilience["volatility_regime"] == "QUIET", "reference volatility regime changed")


def verify_reference_event(resilience: dict[str, Any]) -> None:
    events = resilience["depletion_events"]
    require(len(events) == 1, "reference depletion event count changed")
    event = events[0]
    require(event["side"] == "BID" and event["depleted_price"] == "50024.8", "reference depletion changed")
    require(event["previous_quantity"] == "1.25", "reference previous quantity changed")
    require(event["post_depletion_quantity"] == "0", "reference post quantity changed")
    require(event["replenishment_kind"] == "NONE", "reference replenishment changed")
    require(event["max_window_status"] == "EXPIRED_NO_REPLENISHMENT", "reference window status changed")
    require(event["participant_intent"] == "NOT_INFERRED", "reference participant intent changed")


def verify_reference_slices(resilience: dict[str, Any]) -> None:
    bid = [item for item in resilience["resilience_slices"] if item["side"] == "BID"]
    ask = [item for item in resilience["resilience_slices"] if item["side"] == "ASK"]
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
    }
    for field, value in expected.items():
        require(metrics[field] == value, f"reference metric changed: {field}")


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
    verify_reference_header(resilience)
    verify_reference_event(resilience)
    verify_reference_slices(resilience)
    verify_reference_metrics(state)
    return state, audit, resilience


def verify_coverage(coverage: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 98.86, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 98.46, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")


def verify_mutation(mutation: dict[str, Any]) -> None:
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["mutation_score_percent"] == 82.28, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation below threshold")
    require(mutation["killed_mutants"] == 2140, "mutation killed count changed")
    require(mutation["survived_mutants"] == 461, "mutation survivor count changed")
    require(mutation["evaluated_mutants"] == 2601, "mutation evaluated count changed")
    require(mutation["completed_mutants"] == 2601, "mutation completed count changed")
    require(mutation["total_mutants"] == 2601, "mutation total changed")
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
    result: dict[str, object] = {
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
        "next_lot": 44,
        "next_lot_status": "PLANNED_LOCKED",
        "participant_intent_inferred": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot43FrozenEvidenceError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT43 FROZEN EVIDENCE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
