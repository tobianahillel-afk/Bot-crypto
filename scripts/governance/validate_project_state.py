#!/usr/bin/env python3
"""Validate permanent project_state.json against ENG-00 baseline and migration bridge."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


class ProjectStateError(ValueError):
    pass


def _load(path: str) -> dict[str, Any]:
    target = ROOT / path
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectStateError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectStateError(f"{path} must contain an object")
    return value


def validate() -> None:
    state = _load("config/governance/project_state.json")
    bridge = _load("engineering/STATE.json")
    baseline = _load("engineering/CANONICAL_BASELINE.json")

    if state.get("schema_version") != 1 or state.get("state_kind") != "project_state_v1":
        raise ProjectStateError("permanent state schema identity drift")
    if state.get("project") != baseline.get("project"):
        raise ProjectStateError("permanent state project identity disagrees with baseline")

    business = state.get("business_track")
    if business != baseline.get("business"):
        raise ProjectStateError("BUSINESS track must match certified ENG-00 baseline")

    engineering = state.get("engineering_track")
    bridge_engine = bridge.get("engineering_engine")
    if not isinstance(engineering, dict) or not isinstance(bridge_engine, dict):
        raise ProjectStateError("ENGINEERING track missing")
    for permanent_key, bridge_key in (
        ("phase","phase"),
        ("completed","completed"),
        ("active_lot","active_lot"),
        ("active_task","active_task"),
        ("next_lot","next_lot"),
        ("active_manifest","active_manifest"),
        ("blockers","blockers"),
    ):
        if engineering.get(permanent_key) != bridge_engine.get(bridge_key):
            raise ProjectStateError(f"ENGINEERING migration parity mismatch: {permanent_key}")
    if engineering.get("branch") != bridge.get("bootstrap_engine", {}).get("branch"):
        raise ProjectStateError("ENGINEERING branch disagrees with migration bridge")

    audit = state.get("audit_track")
    if not isinstance(audit, dict):
        raise ProjectStateError("AUDIT track missing")
    if audit.get("phase") != "NOT_STARTED":
        raise ProjectStateError("AUDIT track must remain NOT_STARTED before ENG-07")
    for key in ("active_batch","active_task","next_batch","active_manifest"):
        if audit.get(key) is not None:
            raise ProjectStateError(f"AUDIT {key} must be null before ENG-07")
    if audit.get("completed") != [] or audit.get("blockers") != []:
        raise ProjectStateError("AUDIT track must start empty")

    if state.get("safety") != baseline.get("safety"):
        raise ProjectStateError("safety state disagrees with canonical baseline")
    if state.get("cost_policy") != bridge.get("mandatory_cost_policy"):
        raise ProjectStateError("cost policy disagrees with migration bridge")

    authority = state.get("authority")
    if not isinstance(authority, dict) or authority.get("current_state") != "config/governance/project_state.json":
        raise ProjectStateError("permanent state must self-identify as current_state target")
    for path in authority.values():
        if path is not None and (not isinstance(path, str) or not (ROOT / path).exists()):
            raise ProjectStateError(f"authority path missing: {path!r}")

    observations = state.get("external_observations", {})
    baseline_obs = baseline.get("external_git_observations", {})
    if observations.get("main") != baseline_obs.get("main"):
        raise ProjectStateError("main Git observation disagrees with baseline")
    if observations.get("rulesets_count") != baseline_obs.get("rulesets_count"):
        raise ProjectStateError("rulesets observation disagrees with baseline")
    candidate_obs = observations.get("business_candidate", {})
    baseline_candidate_obs = baseline_obs.get("lot45_candidate", {})
    if candidate_obs != baseline_candidate_obs:
        raise ProjectStateError("candidate Git observation disagrees with baseline")

    if state.get("findings") != bridge.get("known_findings"):
        raise ProjectStateError("findings must preserve migration bridge findings")
    if set(state.get("stop_conditions", [])) != set(bridge.get("stop_conditions", [])):
        raise ProjectStateError("stop conditions drift during migration")

    freshness = state.get("freshness_policy", {})
    if freshness.get("verify_external_git_on_every_agent_resume") is not True:
        raise ProjectStateError("fresh Git verification must remain mandatory")
    if freshness.get("auto_heal_state_from_external_git") is not False:
        raise ProjectStateError("external drift must not auto-heal")
    if freshness.get("mismatch_consequence") != "STATE_DRIFT":
        raise ProjectStateError("external mismatch consequence must be STATE_DRIFT")

    if business.get("development_status") != "PAUSED":
        raise ProjectStateError("business development must remain PAUSED")
    if business.get("next_lot") != {"lot": 46, "status": "LOCKED"}:
        raise ProjectStateError("Lot46 must remain locked")
    candidate = business.get("candidate", {})
    if candidate.get("merged") is not False:
        raise ProjectStateError("candidate PR cannot be represented as merged truth")
    safety = state.get("safety", {})
    if safety.get("trade_allowed") is not False or safety.get("execution_allowed") is not False:
        raise ProjectStateError("permanent state must remain fail-closed")


def main() -> int:
    try:
        validate()
    except ProjectStateError as exc:
        print(f"PROJECT_STATE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("PROJECT_STATE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
