#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from validate_lot40_frozen_evidence import validate as validate_frozen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEAD = "b9a18a8aaef858b985c3f75ef2aa8955ec521e9f"
EVIDENCE_HEAD = "ea04fe826261eeed5a59eea60265b38b68404b6b"
FINAL_PR_HEAD = "1268772c07cbb76c18b3267aef12dad5ba58af31"
MERGED_COMMIT = "88f0dac660e262a1c468d9cd75c5e7996ce4817b"
VALIDATION_RUN = 31425236798
VALIDATION_ARTIFACT = 9076940399
VALIDATION_DIGEST = "sha256:50e77a5ae432979142621402980ad2a42022857fef1303b69a805b84d3d2d9a5"
MUTATION_RUN = 31425236875
MUTATION_ARTIFACT = 9077043930
MUTATION_DIGEST = "sha256:e5ef9cdec8365862eca6c011ea71895f890ff16047290220377d0ebda56d1c8e"


class Lot40PostMergeError(RuntimeError):
    """Raised when independent Lot 40 post-merge certification fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot40PostMergeError(message)


def load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
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


def validate_release_and_lifecycle() -> dict[str, Any]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    require(project["version"] == "0.40.0", "project version must be 0.40.0")
    require("Lot 40" in project["description"], "project description must identify Lot 40")

    previous = load("data/audit/roadmap_lifecycle_overlay_lot39.json")
    current = load("data/audit/roadmap_lifecycle_overlay_lot40.json")
    require(
        current["previous_overlay"]
        == "data/audit/roadmap_lifecycle_overlay_lot39.json",
        "Lot40 lifecycle predecessor mismatch",
    )
    require(previous["latest_implemented_lot"] == 39, "Lot39 historical overlay changed")
    require(current["latest_implemented_lot"] == 40, "latest implemented lot must be 40")
    require(
        current["lots"]["39"] == previous["lots"]["39"],
        "Lot39 lifecycle record drifted",
    )

    lot40 = current["lots"]["40"]
    expected = {
        "status": "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY",
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "pull_request": 48,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
    }
    for key, value in expected.items():
        require(lot40.get(key) == value, f"Lot40 lifecycle mismatch: {key}")
    require(lot40.get("analysis_only") is True, "Lot40 analysis_only changed")
    require(lot40.get("approved_size") == 0, "Lot40 approved_size changed")
    for key in (
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "market_event_publication_allowed",
        "raw_data_mutation_allowed",
        "scenario_score_is_signal",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
        require(lot40.get(key) is False, f"Lot40 permission enabled: {key}")
    require(
        current["lots"]["41"]
        == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot41 historical certification lock changed",
    )
    return current


def validate_docs() -> None:
    audit = (ROOT / "docs/LOT_40_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/LOT40_POST_MERGE_VALIDATION_MATRIX.md").read_text(
        encoding="utf-8"
    )
    required = (
        SOURCE_HEAD,
        EVIDENCE_HEAD,
        FINAL_PR_HEAD,
        MERGED_COMMIT,
        str(VALIDATION_RUN),
        str(VALIDATION_ARTIFACT),
        VALIDATION_DIGEST,
        str(MUTATION_RUN),
        str(MUTATION_ARTIFACT),
        MUTATION_DIGEST,
    )
    for text in (audit, matrix):
        for value in required:
            require(
                value in text,
                "Lot40 post-merge documentation missing exact evidence",
            )
    require("GO_LOT40_POST_MERGE" in audit, "Lot40 post-merge GO verdict missing")
    require(
        "PLANNED_LOCKED" in audit and "Lot 41" in audit,
        "Lot41 historical lock missing",
    )


def validate() -> dict[str, object]:
    frozen = validate_frozen()
    require(frozen["status"] == "PASS", "Lot40 frozen evidence is not PASS")
    require(frozen["source_head"] == SOURCE_HEAD, "Lot40 frozen source head changed")
    require(
        frozen["evidence_head"] == EVIDENCE_HEAD,
        "Lot40 frozen evidence head changed",
    )
    require(frozen["line_coverage_percent"] == 97.31, "Lot40 line coverage changed")
    require(
        frozen["branch_coverage_percent"] == 91.24,
        "Lot40 branch coverage changed",
    )
    require(
        frozen["mutation_score_percent"] == 82.32,
        "Lot40 mutation score changed",
    )
    require(
        frozen["state_output_checksum"]
        == "e601f60e8fad70c4c445955dda503a3b728614936ca17c964cb2ed9c8a927477",
        "Lot40 state checksum changed",
    )
    require(
        frozen["audit_checksum"]
        == "978e910d326e6895b652e256f980bc33203092157334ebe3824ebbf31da1632c",
        "Lot40 audit checksum changed",
    )
    require(
        frozen["integrity_checksum"]
        == "35b9941782811766762eea067fea53f7c026fbe9ea8699f911c34d648b409d2a",
        "Lot40 integrity checksum changed",
    )
    require(
        frozen["veto_checksum"]
        == "000613129dbce4bfa189f66a9927c442a557556870381de92aa2b8da8a7951fc",
        "Lot40 veto checksum changed",
    )
    require(frozen["health_status"] == "HEALTHY", "Lot40 reference health changed")
    require(frozen["book_health_score"] == "100", "Lot40 reference score changed")
    require(frozen["consequence"] == "NONE", "Lot40 reference consequence changed")

    lifecycle = validate_release_and_lifecycle()
    validate_docs()
    result: dict[str, object] = {
        "schema_version": "lot40-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT40_POST_MERGE",
        "project_version": "0.40.0",
        "source_head": SOURCE_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": MERGED_COMMIT,
        "line_coverage_percent": frozen["line_coverage_percent"],
        "branch_coverage_percent": frozen["branch_coverage_percent"],
        "mutation_score_percent": frozen["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot_at_certification": 41,
        "next_lot_status_at_certification": lifecycle["lots"]["41"]["status"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = checksum(result)
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot40PostMergeError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT40 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
