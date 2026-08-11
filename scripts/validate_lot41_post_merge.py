#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from validate_lot41_frozen_evidence import validate as validate_frozen_evidence

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "14c0d8da1b02d076b3c43a07a34ac96c673018b0"
EVIDENCE_HEAD = "7ada0ca6c4d439505ef453b988dedd4aa96c1a32"
FINAL_PR_HEAD = "89ae244db77f16f31d226a7494d78b65b904dcd9"
MERGED_COMMIT = "a253ce35c97303e8b8c65707c07597e996b3a832"
GATE_MERGE = "75822f8ea7c6f67f73649d2f43be6efba840ab67"
VALIDATION_RUN = 31484227338
VALIDATION_ARTIFACT = 9098457077
VALIDATION_DIGEST = "sha256:61431809213962e498f548bf87ed75f5519ac53e7da9bb876f3e118389863320"
MUTATION_RUN = 31484227363
MUTATION_ARTIFACT = 9098475166
MUTATION_DIGEST = "sha256:b64f1b9b5452586f3dfba0b2c456ad911e6fa9d688b023ce78b6100f263c4ab8"
FROZEN_RUN = 31484227389
FROZEN_ARTIFACT = 9098452090
FROZEN_DIGEST = "sha256:7ffb95dd0ec22987f705999af139104100995ec1225fdb2bb51a206c3fc563e9"

PREVIOUS_OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot40.json"
CURRENT_OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot41.json"
AUDIT_DOC = ROOT / "docs/LOT_41_POST_MERGE_AUDIT.md"
MATRIX_DOC = ROOT / "docs/LOT41_POST_MERGE_VALIDATION_MATRIX.md"
IMPLEMENTATION_REPORT = ROOT / "reports/lot_41_spread_depth_and_imbalance_engine_report.md"

LOT42_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py",
    ROOT / "scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py",
    ROOT / "scripts/validate_lot42.py",
)


class Lot41PostMergeError(RuntimeError):
    """Raised when the independent Lot 41 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot41PostMergeError(message)


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
    require(project.get("version") == "0.41.0", "project version must be 0.41.0")
    description = project.get("description")
    require(
        isinstance(description, str) and "Lot 41" in description,
        "release description must identify Lot 41",
    )
    report = IMPLEMENTATION_REPORT.read_text(encoding="utf-8")
    require(
        "PASS_FROZEN_IMPLEMENTATION_EVIDENCE" in report,
        "frozen implementation verdict missing",
    )


def validate_lot41_record(record: dict[str, Any]) -> None:
    expected = {
        "status": "IMPLEMENTED_VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY",
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 51,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_contract": "docs/LOT_41_SPREAD_DEPTH_AND_IMBALANCE_ENGINE.md",
        "acceptance_contract": "docs/ACCEPTANCE_CRITERIA_LOT_41.md",
        "state_artifact": "data/audit/spread_depth_and_imbalance_engine_lot41.json",
        "audit_artifact": "data/audit/spread_depth_and_imbalance_engine_audit_lot41.json",
        "feature_artifact": "data/audit/book_feature_state_lot41.json",
        "quality_coverage_evidence": "reports/lot41/coverage_summary.json",
        "quality_mutation_evidence": "reports/lot41/mutation_summary.json",
        "report": "reports/lot_41_spread_depth_and_imbalance_engine_report.md",
        "post_merge_audit": "docs/LOT_41_POST_MERGE_AUDIT.md",
        "runner": "scripts/run_lot41_spread_depth_and_imbalance_engine.py",
        "validator": "scripts/validate_lot41.py",
    }
    for field, value in expected.items():
        require(record.get(field) == value, f"Lot41 lifecycle mismatch: {field}")
    for field, value in expected_safety().items():
        require(record.get(field) == value, f"Lot41 safety mismatch: {field}")


def validate_lifecycle() -> dict[str, Any]:
    previous = load(PREVIOUS_OVERLAY)
    current = load(CURRENT_OVERLAY)
    require(previous.get("latest_implemented_lot") == 40, "Lot40 historical overlay changed")
    require(
        current.get("previous_overlay") == str(PREVIOUS_OVERLAY.relative_to(ROOT)),
        "Lot41 lifecycle predecessor mismatch",
    )
    require(current.get("latest_implemented_lot") == 41, "latest implemented lot must be 41")
    previous_lots = previous.get("lots")
    current_lots = current.get("lots")
    require(
        isinstance(previous_lots, dict) and isinstance(current_lots, dict),
        "lifecycle lot map missing",
    )
    require(current_lots.get("40") == previous_lots.get("40"), "Lot40 lifecycle record drifted")
    lot41 = current_lots.get("41")
    require(isinstance(lot41, dict), "Lot41 lifecycle record missing")
    validate_lot41_record(lot41)
    require(
        current_lots.get("42") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot42 lifecycle lock changed",
    )
    return current


def validate_frozen() -> dict[str, object]:
    frozen = validate_frozen_evidence()
    expected = {
        "status": "PASS",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "gate_merge": GATE_MERGE,
        "state_output_checksum": "23bc1713999aa6dd4d52edefe0b024860636f6f07864c4f8c97b4e91d47ba573",
        "audit_checksum": "af8f4715c501e3cab5a74f3fc66619637256206d2f3ed3d3494681dd0c9a6bbd",
        "feature_checksum": "77a6f6b92cae8094292bb8a8b553c57a52e4c73d376251c9e55e8221d2376ab5",
        "line_coverage_percent": 100.0,
        "branch_coverage_percent": 100.0,
        "mutation_score_percent": 81.93,
        "next_lot": 42,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected.items():
        require(frozen.get(field) == value, f"Lot41 frozen evidence mismatch: {field}")
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
    require("GO_LOT41_POST_MERGE" in audit, "Lot41 post-merge GO verdict missing")
    require(
        "Lot 42" in audit and "PLANNED_LOCKED" in audit,
        "Lot42 lock missing from audit",
    )


def validate_lot42_absence() -> None:
    for path in LOT42_FORBIDDEN:
        require(not path.exists(), f"Lot42 implementation must remain absent: {path}")


def validate() -> dict[str, object]:
    validate_release()
    frozen = validate_frozen()
    lifecycle = validate_lifecycle()
    validate_docs()
    validate_lot42_absence()
    result: dict[str, object] = {
        "schema_version": "lot41-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT41_POST_MERGE",
        "project_version": "0.41.0",
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "line_coverage_percent": frozen["line_coverage_percent"],
        "branch_coverage_percent": frozen["branch_coverage_percent"],
        "mutation_score_percent": frozen["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 42,
        "next_lot_status": lifecycle["lots"]["42"]["status"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot41PostMergeError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT41 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
