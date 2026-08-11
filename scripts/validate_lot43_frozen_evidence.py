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

SOURCE_HEAD = "c0dae9a04f0c8464003b039aba4660c223afe2a8"
EVIDENCE_HEAD = "711b80410210b50f000bd243212276d399fdb7e4"
GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
VALIDATION_RUN = 31532094394
VALIDATION_ARTIFACT = 9117300635
VALIDATION_DIGEST = "sha256:6cc3b15e8be3813dbb3311eac9ea7f592aa71d387f300f38984638962f0976ce"
MUTATION_RUN = 31532094445
MUTATION_ARTIFACT = 9117371001
MUTATION_DIGEST = "sha256:68ae4dfb90e8214cb4d192d990d35ff62b94d3f1ff4929daef14555f51aba29d"

STATE_PATH = ROOT / "data/audit/book_resilience_and_replenishment_engine_lot43.json"
AUDIT_PATH = ROOT / "data/audit/book_resilience_and_replenishment_engine_audit_lot43.json"
RESILIENCE_PATH = ROOT / "data/audit/book_resilience_state_lot43.json"
COVERAGE_PATH = ROOT / "reports/lot43/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot43/mutation_summary.json"

EXPECTED_STATE = "347c394e71886e6deca4a9e809eb13860a5c63c7c4fe15eed1ea7a95f942f096"
EXPECTED_AUDIT = "18b4f70a4284f0250f8a580285d5cda06bf758163fa92776d8de3b7a285544ea"
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
    STATE_PATH: "d866e608f3afde084114fd4ebd6bc118be5a906335e1e86bf2500b9fd2f4f3f3",
    AUDIT_PATH: "3c77e11e709699d59708096d8796373df81a8bb3d582bbafb9e1969856acf833",
    RESILIENCE_PATH: "b0dc74447c54ee84bb3da36a78cf3f48edb4ed54352c6837bed3823a2c898240",
    COVERAGE_PATH: "a80a159752ea86929c7d26b851509a1a81fab7401538b9d1ad12f865d06509d0",
    MUTATION_PATH: "1eead48d3ab086ef2a3e2d7fdbc460842a455c65961dbd5ccedb0a8d6bc8cfd7",
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
    """Raised when Lot 43 frozen evidence no longer matches certification."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot43FrozenEvidenceError(message)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_files() -> None:
    for path, expected in EXPECTED_FILE_SHA256.items():
        require(path.is_file(), f"Lot 43 frozen evidence missing: {path}")
        require(_file_sha256(path) == expected, f"Lot 43 frozen evidence file drifted: {path}")


def _verify_checksum(payload: dict[str, Any], field: str, expected: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(actual == expected, f"{label} certified checksum changed")
    require(canonical_checksum(body) == expected, f"{label} checksum mismatch")


def _expected_safety() -> dict[str, object]:
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


def _validate_lineage(state: dict[str, Any], audit: dict[str, Any]) -> None:
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


def _validate_reference(resilience: dict[str, Any], state: dict[str, Any]) -> None:
    require(resilience["sequence_id"] == 1003, "reference sequence changed")
    require(resilience["history_sequence_ids"] == [1001, 1002, 1003], "reference history changed")
    require(resilience["observed_book_only"] is True, "observed-book-only changed")
    require(resilience["participant_intent_inferred"] is False, "participant intent inference enabled")
    require(resilience["volatility_measure_bps"] == "0", "reference volatility changed")
    require(resilience["volatility_regime"] == "QUIET", "reference volatility regime changed")
    events = resilience["depletion_events"]
    require(len(events) == 1, "reference depletion event count changed")
    event = events[0]
    require(event["side"] == "BID", "reference depletion side changed")
    require(event["depleted_price"] == "50024.8", "reference depletion price changed")
    require(event["previous_quantity"] == "1.25", "reference previous quantity changed")
    require(event["post_depletion_quantity"] == "0", "reference post quantity changed")
    require(event["replenishment_kind"] == "NONE", "reference replenishment kind changed")
    require(event["max_window_status"] == "EXPIRED_NO_REPLENISHMENT", "reference window status changed")
    require(event["participant_intent"] == "NOT_INFERRED", "reference participant intent changed")
    slices = resilience["resilience_slices"]
    bid = [item for item in slices if item["side"] == "BID"]
    ask = [item for item in slices if item["side"] == "ASK"]
    require([item["horizon_us"] for item in bid] == [10000, 25000], "BID horizons changed")
    require([item["resilience_status"] for item in bid] == ["FRAGILE", "FRAGILE"], "BID resilience changed")
    require([item["horizon_us"] for item in ask] == [10000, 25000], "ASK horizons changed")
    require([item["resilience_status"] for item in ask] == ["NO_EVENTS", "NO_EVENTS"], "ASK resilience changed")
    metrics = state["metrics"]
    require(metrics["lot_43_observations_total"] == 3, "observation count changed")
    require(metrics["lot_43_depletion_events_total"] == 1, "depletion metric changed")
    require(metrics["lot_43_expired_max_window_events_total"] == 1, "expiry metric changed")
    require(metrics["lot_43_same_price_replenishments_total"] == 0, "same-price metric changed")
    require(metrics["lot_43_adjacent_price_replenishments_total"] == 0, "adjacent metric changed")
    require(metrics["lot_43_mid_shift_events_total"] == 0, "mid-shift metric changed")


def _validate_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _verify_files()
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    resilience = load_json_object(RESILIENCE_PATH)
    _verify_checksum(state, "output_checksum", EXPECTED_STATE, "Lot 43 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_AUDIT, "Lot 43 audit")
    _verify_checksum(resilience, "resilience_checksum", EXPECTED_RESILIENCE, "BookResilienceStateV1")
    require(state["book_resilience"] == resilience, "state/resilience payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["resilience_checksum"] == EXPECTED_RESILIENCE, "audit/resilience link changed")
    require(state["validation_state"] == VALIDATION_STATE, "validation state changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["run_context"]["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["safety"] == _expected_safety(), "state safety boundary changed")
    require(audit["safety"] == _expected_safety(), "audit safety boundary changed")
    _validate_lineage(state, audit)
    _validate_reference(resilience, state)
    return state, audit, resilience


def _validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load_json_object(COVERAGE_PATH)
    mutation = load_json_object(MUTATION_PATH)
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 98.82, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 98.41, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["mutation_score_percent"] == 81.6, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation below threshold")
    require(mutation["killed_mutants"] == 2066, "mutation killed count changed")
    require(mutation["survived_mutants"] == 466, "mutation survivor count changed")
    require(mutation["evaluated_mutants"] == 2532, "mutation evaluated count changed")
    require(mutation["completed_mutants"] == 2532, "mutation completed count changed")
    require(mutation["total_mutants"] == 2532, "mutation total changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "mutation suspicious count changed")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    require(mutation["mutmut_run_exit_code"] == 0, "mutmut run failed")
    require(mutation["mutmut_results_exit_code"] == 0, "mutmut results failed")
    return coverage, mutation


def _validate_lot44_lock() -> None:
    for path in LOT44_FORBIDDEN:
        require(not path.exists(), f"Lot 44 must remain locked: {path}")


def validate() -> dict[str, object]:
    state, audit, resilience = _validate_artifacts()
    coverage, mutation = _validate_quality()
    _validate_lot44_lock()
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
