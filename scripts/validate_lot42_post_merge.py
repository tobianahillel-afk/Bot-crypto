#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from validate_lot42_frozen_evidence import validate as validate_frozen_evidence

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "2d91da1777f1ccbd7f81563dbc74fd3b89eecdf2"
EVIDENCE_HEAD = "3655b18a24cafb3383dfeb2709904af59044535f"
FINAL_PR_HEAD = "85f0a141d52d448a452ff1493050a3bf31a23dce"
MERGED_COMMIT = "3a7226b4beeb23bfeee976243efc0057cac69e0e"
GATE_MERGE = "7456c5b80b609ee5958d8b6da0effd489faa308c"
VALIDATION_RUN = 31510169694
VALIDATION_ARTIFACT = 9108858997
VALIDATION_DIGEST = "sha256:ed8fdc89d3e37869ccd8a677e95d182304345018703911556ed0323903d22b6d"
MUTATION_RUN = 31510169749
MUTATION_ARTIFACT = 9108976924
MUTATION_DIGEST = "sha256:f8810abe404c5833bc5baa5581aa4b769ce59aab44aede0ac783cae17b2621a8"
FROZEN_RUN = 31510169788
FROZEN_ARTIFACT = 9108812060
FROZEN_DIGEST = "sha256:859b415baa1b99589d312d907ad73798fb822289511ede814acc28c92e74d90d"

PREVIOUS_OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot41.json"
CURRENT_OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot42.json"
AUDIT_DOC = ROOT / "docs/LOT_42_POST_MERGE_AUDIT.md"
MATRIX_DOC = ROOT / "docs/LOT42_POST_MERGE_VALIDATION_MATRIX.md"
IMPLEMENTATION_REPORT = ROOT / "reports/lot_42_liquidity_zones_walls_and_voids_engine_report.md"

LOT43_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py",
    ROOT / "config/microstructure/book_resilience_and_replenishment_engine_v1.json",
    ROOT / "contracts/schemas/book_resilience_and_replenishment_engine_state_v1.schema.json",
    ROOT / "contracts/schemas/book_resilience_and_replenishment_engine_audit_v1.schema.json",
    ROOT / "scripts/run_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "scripts/validate_lot43.py",
    ROOT / "tests/test_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "docs/LOT_43_BOOK_RESILIENCE_AND_REPLENISHMENT_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_43.md",
    ROOT / "reports/lot_43_book_resilience_and_replenishment_engine_report.md",
)


class Lot42PostMergeError(RuntimeError):
    """Raised when the independent Lot 42 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot42PostMergeError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def expected_safety() -> dict[str, object]:
    return {
        "analysis_only": True,
        "used_for_decision": False,
        "external_connectivity_allowed": False,
        "network_ingestion_allowed": False,
        "real_credentials_allowed": False,
        "market_event_publication_allowed": False,
        "raw_data_mutation_allowed": False,
        "participant_behavior_inference_explicitly_labeled": True,
        "scenario_score_is_signal": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def validate_release() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata.get("project")
    require(isinstance(project, dict), "project metadata missing")
    require(project.get("version") == "0.42.0", "project version must be 0.42.0")
    description = project.get("description")
    require(
        isinstance(description, str)
        and "Lot 42" in description
        and "post-merge audited" in description,
        "release description must identify audited Lot 42",
    )
    report = IMPLEMENTATION_REPORT.read_text(encoding="utf-8")
    require(
        "PASS_FROZEN_IMPLEMENTATION_EVIDENCE" in report,
        "frozen implementation verdict missing",
    )


def validate_lot42_record(record: dict[str, Any]) -> None:
    expected = {
        "status": "IMPLEMENTED_VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY",
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 54,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_contract": "docs/LOT_42_LIQUIDITY_ZONES_WALLS_AND_VOIDS_ENGINE.md",
        "acceptance_contract": "docs/ACCEPTANCE_CRITERIA_LOT_42.md",
        "state_artifact": "data/audit/liquidity_zones_walls_and_voids_engine_lot42.json",
        "audit_artifact": "data/audit/liquidity_zones_walls_and_voids_engine_audit_lot42.json",
        "zone_set_artifact": "data/audit/liquidity_zone_set_lot42.json",
        "quality_coverage_evidence": "reports/lot42/coverage_summary.json",
        "quality_mutation_evidence": "reports/lot42/mutation_summary.json",
        "report": "reports/lot_42_liquidity_zones_walls_and_voids_engine_report.md",
        "post_merge_audit": "docs/LOT_42_POST_MERGE_AUDIT.md",
        "runner": "scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py",
        "validator": "scripts/validate_lot42.py",
    }
    for field, value in expected.items():
        require(record.get(field) == value, f"Lot42 lifecycle mismatch: {field}")
    for field, value in expected_safety().items():
        require(record.get(field) == value, f"Lot42 safety mismatch: {field}")


def validate_lifecycle() -> dict[str, Any]:
    previous = load(PREVIOUS_OVERLAY)
    current = load(CURRENT_OVERLAY)
    require(previous.get("latest_implemented_lot") == 41, "Lot41 historical overlay changed")
    require(
        current.get("previous_overlay") == str(PREVIOUS_OVERLAY.relative_to(ROOT)),
        "Lot42 lifecycle predecessor mismatch",
    )
    require(current.get("latest_implemented_lot") == 42, "latest implemented lot must be 42")
    require(
        current.get("historical_registry") == previous.get("historical_registry"),
        "historical registry binding changed",
    )
    require(
        current.get("future_capabilities_locked") == previous.get("future_capabilities_locked"),
        "future capability lock registry changed",
    )
    previous_lots = previous.get("lots")
    current_lots = current.get("lots")
    require(
        isinstance(previous_lots, dict) and isinstance(current_lots, dict),
        "lifecycle lot map missing",
    )
    require(current_lots.get("41") == previous_lots.get("41"), "Lot41 lifecycle record drifted")
    lot42 = current_lots.get("42")
    require(isinstance(lot42, dict), "Lot42 lifecycle record missing")
    validate_lot42_record(lot42)
    require(
        current_lots.get("43") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot43 lifecycle lock changed",
    )
    return current


def validate_frozen() -> dict[str, object]:
    frozen = validate_frozen_evidence()
    expected = {
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "gate_merge": GATE_MERGE,
        "state_output_checksum": "6e1fe348dc9fdc262d2f27990c6f3234f0b1ed71f5bfb3347fe27a9e458af8b0",
        "audit_checksum": "b562b0cca61e0b10fbacf4a2318ef1075230b57388fe0240de0ca3d200582e3f",
        "zone_set_checksum": "f5769313ec5f9f6de503b1eb9a40c31262ddf0eba6131f791c070f6557168c89",
        "line_coverage_percent": 98.17,
        "branch_coverage_percent": 93.07,
        "mutation_score_percent": 80.1,
        "next_lot": 43,
        "next_lot_status": "PLANNED_LOCKED",
        "participant_intent_inferred": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected.items():
        require(frozen.get(field) == value, f"Lot42 frozen evidence mismatch: {field}")
    return frozen


def validate_docs() -> None:
    audit = AUDIT_DOC.read_text(encoding="utf-8")
    matrix = MATRIX_DOC.read_text(encoding="utf-8")
    exact_values = (
        SOURCE_HEAD,
        EVIDENCE_HEAD,
        FINAL_PR_HEAD,
        MERGED_COMMIT,
        GATE_MERGE,
        str(VALIDATION_RUN),
        str(VALIDATION_ARTIFACT),
        VALIDATION_DIGEST,
        str(MUTATION_RUN),
        str(MUTATION_ARTIFACT),
        MUTATION_DIGEST,
        str(FROZEN_RUN),
        str(FROZEN_ARTIFACT),
        FROZEN_DIGEST,
    )
    for text in (audit, matrix):
        for value in exact_values:
            require(value in text, "post-merge documentation missing exact evidence")
    require("GO_LOT42_POST_MERGE" in audit, "Lot42 post-merge GO verdict missing")
    require(
        "Lot 43" in audit and "PLANNED_LOCKED" in audit,
        "Lot43 lock missing from audit",
    )
    require("0.42.0" in audit, "Lot42 release missing from audit")


def validate_lot43_absence() -> None:
    for path in LOT43_FORBIDDEN:
        require(not path.exists(), f"Lot43 implementation must remain absent: {path}")


def validate() -> dict[str, object]:
    validate_release()
    frozen = validate_frozen()
    lifecycle = validate_lifecycle()
    validate_docs()
    validate_lot43_absence()
    result: dict[str, object] = {
        "schema_version": "lot42-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT42_POST_MERGE",
        "project_version": "0.42.0",
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "line_coverage_percent": frozen["line_coverage_percent"],
        "branch_coverage_percent": frozen["branch_coverage_percent"],
        "mutation_score_percent": frozen["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 43,
        "next_lot_status": lifecycle["lots"]["43"]["status"],
        "participant_intent_inferred": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot42PostMergeError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT42 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
