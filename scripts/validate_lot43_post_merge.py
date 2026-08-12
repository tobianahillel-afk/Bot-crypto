#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_lot43_frozen_evidence as frozen  # noqa: E402

GATE_MERGE = "ed8845e0e56151348fe57c0e9bceaf4646ea49aa"
SOURCE_HEAD = "d45f40aec90b26dd1278ec2f49b405fa5b2ed94e"
CERTIFICATION_ANCHOR = "2b04ea3470f404a57c7a2778b3dccacd889d1fcc"
EVIDENCE_HEAD = "76c0670d7933f29965306993ff217647def0f0d4"
CERTIFIED_CONTENT_HEAD = "fd5cbe23d22dcd34d85e97c79667d7d98d1ddaff"
FINAL_PR_HEAD = "69667b5c46ac2ecf7b2a64656f84c374ee929dbf"
IMPLEMENTATION_MERGE = "0b524b1478272e0a69a06b50c68b1b2c3b092964"
IMPLEMENTATION_PR = 57
RELEASE = "0.43.0"
STATUS = "IMPLEMENTED_VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY"

SOURCE_PROOF = (
    31642595060,
    9159515091,
    "sha256:7878366052c7188221d2819f1b0bb447d265c82e8b701d80b675f7c22d024b90",
)
MUTATION_PROOF = (
    31642595056,
    9159605334,
    "sha256:124ffd3b1b8d18310fd86cbdfc314ebab904a6a329594a3249f5201683d660f5",
)
FROZEN_PROOF = (
    31643513115,
    9159962077,
    "sha256:c34bea93fb5f0afb0a36810a6df72d0c71982531f3d000f325c485e984925ace",
)

OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot43.json"
PREVIOUS_OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot42.json"
AUDIT_DOC = ROOT / "docs/LOT_43_POST_MERGE_AUDIT.md"
MATRIX_DOC = ROOT / "docs/LOT43_POST_MERGE_VALIDATION_MATRIX.md"
PYPROJECT = ROOT / "pyproject.toml"
MUTATION = ROOT / "reports/lot43/mutation_summary.json"

LOT44_FORBIDDEN = frozen.LOT44_FORBIDDEN


class Lot43PostMergeAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot43PostMergeAuditError(message)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"expected object: {path}")
    return payload


def _verify_release() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    require(project["version"] == RELEASE, "release version must be 0.43.0")
    description = project["description"].lower()
    require("lot 43" in description, "release description must identify Lot 43")
    require("post-merge audited" in description, "release description must be post-merge audited")


def _verify_lifecycle() -> None:
    previous = load_json(PREVIOUS_OVERLAY)
    overlay = load_json(OVERLAY)
    previous_path = str(PREVIOUS_OVERLAY.relative_to(ROOT))
    require(overlay["previous_overlay"] == previous_path, "previous overlay changed")
    require(overlay["historical_registry"] == previous["historical_registry"], "historical registry changed")
    require(overlay["future_capabilities_locked"] == previous["future_capabilities_locked"], "future locks changed")
    require(overlay["latest_implemented_lot"] == 43, "latest implemented lot must be 43")
    require(overlay["lots"]["42"] == previous["lots"]["42"], "Lot 42 lifecycle record changed")

    lot43 = overlay["lots"]["43"]
    expected = {
        "status": STATUS,
        "implementation_commit": SOURCE_HEAD,
        "evidence_commit": EVIDENCE_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "merged_commit": IMPLEMENTATION_MERGE,
        "pull_request": IMPLEMENTATION_PR,
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
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
    for key, value in expected.items():
        require(lot43.get(key) == value, f"Lot 43 lifecycle field changed: {key}")

    lot44 = overlay["lots"]["44"]
    expected_lot44 = {"implementation_started": False, "status": "PLANNED_LOCKED"}
    require(lot44 == expected_lot44, "Lot 44 unlocked")


def _verify_frozen() -> dict[str, object]:
    result = frozen.validate()
    require(result["status"] == "PASS", "frozen evidence did not pass")
    require(result["gate_merge"] == GATE_MERGE, "gate merge changed")
    require(result["source_head"] == SOURCE_HEAD, "source head changed")
    require(result["certification_anchor"] == CERTIFICATION_ANCHOR, "certification anchor changed")
    require(result["evidence_head"] == EVIDENCE_HEAD, "evidence head changed")
    require(result["state_output_checksum"] == frozen.EXPECTED_STATE, "state checksum changed")
    require(result["audit_checksum"] == frozen.EXPECTED_AUDIT, "audit checksum changed")
    require(result["resilience_checksum"] == frozen.EXPECTED_RESILIENCE, "resilience checksum changed")
    require(result["line_coverage_percent"] == 98.07, "line coverage changed")
    require(result["branch_coverage_percent"] == 96.88, "branch coverage changed")
    require(result["mutation_score_percent"] == 82.13, "mutation score changed")
    require(result["validation_run"] == SOURCE_PROOF[0], "source validation run changed")
    require(result["validation_artifact"] == SOURCE_PROOF[1], "source artifact changed")
    require(result["validation_artifact_digest"] == SOURCE_PROOF[2], "source digest changed")
    require(result["mutation_run"] == MUTATION_PROOF[0], "mutation run changed")
    require(result["mutation_artifact"] == MUTATION_PROOF[1], "mutation artifact changed")
    require(result["mutation_artifact_digest"] == MUTATION_PROOF[2], "mutation digest changed")
    require(result["lot44_status"] == "PLANNED_LOCKED", "frozen validator unlocked Lot 44")

    mutation = load_json(MUTATION)
    require(mutation["killed_mutants"] == 2357, "killed-mutant count changed")
    require(mutation["survived_mutants"] == 513, "survived-mutant count changed")
    require(mutation["total_mutants"] == 2870, "total-mutant count changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout present")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutation present")
    return result


def _verify_docs() -> None:
    audit = AUDIT_DOC.read_text(encoding="utf-8")
    matrix = MATRIX_DOC.read_text(encoding="utf-8")
    for text in (audit, matrix):
        require("GO_LOT43_POST_MERGE" in text, "post-merge GO missing from documentation")
        require(IMPLEMENTATION_MERGE in text, "implementation merge missing from documentation")
        require(FINAL_PR_HEAD in text, "final PR head missing from documentation")
        require(SOURCE_HEAD in text, "source head missing from documentation")
        require("Lot 44" in text and "PLANNED_LOCKED" in text, "Lot 44 lock missing")
        require("23/23" in text, "exact pre-merge workflow matrix missing")
        require("owner override" in text.lower(), "owner-override provenance missing")


def _verify_lot44_absent() -> None:
    for relative in LOT44_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"Lot 44 must remain absent: {relative}")


def validate() -> dict[str, object]:
    _verify_release()
    _verify_lifecycle()
    frozen_result = _verify_frozen()
    _verify_docs()
    _verify_lot44_absent()
    result: dict[str, object] = {
        "schema_version": "lot43-post-merge-audit-v1",
        "status": "PASS",
        "verdict": "GO_LOT43_POST_MERGE",
        "release": RELEASE,
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
        "certified_content_head": CERTIFIED_CONTENT_HEAD,
        "final_pr_head": FINAL_PR_HEAD,
        "implementation_merge": IMPLEMENTATION_MERGE,
        "implementation_pr": IMPLEMENTATION_PR,
        "pre_merge_workflows": "23/23 SUCCESS",
        "source_validation_run": SOURCE_PROOF[0],
        "source_validation_artifact": SOURCE_PROOF[1],
        "source_validation_digest": SOURCE_PROOF[2],
        "mutation_run": MUTATION_PROOF[0],
        "mutation_artifact": MUTATION_PROOF[1],
        "mutation_digest": MUTATION_PROOF[2],
        "frozen_run": FROZEN_PROOF[0],
        "frozen_artifact": FROZEN_PROOF[1],
        "frozen_digest": FROZEN_PROOF[2],
        "frozen_state_checksum": frozen_result["state_output_checksum"],
        "frozen_audit_checksum": frozen_result["audit_checksum"],
        "resilience_checksum": frozen_result["resilience_checksum"],
        "line_coverage_percent": frozen_result["line_coverage_percent"],
        "branch_coverage_percent": frozen_result["branch_coverage_percent"],
        "mutation_score_percent": frozen_result["mutation_score_percent"],
        "owner_override_recorded": True,
        "lot44_status": "PLANNED_LOCKED",
        "lot44_implementation_started": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["post_merge_audit_checksum"] = hashlib.sha256(encoded).hexdigest()
    return result


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
