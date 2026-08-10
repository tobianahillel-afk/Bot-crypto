#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from validate_lot39_frozen_evidence import validate as validate_frozen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "203a2b2d3d69644bd67c0e583df9d0405941def6"
EVIDENCE_HEAD = "b1bf9605fe20cacca76861e3fc6941ad38ea8f23"
FINAL_PR_HEAD = "3dc7ec29bb1a4152017854581573c26465ee33a2"
MERGED_COMMIT = "e2b787905e126a4f8ba19c933d39550ad338ac74"
VALIDATION_RUN = 31392299867
VALIDATION_ARTIFACT = 9064203889
VALIDATION_DIGEST = "sha256:5312bb4008fbf70d95cf50cc4cee4e2e38de12cb8825ae2834d0e425b68181a1"
MUTATION_RUN = 31392299824
MUTATION_ARTIFACT = 9064269635
MUTATION_DIGEST = "sha256:024b3ce65daca395a24d0c5c23c1ef0ecfc4ca1a94b98690f2cb5755dbbf93bf"


class Lot39PostMergeError(RuntimeError):
    """Raised when independent Lot 39 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot39PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def checksum(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_release_and_lifecycle() -> dict[str, Any]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["version"] == "0.39.0", "project version must be 0.39.0")
    require("Lot 39" in project["description"], "project description must identify Lot 39")
    previous = load("data/audit/roadmap_lifecycle_overlay_lot38.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot39.json")
    require(current["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot38.json", "Lot39 predecessor mismatch")
    require(current["latest_implemented_lot"] == 39, "latest implemented lot must be 39")
    require(previous["latest_implemented_lot"] == 38, "Lot38 historical overlay changed")
    lot39 = current["lots"]["39"]
    expected = {
        "status": "IMPLEMENTED_VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY",
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 45,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for key, value in expected.items():
        require(lot39.get(key) == value, f"Lot39 lifecycle mismatch: {key}")
    require(lot39.get("analysis_only") is True, "Lot39 analysis_only changed")
    require(lot39.get("approved_size") == 0, "Lot39 approved_size changed")
    for key in (
        "used_for_decision", "external_connectivity_allowed", "network_ingestion_allowed",
        "real_credentials_allowed", "market_event_publication_allowed", "raw_data_mutation_allowed",
        "scenario_score_is_signal", "signal_generation_allowed", "risk_approval_allowed",
        "order_routing_allowed", "trade_allowed", "execution_allowed",
    ):
        require(lot39.get(key) is False, f"Lot39 permission enabled: {key}")
    require(current["lots"]["40"] == {"implementation_started": False, "status": "PLANNED_LOCKED"}, "Lot40 must remain locked")
    return current


def validate_docs() -> None:
    audit = (ROOT / "docs/LOT_39_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/LOT39_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    for text in (audit, matrix):
        for value in (
            SOURCE_HEAD, EVIDENCE_HEAD, FINAL_PR_HEAD, MERGED_COMMIT,
            str(VALIDATION_RUN), str(VALIDATION_ARTIFACT), VALIDATION_DIGEST,
            str(MUTATION_RUN), str(MUTATION_ARTIFACT), MUTATION_DIGEST,
        ):
            require(value in text, "post-merge documentation missing exact evidence")
    require("GO_LOT39_POST_MERGE" in audit, "post-merge GO verdict missing")
    require("PLANNED_LOCKED" in audit and "Lot 40" in audit, "Lot40 lock missing")


def validate_lot40_absence() -> None:
    forbidden = (
        "src/crypto_quant_bot/microstructure/book_integrity_and_desynchronization_detector.py",
        "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector.py",
        "scripts/run_lot40_book_integrity_and_desynchronization_detector.py",
        "scripts/validate_lot40.py",
    )
    for path in forbidden:
        require(not (ROOT / path).exists(), f"Lot40 implementation present: {path}")


def validate() -> dict[str, object]:
    frozen = validate_frozen()
    require(frozen["status"] == "PASS", "Lot39 frozen evidence is not PASS")
    require(frozen["source_head"] == SOURCE_HEAD, "frozen source head changed")
    require(frozen["evidence_head"] == EVIDENCE_HEAD, "frozen evidence head changed")
    require(frozen["line_coverage_percent"] == 99.24, "line coverage changed")
    require(frozen["branch_coverage_percent"] == 96.97, "branch coverage changed")
    require(frozen["mutation_score_percent"] == 81.81, "mutation score changed")
    lifecycle = validate_release_and_lifecycle()
    validate_docs()
    validate_lot40_absence()
    result: dict[str, object] = {
        "schema_version": "lot39-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT39_POST_MERGE",
        "project_version": "0.39.0",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "line_coverage_percent": frozen["line_coverage_percent"],
        "branch_coverage_percent": frozen["branch_coverage_percent"],
        "mutation_score_percent": frozen["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 40,
        "next_lot_status": lifecycle["lots"]["40"]["status"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot39PostMergeError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT39 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
