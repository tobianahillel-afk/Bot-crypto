#!/usr/bin/env python3
from __future__ import annotations

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

SOURCE_HEAD = "2d91da1777f1ccbd7f81563dbc74fd3b89eecdf2"
EVIDENCE_HEAD = "3655b18a24cafb3383dfeb2709904af59044535f"
GATE_MERGE = "7456c5b80b609ee5958d8b6da0effd489faa308c"
VALIDATION_RUN = 31509163914
VALIDATION_ARTIFACT = 9108342857
VALIDATION_DIGEST = "sha256:38f90077aebf0e02ec34cec28cba631b6f366755937837a8e14652a990630cbe"
MUTATION_RUN = 31509163840
MUTATION_ARTIFACT = 9108422274
MUTATION_DIGEST = "sha256:fbefcbd17b112ab2660e7ebb6366827616dffbabd76c9a591a9d620495a2f6e2"

STATE_PATH = ROOT / "data/audit/liquidity_zones_walls_and_voids_engine_lot42.json"
AUDIT_PATH = ROOT / "data/audit/liquidity_zones_walls_and_voids_engine_audit_lot42.json"
ZONE_SET_PATH = ROOT / "data/audit/liquidity_zone_set_lot42.json"
COVERAGE_PATH = ROOT / "reports/lot42/coverage_summary.json"
MUTATION_PATH = ROOT / "reports/lot42/mutation_summary.json"

EXPECTED_STATE = "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0"
EXPECTED_AUDIT = "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f"
EXPECTED_ZONE_SET = "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89"
EXPECTED_GATE = "7ab3b17a74d30866fbec4ec15acfe608a9545e8831d80dcb39db2d059e293924"
EXPECTED_CONFIG = "81acdd9e6d0a7d3ead9d4d483f71485082f591be8efd8480d70f4525113c47b6"
EXPECTED_LOT41_STATE = "23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573"
EXPECTED_LOT41_AUDIT = "af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd"
EXPECTED_LOT41_FEATURE = "77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5"
EXPECTED_LOT39_BOOK = "a503d56b312cbb21586712fcf929a0381cbc9adde9c5d70700e1f7166ef58dde"
EXPECTED_DELTA_FIXTURE = "1e7528a350ca78e21c4832b4af0ef4763e6bbadec82ea0f55a1005502cadff97"
EXPECTED_LOT38_SNAPSHOT = "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
VALIDATION_STATE = "VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY"

LOT43_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py",
    ROOT / "config/microstructure/book_resilience_and_replenishment_engine_v1.json",
    ROOT / "scripts/run_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "scripts/validate_lot43.py",
    ROOT / "tests/test_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "docs/LOT_43_BOOK_RESILIENCE_AND_REPLENISHMENT_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_43.md",
)


class Lot42FrozenEvidenceError(RuntimeError):
    """Raised when Lot 42 frozen evidence no longer matches certification."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot42FrozenEvidenceError(message)


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
        "lot41_state_checksum": EXPECTED_LOT41_STATE,
        "lot41_audit_checksum": EXPECTED_LOT41_AUDIT,
        "lot41_feature_checksum": EXPECTED_LOT41_FEATURE,
        "lot39_book_checksum": EXPECTED_LOT39_BOOK,
        "lot39_delta_fixture_checksum": EXPECTED_DELTA_FIXTURE,
        "lot38_snapshot_checksum": EXPECTED_LOT38_SNAPSHOT,
    }
    for field, value in expected.items():
        require(state["lineage"][field] == value, f"Lot 42 lineage changed: {field}")
        require(audit["lineage"][field] == value, f"Lot 42 audit lineage changed: {field}")
    require(state["lineage"] == audit["lineage"], "state/audit lineage diverged")


def _validate_reference(zone_set: dict[str, Any], state: dict[str, Any]) -> None:
    require(zone_set["sequence_id"] == 1003, "reference sequence changed")
    require(zone_set["history_sequence_ids"] == [1001, 1002, 1003], "reference history changed")
    require(zone_set["mid_price"] == "50025", "reference mid changed")
    require(zone_set["observed_book_only"] is True, "observed-book-only changed")
    require(zone_set["participant_intent_inferred"] is False, "participant intent inference enabled")
    require(zone_set["expired_candidates_total"] == 0, "reference expiry count changed")
    zones = zone_set["zones"]
    voids = zone_set["voids"]
    require(len(zones) == 3, "active zone count changed")
    require(len(voids) == 1, "liquidity void count changed")
    require(sum("DISPLAYED_WALL" in item["classifications"] for item in zones) == 3, "wall count changed")
    require(sum("PERSISTENT_ZONE" in item["classifications"] for item in zones) == 2, "persistent count changed")
    require(sum(item["confidence_status"] == "LOW_CONFIDENCE" for item in zones) == 1, "low-confidence count changed")
    require(all(item["participant_intent"] == "NOT_INFERRED" for item in zones), "zone intent changed")
    require(all(item["participant_intent"] == "NOT_INFERRED" for item in voids), "void intent changed")
    require(voids[0]["side"] == "BID", "reference void side changed")
    require(voids[0]["near_price"] == "50024.9", "reference void near price changed")
    require(voids[0]["far_price"] == "50024.7", "reference void far price changed")
    metrics = state["metrics"]
    require(metrics["lot_42_observations_total"] == 3, "observation count changed")
    require(metrics["lot_42_active_zones_total"] == 3, "metric active zone count changed")
    require(metrics["lot_42_displayed_walls_total"] == 3, "metric wall count changed")
    require(metrics["lot_42_persistent_zones_total"] == 2, "metric persistent count changed")
    require(metrics["lot_42_low_confidence_walls_total"] == 1, "metric confidence count changed")
    require(metrics["lot_42_liquidity_voids_total"] == 1, "metric void count changed")


def _validate_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    zone_set = load_json_object(ZONE_SET_PATH)
    _verify_checksum(state, "output_checksum", EXPECTED_STATE, "Lot 42 state")
    _verify_checksum(audit, "audit_checksum", EXPECTED_AUDIT, "Lot 42 audit")
    _verify_checksum(zone_set, "zone_set_checksum", EXPECTED_ZONE_SET, "LiquidityZoneSetV1")
    require(state["liquidity_zones"] == zone_set, "state/zone-set payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["zone_set_checksum"] == EXPECTED_ZONE_SET, "audit/zone-set link changed")
    require(state["validation_state"] == VALIDATION_STATE, "validation state changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source head changed")
    require(audit["run_context"]["code_commit"] == SOURCE_HEAD, "audit source head changed")
    require(state["safety"] == _expected_safety(), "state safety boundary changed")
    require(audit["safety"] == _expected_safety(), "audit safety boundary changed")
    _validate_lineage(state, audit)
    _validate_reference(zone_set, state)
    return state, audit, zone_set


def _validate_quality() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load_json_object(COVERAGE_PATH)
    mutation = load_json_object(MUTATION_PATH)
    require(coverage["status"] == "PASS", "coverage evidence not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source head changed")
    require(coverage["line_coverage_percent"] == 98.17, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 93.07, "branch coverage changed")
    require(coverage["line_coverage_percent"] >= 95.0, "line coverage below threshold")
    require(coverage["branch_coverage_percent"] >= 90.0, "branch coverage below threshold")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake evidence changed")
    require(mutation["status"] == "PASS", "mutation evidence not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source head changed")
    require(mutation["mutation_score_percent"] == 80.1, "mutation score changed")
    require(mutation["mutation_score_percent"] >= 80.0, "mutation below threshold")
    require(mutation["killed_mutants"] == 1803, "mutation killed count changed")
    require(mutation["survived_mutants"] == 448, "mutation survivor count changed")
    require(mutation["evaluated_mutants"] == 2251, "mutation evaluated count changed")
    require(mutation["completed_mutants"] == 2251, "mutation completed count changed")
    require(mutation["total_mutants"] == 2251, "mutation total changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout count changed")
    require(mutation["suspicious_mutants"] == 0, "mutation suspicious count changed")
    require(mutation["max_children"] == 1, "mutation worker policy changed")
    require(mutation["python_hash_seed"] == "0", "mutation hash seed changed")
    require(mutation["mutmut_run_exit_code"] == 0, "mutmut run failed")
    require(mutation["mutmut_results_exit_code"] == 0, "mutmut results failed")
    return coverage, mutation


def _validate_lot43_lock() -> None:
    for path in LOT43_FORBIDDEN:
        require(not path.exists(), f"Lot 43 must remain locked: {path}")


def validate() -> dict[str, object]:
    state, audit, zone_set = _validate_artifacts()
    coverage, mutation = _validate_quality()
    _validate_lot43_lock()
    result: dict[str, object] = {
        "schema_version": "lot42-frozen-evidence-validation-v1",
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "gate_merge": GATE_MERGE,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "zone_set_checksum": zone_set["zone_set_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "validation_run": VALIDATION_RUN,
        "validation_artifact": VALIDATION_ARTIFACT,
        "validation_artifact_digest": VALIDATION_DIGEST,
        "mutation_run": MUTATION_RUN,
        "mutation_artifact": MUTATION_ARTIFACT,
        "mutation_artifact_digest": MUTATION_DIGEST,
        "next_lot": 43,
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
    except (Lot42FrozenEvidenceError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT42 FROZEN EVIDENCE: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
