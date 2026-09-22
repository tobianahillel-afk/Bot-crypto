#!/usr/bin/env python3
"""Validate the ENG-00 canonical baseline against all ENG-00 authority artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


class CanonicalBaselineError(ValueError):
    pass


def _load(path: str) -> dict[str, Any]:
    target = ROOT / path
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalBaselineError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CanonicalBaselineError(f"{path} must contain an object")
    return value


def validate() -> None:
    baseline = _load("engineering/CANONICAL_BASELINE.json")
    state = _load("engineering/STATE.json")
    design = _load("engineering/PERMANENT_STATE_DESIGN.json")
    truth = _load("engineering/REPOSITORY_TRUTH_REGISTRY.json")
    protection = _load("engineering/HISTORICAL_EVIDENCE_PROTECTION.json")

    if baseline.get("schema_version") != 1:
        raise CanonicalBaselineError("unsupported baseline schema_version")
    if baseline.get("baseline_kind") != "eng00_canonical_baseline":
        raise CanonicalBaselineError("invalid baseline_kind")
    if baseline.get("project") != state.get("project"):
        raise CanonicalBaselineError("project identity disagrees with canonical state")
    if baseline.get("project") != design.get("project"):
        raise CanonicalBaselineError("project identity disagrees with permanent-state design")

    business = baseline.get("business", {})
    state_business = state.get("business_track", {})
    if business.get("development_status") != state_business.get("business_development"):
        raise CanonicalBaselineError("business development status mismatch")
    if business.get("merged_certified_baseline", {}).get("lot") != 44:
        raise CanonicalBaselineError("Lot44 must be the certified implementation baseline")
    if business.get("merged_certified_baseline", {}).get("version") != "0.44.0":
        raise CanonicalBaselineError("certified baseline version must be 0.44.0")
    if business.get("merged_certified_baseline", {}).get("verdict") != "GO_LOT44_POST_MERGE":
        raise CanonicalBaselineError("Lot44 post-merge verdict drift")
    if business.get("merged_entry_gate", {}).get("target_lot") != 45:
        raise CanonicalBaselineError("Lot45 entry gate missing")
    if business.get("merged_entry_gate", {}).get("verdict") != "GO_LOT45_IMPLEMENTATION_ENTRY":
        raise CanonicalBaselineError("Lot45 entry gate verdict drift")

    candidate = business.get("candidate", {})
    state_candidate = state_business.get("active_candidate", {})
    expected_candidate = {
        "lot": state_candidate.get("lot"),
        "pr": state_candidate.get("pull_request"),
        "branch": state_candidate.get("branch"),
        "observed_head": state_candidate.get("observed_head_sha"),
        "status": state_candidate.get("status"),
    }
    for key, expected in expected_candidate.items():
        if candidate.get(key) != expected:
            raise CanonicalBaselineError(f"Lot45 candidate mismatch for {key}")
    if candidate.get("merged") is not False or candidate.get("state") != "OPEN":
        raise CanonicalBaselineError("Lot45 candidate must remain explicitly open and unmerged")
    if business.get("next_lot") != {"lot": 46, "status": "LOCKED"}:
        raise CanonicalBaselineError("Lot46 lock missing")

    if baseline.get("safety") != state.get("safety"):
        raise CanonicalBaselineError("baseline safety does not match canonical state")

    views = set(baseline.get("reconciled_status_views", []))
    truth_resolved = set(truth.get("resolved_drift_targets", []))
    if views != truth_resolved:
        raise CanonicalBaselineError("reconciled status views disagree with truth registry")

    authority = baseline.get("authority", {})
    for path in authority.values():
        if not isinstance(path, str) or not (ROOT / path).exists():
            raise CanonicalBaselineError(f"authority path missing: {path!r}")

    design_business = design.get("tracks", {}).get("business", {})
    if design_business.get("merged_certified_baseline", {}).get("lot") != 44:
        raise CanonicalBaselineError("permanent-state design baseline drift")
    if design_business.get("merged_entry_gate", {}).get("merge") != business.get(
        "merged_entry_gate", {}
    ).get("merge"):
        raise CanonicalBaselineError("Lot45 gate merge disagrees with permanent-state design")

    anchor_ids = {item.get("id") for item in protection.get("anchors", []) if isinstance(item, dict)}
    if anchor_ids != {"LOT44_POST_MERGE_CERTIFICATION", "LOT45_ENTRY_GATE"}:
        raise CanonicalBaselineError("historical evidence anchors are incomplete")

    findings = baseline.get("unresolved_findings")
    state_findings = state.get("known_findings")
    if not isinstance(findings, list) or not findings:
        raise CanonicalBaselineError("baseline must retain unresolved findings")
    if not isinstance(state_findings, list) or not state_findings:
        raise CanonicalBaselineError("canonical state unexpectedly lost findings")
    if findings[0].get("id") != state_findings[0].get("id"):
        raise CanonicalBaselineError("baseline finding id disagrees with canonical state")
    if findings[0].get("blocks") != "BUSINESS_DEVELOPMENT_UNLOCK":
        raise CanonicalBaselineError("main branch protection finding must block business unlock")

    target = baseline.get("handoff_target", {})
    engine = state.get("engineering_engine", {})
    target_lot = target.get("engineering_lot")
    if target_lot != "ENG-01":
        raise CanonicalBaselineError("canonical baseline must hand off to ENG-01")
    if engine.get("active_lot") == "ENG-00":
        if engine.get("next_lot") != target_lot:
            raise CanonicalBaselineError("ENG-01 handoff target disagrees with ENG-00 next_lot")
    elif engine.get("active_lot") == "ENG-01":
        if engine.get("active_task") != target.get("first_task"):
            raise CanonicalBaselineError("active ENG-01 task disagrees with baseline handoff target")
    else:
        completed = engine.get("completed", [])
        if "ENG-01" not in completed:
            raise CanonicalBaselineError("ENG-01 handoff target was neither activated nor completed")
    if target.get("first_task") != "ENG-01.1":
        raise CanonicalBaselineError("ENG-01 must start at ENG-01.1")


def main() -> int:
    try:
        validate()
    except CanonicalBaselineError as exc:
        print(f"CANONICAL_BASELINE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("CANONICAL_BASELINE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
