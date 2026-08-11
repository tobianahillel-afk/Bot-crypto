#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "14c0d8da1b02d076b3c43a07a34ac96c673018b0"
EVIDENCE_HEAD = "7ada0ca6c4d439505ef453b988dedd4aa96c1a32"
GATE_MERGE = "75822f8ea7c6f67f73649d2f43be6efba840ab67"
VALIDATION_RUN = 31483147929
VALIDATION_ARTIFACT = 9098042735
VALIDATION_DIGEST = "sha256:c72bf3a6eda3e006132b924bbe6bdee896bfd89522aff2efcbf64aee1a073daa"
MUTATION_RUN = 31483147942
MUTATION_ARTIFACT = 9098069057
MUTATION_DIGEST = "sha256:0790745bf018c8ccfa6d5f6c88445d11d8a416d95025d0193b793208146f8037"

STATE_PATH = ROOT / "data/audit/spread_depth_and_imbalance_engine_lot41.json"
AUDIT_PATH = ROOT / "data/audit/spread_depth_and_imbalance_engine_audit_lot41.json"
FEATURE_PATH = ROOT / "data/audit/book_feature_state_lot41.json"
COVERAGE_PATH = ROOT / "reports/lot41/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot41/mutation_summary.json"

EXPECTED_STATE = "23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573"
EXPECTED_AUDIT = "af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd"
EXPECTED_FEATURE = "77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5"
EXPECTED_GATE = "1d3fab39fde8c92ed7c94af1b722b5f877d56663f28f856b603de7f3e31a8efe"
EXPECTED_LOT40_STATE = "e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477"
EXPECTED_LOT40_AUDIT = "978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c"
EXPECTED_INTEGRITY = "35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a"
EXPECTED_VETO = "000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc"
EXPECTED_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
VALIDATION_STATE = "VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY"

LOT42_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py",
    ROOT / "scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py",
    ROOT / "scripts/validate_lot42.py",
)


class Lot41FrozenEvidenceError(RuntimeError):
    """Raised when Lot 41 frozen evidence no longer matches certification."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot41FrozenEvidenceError(message)


def _verify_checksum(
    payload: dict[str, Any],
    field: str,
    expected: str,
    label: str,
) -> None:
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
    lineage = state["lineage"]
    expected = {
        "entry_gate_checksum": EXPECTED_GATE,
        "lot40_state_checksum": EXPECTED_LOT40_STATE,
        "lot40_audit_checksum": EXPECTED_LOT40_AUDIT,
        "lot40_integrity_checksum": EXPECTED_INTEGRITY,
        "lot40_veto_checksum": EXPECTED_VETO,
        "reconstructed_book_checksum": EXPECTED_BOOK,
    }
    for field, value in expected.items():
        require(lineage[field] == value, f"Lot 41 lineage changed: {field}")
        require(audit["lineage"][field] == value, f"Lot 41 audit lineage changed: {field}")


def _validate_reference(feature: dict[str, Any]) -> None:
    require(feature["sequence_id"] == 1003, "reference sequence changed")
    require(feature["spread_absolute"] == "0.2", "reference spread changed")
    require(feature["mid_price"] == "50025", "reference mid changed")
    require(
        feature["spread_bps"] == "0.03998000999500249875062468766",
        "reference spread bps changed",
    )
    require(
        feature["microprice"] == "50025.01612903225806451612903",
        "reference microprice changed",
    )
    require(feature["observed_depth_only"] is True, "observed-depth-only changed")
    require(feature["extrapolated"] is False, "frozen evidence became extrapolated")
    bands = feature["depth_bands"]
    require([item["band_bps"] for item in bands] == ["0.025", "0.05", "0.1"], "depth bands changed")
    require([item["bid_quantity"] for item in bands] == ["0.9", "0.9", "1.4"], "bid depth changed")
    require([item["ask_quantity"] for item in bands] == ["0.65", "1.75", "2.15"], "ask depth changed")
    quality = feature["book_quality"]
    require(quality["health_status"] == "HEALTHY", "upstream health changed")
    require(quality["book_health_score"] == "100", "upstream health score changed")
    require(quality["consequence"] == "NONE", "upstream consequence changed")


def _validate_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    feature = load_json_object(FEATURE_PATH)
    _verify_checksum(state, "output_checksum", EXPECTED_STATE, "Lot 41 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_AUDIT, "Lot 41 audit")
    _verify_checksum(feature, "feature_checksum", EXPECTED_FEATURE, "BookFeatureStateV1")
    require(state["book_features"] == feature, "state/feature payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["feature_checksum"] == EXPECTED_FEATURE, "audit/feature link changed")
    require(state["validation_state"] == VALIDATION_STATE, "state validation changed")
    require(audit["validation_state"] == VALIDATION_STATE, "audit validation changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["run_context"]["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["safety"] == _expected_safety(), "state safety boundary changed")
    require(audit["safety"] == _expected_safety(), "audit safety boundary changed")
    _validate_lineage(state, audit)
    _validate_reference(feature)
    return state, audit, feature


def _validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load_json_object(COVERAGE_PATH)
    mutation = load_json_object(MUTATION_PATH)
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 100.0, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 100.0, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["mutation_score_percent"] == 81.93, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation below threshold")
    require(mutation["killed_mutants"] == 966, "mutation killed count changed")
    require(mutation["survived_mutants"] == 213, "mutation survivor count changed")
    require(mutation["evaluated_mutants"] == 1179, "mutation evaluated count changed")
    require(mutation["total_mutants"] == 1179, "mutation total changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "mutation suspicious count changed")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    require(mutation["mutmut_run_exit_code"] == 0, "mutmut run failed")
    require(mutation["mutmut_results_exit_code"] == 0, "mutmut results failed")
    return coverage, mutation


def _validate_lot42_lock() -> None:
    for path in LOT42_FORBIDDEN:
        require(not path.exists(), f"Lot 42 must remain locked: {path}")


def validate() -> dict[str, object]:
    state, audit, feature = _validate_artifacts()
    coverage, mutation = _validate_quality()
    _validate_lot42_lock()
    result: dict[str, object] = {
        "schema_version": "lot41-frozen-evidence-validation-v1",
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "gate_merge": GATE_MERGE,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "feature_checksum": feature["feature_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "validation_run": VALIDATION_RUN,
        "validation_artifact": VALIDATION_ARTIFACT,
        "validation_artifact_digest": VALIDATION_DIGEST,
        "mutation_run": MUTATION_RUN,
        "mutation_artifact": MUTATION_ARTIFACT,
        "mutation_artifact_digest": MUTATION_DIGEST,
        "next_lot": 42,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot41FrozenEvidenceError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT41 FROZEN EVIDENCE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
