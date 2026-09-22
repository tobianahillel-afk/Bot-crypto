#!/usr/bin/env python3
"""Validate ENG-00 permanent project-state design against current canonical state."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "engineering" / "PERMANENT_STATE_DESIGN.json"
STATE = ROOT / "engineering" / "STATE.json"


class PermanentStateDesignError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermanentStateDesignError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PermanentStateDesignError(f"{path} must contain an object")
    return value


def validate(design: dict[str, Any], state: dict[str, Any]) -> None:
    if design.get("schema_version") != 1:
        raise PermanentStateDesignError("unsupported design schema")
    if design.get("design_kind") != "permanent_project_state_design":
        raise PermanentStateDesignError("invalid design kind")
    if design.get("project") != state.get("project"):
        raise PermanentStateDesignError("project identity disagrees with canonical state")

    tracks = design.get("tracks")
    if not isinstance(tracks, dict) or set(tracks) != {"business", "engineering", "audit"}:
        raise PermanentStateDesignError("business/engineering/audit tracks are required")

    business = tracks["business"]
    current_business = state.get("business_track", {})
    if business.get("development_status") != current_business.get("business_development"):
        raise PermanentStateDesignError("business development status mismatch")
    if business.get("merged_certified_baseline", {}).get("lot") != 44:
        raise PermanentStateDesignError("Lot44 must remain the merged certified baseline")
    if business.get("merged_certified_baseline", {}).get("version") != "0.44.0":
        raise PermanentStateDesignError("certified baseline version must be 0.44.0")
    if business.get("merged_entry_gate", {}).get("target_lot") != 45:
        raise PermanentStateDesignError("Lot45 merged entry gate missing")
    if business.get("merged_entry_gate", {}).get("merge") != state.get(
        "observed_git_baseline", {}
    ).get("main_sha"):
        raise PermanentStateDesignError("Lot45 gate merge must equal observed main baseline")

    candidate = business.get("candidate", {})
    state_candidate = current_business.get("active_candidate", {})
    expected_candidate = {
        "lot": state_candidate.get("lot"),
        "pr": state_candidate.get("pull_request"),
        "branch": state_candidate.get("branch"),
        "observed_head": state_candidate.get("observed_head_sha"),
        "status": state_candidate.get("status"),
    }
    for key, value in expected_candidate.items():
        if candidate.get(key) != value:
            raise PermanentStateDesignError(f"candidate mismatch for {key}")
    if candidate.get("merged") is not False:
        raise PermanentStateDesignError("candidate must remain explicitly unmerged")

    if business.get("next_lot") != {"lot": 46, "status": "LOCKED"}:
        raise PermanentStateDesignError("Lot46 lock missing")

    safety = design.get("safety", {})
    for key in ("trade_allowed", "execution_allowed"):
        if safety.get(key) is not False:
            raise PermanentStateDesignError(f"{key} must remain false")
    if safety.get("live_execution") != "DISABLED":
        raise PermanentStateDesignError("live execution must remain disabled")

    freshness = design.get("freshness_policy", {})
    if freshness.get("verify_external_git_on_every_agent_resume") is not True:
        raise PermanentStateDesignError("fresh Git verification must be mandatory")
    if freshness.get("auto_heal_state_from_external_git") is not False:
        raise PermanentStateDesignError("unexpected Git drift must never auto-heal")
    if freshness.get("mismatch_consequence") != "STATE_DRIFT":
        raise PermanentStateDesignError("Git mismatch consequence must be STATE_DRIFT")

    promotion = design.get("promotion_policy", {})
    for key in (
        "business_progress_requires_explicit_unlock",
        "candidate_pr_is_never_merged_truth",
        "gate_is_not_implementation_certification",
        "lot46_requires_lot45_certification_and_explicit_gate",
        "unresolved_high_security_findings_block_business_unlock",
    ):
        if promotion.get(key) is not True:
            raise PermanentStateDesignError(f"promotion policy {key} must be true")


def main() -> int:
    try:
        validate(_load(DESIGN), _load(STATE))
    except PermanentStateDesignError as exc:
        print(f"PERMANENT_STATE_DESIGN_INVALID: {exc}", file=sys.stderr)
        return 1
    print("PERMANENT_STATE_DESIGN_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
