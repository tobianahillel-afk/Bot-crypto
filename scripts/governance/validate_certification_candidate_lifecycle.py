#!/usr/bin/env python3
"""Validate ENG-06.1 certification-candidate lifecycle policy and snapshots."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "certification_candidate_lifecycle_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
CANDIDATE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class CandidateLifecycleError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateLifecycleError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CandidateLifecycleError(f"{path} must contain an object")
    return value


def validate_policy(
    policy: dict[str, Any],
    evidence_policy: dict[str, Any],
    assurance_policy: dict[str, Any],
) -> None:
    if policy.get("schema_version") != 1:
        raise CandidateLifecycleError("unsupported lifecycle policy version")
    if policy.get("policy_kind") != "certification_candidate_lifecycle_v1":
        raise CandidateLifecycleError("invalid lifecycle policy kind")
    if policy.get("semantics") != "EXPLICIT_FAIL_CLOSED_CERTIFICATION_CANDIDATE_STATE_MACHINE":
        raise CandidateLifecycleError("lifecycle semantics drift")

    states = policy.get("states")
    mutable = policy.get("mutable_states")
    terminal = policy.get("terminal_states")
    if not isinstance(states, list) or len(states) != len(set(states)):
        raise CandidateLifecycleError("states must be a unique list")
    state_set = set(states)
    if policy.get("initial_state") != "DRAFT" or "DRAFT" not in state_set:
        raise CandidateLifecycleError("DRAFT must remain the initial state")
    if not isinstance(mutable, list) or not isinstance(terminal, list):
        raise CandidateLifecycleError("mutable/terminal state sets missing")
    if set(mutable) & set(terminal) or set(mutable) | set(terminal) != state_set:
        raise CandidateLifecycleError("mutable and terminal states must partition all states")
    if set(terminal) != {"CERTIFIED", "REJECTED", "WITHDRAWN"}:
        raise CandidateLifecycleError("terminal-state set drift")

    transitions = policy.get("allowed_transitions")
    if not isinstance(transitions, dict) or set(transitions) != state_set:
        raise CandidateLifecycleError("transition map must cover every state")
    for source, targets in transitions.items():
        if not isinstance(targets, list) or len(targets) != len(set(targets)):
            raise CandidateLifecycleError(f"invalid transitions from {source}")
        if any(target not in state_set for target in targets):
            raise CandidateLifecycleError(f"unknown transition target from {source}")
        if source in terminal and targets:
            raise CandidateLifecycleError(f"terminal state {source} cannot have outgoing transitions")

    evidence_classes = evidence_policy.get("evidence_classes")
    if not isinstance(evidence_classes, dict) or not evidence_classes:
        raise CandidateLifecycleError("agent evidence classes unavailable")
    catalog = policy.get("prerequisite_catalog")
    if not isinstance(catalog, dict) or not catalog:
        raise CandidateLifecycleError("prerequisite catalog missing")
    for name, rule in catalog.items():
        if not isinstance(rule, dict) or set(rule) != {"allowed_evidence_classes"}:
            raise CandidateLifecycleError(f"invalid prerequisite rule: {name}")
        allowed = rule["allowed_evidence_classes"]
        if not isinstance(allowed, list) or not allowed or len(allowed) != len(set(allowed)):
            raise CandidateLifecycleError(f"invalid evidence-class list for {name}")
        if any(item not in evidence_classes for item in allowed):
            raise CandidateLifecycleError(f"prerequisite {name} references unknown evidence class")

    required = policy.get("required_prerequisites_by_state")
    if not isinstance(required, dict) or set(required) != state_set:
        raise CandidateLifecycleError("state prerequisite map must cover every state")
    for state, names in required.items():
        if not isinstance(names, list) or len(names) != len(set(names)):
            raise CandidateLifecycleError(f"invalid prerequisites for {state}")
        if any(name not in catalog for name in names):
            raise CandidateLifecycleError(f"state {state} references unknown prerequisite")

    ready_required = set(required["CERTIFICATION_READY"])
    if not {
        "CANDIDATE_REF_BOUND",
        "VALIDATION_PASS_BOUND",
        "ASSURANCE_SELECTION_BOUND",
        "NO_OPEN_BLOCKER",
    } <= ready_required:
        raise CandidateLifecycleError("CERTIFICATION_READY prerequisite floor missing")
    certified_required = set(required["CERTIFIED"])
    if not {
        "EXACT_HEAD_CERTIFICATION_EVIDENCE",
        "CERTIFICATION_VERDICT_PASS",
    } <= certified_required:
        raise CandidateLifecycleError("CERTIFIED exact-head/verdict prerequisite floor missing")

    fresh = policy.get("evidence_fresh_required_states")
    if set(fresh or []) != {"CERTIFICATION_READY", "CERTIFIED"}:
        raise CandidateLifecycleError("fresh-evidence state floor drift")
    if policy.get("stale_state") != "STALE":
        raise CandidateLifecycleError("STALE state drift")
    if policy.get("evidence_policy_source") != "engineering/AGENT_CAPABILITIES.json":
        raise CandidateLifecycleError("evidence-policy source drift")
    if policy.get("assurance_policy_source") != "config/governance/validation_t3_t4_policy_v1.json":
        raise CandidateLifecycleError("assurance-policy source drift")

    for key in ("t3_requirement_ids", "t4_requirement_ids", "risk_to_t3", "risk_to_t4"):
        if key not in assurance_policy:
            raise CandidateLifecycleError(f"assurance policy missing {key}")


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or len(value) != len(set(value)):
        raise CandidateLifecycleError(f"{name} must be a unique list")
    if any(not isinstance(item, str) or not item for item in value):
        raise CandidateLifecycleError(f"{name} contains invalid id")
    return value


def validate_candidate(
    candidate: dict[str, Any],
    policy: dict[str, Any],
    evidence_policy: dict[str, Any],
    assurance_policy: dict[str, Any],
) -> None:
    validate_policy(policy, evidence_policy, assurance_policy)
    expected_keys = {
        "candidate_id",
        "head_sha",
        "risk_class",
        "state",
        "evidence_fresh",
        "evidence_bindings",
        "required_t3",
        "satisfied_t3",
        "required_t4",
        "satisfied_t4",
    }
    if set(candidate) != expected_keys:
        raise CandidateLifecycleError(
            f"candidate shape mismatch: missing={sorted(expected_keys-set(candidate))} "
            f"extra={sorted(set(candidate)-expected_keys)}"
        )

    candidate_id = candidate["candidate_id"]
    head_sha = candidate["head_sha"]
    risk_class = candidate["risk_class"]
    state = candidate["state"]
    if not isinstance(candidate_id, str) or CANDIDATE_ID.fullmatch(candidate_id) is None:
        raise CandidateLifecycleError("invalid candidate_id")
    if not isinstance(head_sha, str) or SHA40.fullmatch(head_sha) is None:
        raise CandidateLifecycleError("candidate head_sha must be lowercase SHA-40")
    if risk_class not in assurance_policy.get("risk_order", []):
        raise CandidateLifecycleError(f"unknown risk class: {risk_class}")
    if state not in policy["states"]:
        raise CandidateLifecycleError(f"unknown lifecycle state: {state}")
    if not isinstance(candidate["evidence_fresh"], bool):
        raise CandidateLifecycleError("evidence_fresh must be boolean")

    bindings = candidate["evidence_bindings"]
    if not isinstance(bindings, dict):
        raise CandidateLifecycleError("evidence_bindings must be an object")
    unknown_bindings = sorted(set(bindings) - set(policy["prerequisite_catalog"]))
    if unknown_bindings:
        raise CandidateLifecycleError(f"unknown prerequisite bindings: {unknown_bindings}")
    for name, evidence_class in bindings.items():
        if not isinstance(evidence_class, str):
            raise CandidateLifecycleError(f"evidence class for {name} must be a string")
        allowed = policy["prerequisite_catalog"][name]["allowed_evidence_classes"]
        if evidence_class not in allowed:
            raise CandidateLifecycleError(
                f"evidence class {evidence_class} cannot satisfy {name}"
            )

    missing_prerequisites = [
        name
        for name in policy["required_prerequisites_by_state"][state]
        if name not in bindings
    ]
    if missing_prerequisites:
        raise CandidateLifecycleError(
            f"state {state} missing prerequisites: {missing_prerequisites}"
        )
    if state in policy["evidence_fresh_required_states"] and not candidate["evidence_fresh"]:
        raise CandidateLifecycleError(f"state {state} requires fresh evidence")
    if state == policy["stale_state"] and candidate["evidence_fresh"]:
        raise CandidateLifecycleError("STALE candidate must have evidence_fresh=false")

    required_t3 = _string_list(candidate["required_t3"], "required_t3")
    satisfied_t3 = _string_list(candidate["satisfied_t3"], "satisfied_t3")
    required_t4 = _string_list(candidate["required_t4"], "required_t4")
    satisfied_t4 = _string_list(candidate["satisfied_t4"], "satisfied_t4")
    t3_ids = set(assurance_policy["t3_requirement_ids"])
    t4_ids = set(assurance_policy["t4_requirement_ids"])
    if not set(required_t3) <= t3_ids or not set(satisfied_t3) <= t3_ids:
        raise CandidateLifecycleError("candidate references unknown T3 requirement")
    if not set(required_t4) <= t4_ids or not set(satisfied_t4) <= t4_ids:
        raise CandidateLifecycleError("candidate references unknown T4 requirement")
    if not set(satisfied_t3) <= set(required_t3):
        raise CandidateLifecycleError("satisfied_t3 must be a subset of required_t3")
    if not set(satisfied_t4) <= set(required_t4):
        raise CandidateLifecycleError("satisfied_t4 must be a subset of required_t4")

    floor_t3 = set(assurance_policy["risk_to_t3"][risk_class])
    floor_t4 = set(assurance_policy["risk_to_t4"][risk_class])
    if not floor_t3 <= set(required_t3):
        raise CandidateLifecycleError(f"{risk_class} candidate missing T3 risk floor")
    if not floor_t4 <= set(required_t4):
        raise CandidateLifecycleError(f"{risk_class} candidate missing T4 risk floor")

    missing_t3 = set(required_t3) - set(satisfied_t3)
    missing_t4 = set(required_t4) - set(satisfied_t4)
    if state == "ASSURANCE_REQUIRED" and not missing_t3:
        raise CandidateLifecycleError("ASSURANCE_REQUIRED requires at least one unsatisfied T3 item")
    if state in {"CERTIFICATION_READY", "CERTIFIED"} and missing_t3:
        raise CandidateLifecycleError(f"state {state} cannot retain unsatisfied T3 items")
    if state == "CERTIFIED" and missing_t4:
        raise CandidateLifecycleError("CERTIFIED cannot retain unsatisfied T4 items")


def validate_transition(
    before: dict[str, Any],
    after: dict[str, Any],
    policy: dict[str, Any],
    evidence_policy: dict[str, Any],
    assurance_policy: dict[str, Any],
) -> None:
    validate_candidate(before, policy, evidence_policy, assurance_policy)
    validate_candidate(after, policy, evidence_policy, assurance_policy)

    for field in ("candidate_id", "head_sha", "risk_class"):
        if before[field] != after[field]:
            raise CandidateLifecycleError(
                f"candidate identity field {field} is immutable; create a new candidate"
            )
    allowed = policy["allowed_transitions"][before["state"]]
    if after["state"] not in allowed:
        raise CandidateLifecycleError(
            f"transition forbidden: {before['state']} -> {after['state']}"
        )
    if before["evidence_fresh"] and not after["evidence_fresh"]:
        if after["state"] not in {"STALE", "REJECTED", "WITHDRAWN"}:
            raise CandidateLifecycleError(
                "fresh-to-stale evidence change must enter STALE or a terminal rejection/withdrawal"
            )


def _load_policies() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    lifecycle = _json(POLICY_PATH)
    evidence = _json(ROOT / lifecycle["evidence_policy_source"])
    assurance = _json(ROOT / lifecycle["assurance_policy_source"])
    return lifecycle, evidence, assurance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    args = parser.parse_args()
    try:
        lifecycle, evidence, assurance = _load_policies()
        validate_policy(lifecycle, evidence, assurance)
        if args.candidate is not None:
            validate_candidate(_json(args.candidate), lifecycle, evidence, assurance)
        if (args.before is None) != (args.after is None):
            raise CandidateLifecycleError("--before and --after must be supplied together")
        if args.before is not None:
            validate_transition(
                _json(args.before),
                _json(args.after),
                lifecycle,
                evidence,
                assurance,
            )
    except CandidateLifecycleError as exc:
        print(f"CERTIFICATION_CANDIDATE_LIFECYCLE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("CERTIFICATION_CANDIDATE_LIFECYCLE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
