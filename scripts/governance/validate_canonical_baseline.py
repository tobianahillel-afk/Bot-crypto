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
    current_business_status = state_business.get("business_development")
    if business.get("development_status") != "PAUSED":
        raise CanonicalBaselineError(
            "ENG-00 baseline must preserve historical PAUSED business development status"
        )
    if current_business_status not in {"PAUSED", "ACTIVE"}:
        raise CanonicalBaselineError("current business development lifecycle is unsupported")
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
    expected_identity = {
        "lot": state_candidate.get("lot"),
        "pr": state_candidate.get("pull_request"),
        "branch": state_candidate.get("branch"),
        "observed_head": state_candidate.get("observed_head_sha"),
    }
    for key, expected in expected_identity.items():
        if candidate.get(key) != expected:
            raise CanonicalBaselineError(f"Lot45 candidate identity mismatch for {key}")
    if candidate.get("status") != "SUSPENDED_CANDIDATE":
        raise CanonicalBaselineError(
            "ENG-00 baseline must preserve historical SUSPENDED_CANDIDATE status"
        )
    if candidate.get("merged") is not False or candidate.get("state") != "OPEN":
        raise CanonicalBaselineError("Lot45 baseline candidate must remain open and unmerged")

    if state_business.get("next_lot") != {"lot": 46, "status": "LOCKED"}:
        raise CanonicalBaselineError("current lifecycle must preserve the Lot46 lock")

    if current_business_status == "PAUSED":
        if state_candidate.get("status") != "SUSPENDED_CANDIDATE":
            raise CanonicalBaselineError(
                "PAUSED lifecycle requires SUSPENDED_CANDIDATE current status"
            )
    else:
        if state_candidate.get("status") != "ACTIVE_CANDIDATE":
            raise CanonicalBaselineError(
                "ACTIVE lifecycle requires ACTIVE_CANDIDATE current status"
            )
        activation = _load("engineering/BUSINESS_DEVELOPMENT_UNLOCK_ACTIVATION.json")
        if activation.get("schema_version") != 1:
            raise CanonicalBaselineError("business activation evidence schema drift")
        if (
            activation.get("evidence_kind")
            != "business_development_unlock_activation_v1"
            or activation.get("status") != "ACTIVATED"
            or activation.get("explicit_human_action") != "BUSINESS_DEVELOPMENT_UNLOCK"
        ):
            raise CanonicalBaselineError("ACTIVE lifecycle lacks explicit activation evidence")
        if (
            activation.get("candidate_mutated") is not False
            or activation.get("candidate_merged") is not False
            or activation.get("lot46_status") != "LOCKED"
        ):
            raise CanonicalBaselineError(
                "activation evidence violates candidate immutability or Lot46 lock"
            )
        transition = activation.get("authority_transition", {})
        if (
            transition.get("business") != "PAUSED_TO_ACTIVE"
            or transition.get("candidate")
            != "SUSPENDED_CANDIDATE_TO_ACTIVE_CANDIDATE"
        ):
            raise CanonicalBaselineError("business activation transition drift")
        live = activation.get("live_reverification", {})
        activation_identity = {
            "lot": 45,
            "pr": live.get("lot45_pr"),
            "branch": candidate.get("branch"),
            "observed_head": live.get("lot45_head_sha"),
        }
        if activation_identity != {
            "lot": candidate.get("lot"),
            "pr": candidate.get("pr"),
            "branch": candidate.get("branch"),
            "observed_head": candidate.get("observed_head"),
        }:
            raise CanonicalBaselineError(
                "activation evidence disagrees with immutable Lot45 candidate identity"
            )
        if live.get("lot45_state") != "open" or live.get("lot45_merged") is not False:
            raise CanonicalBaselineError(
                "activation evidence must preserve open unmerged Lot45 candidate"
            )
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
        manifest_path = engine.get("active_manifest")
        if not isinstance(manifest_path, str):
            raise CanonicalBaselineError("active ENG-01 manifest path is missing")
        manifest = _load(manifest_path)
        first_task = target.get("first_task")
        task_status = {
            task.get("id"): task.get("status")
            for task in manifest.get("tasks", [])
            if isinstance(task, dict)
        }.get(first_task)
        if task_status not in {"IN_PROGRESS", "DONE"}:
            raise CanonicalBaselineError("ENG-01 entry task has not been consumed")
    else:
        completed = engine.get("completed", [])
        if "ENG-01" not in completed:
            raise CanonicalBaselineError("ENG-01 handoff target was neither activated nor completed")
    if target.get("first_task") != "ENG-01.1":
        raise CanonicalBaselineError("ENG-01 must start at ENG-01.1")


def _expect_baseline_error(fn: Any, label: str) -> None:
    try:
        fn()
    except CanonicalBaselineError:
        return
    raise AssertionError(f"canonical baseline negative scenario unexpectedly passed: {label}")


def _self_check_lifecycle() -> None:
    business = {
        "development_status": "PAUSED",
        "candidate": {
            "lot": 45,
            "pr": 66,
            "branch": "agent/lot45-order-flow-delta-cvd-engine-v2",
            "observed_head": "e" * 40,
            "state": "OPEN",
            "merged": False,
            "status": "SUSPENDED_CANDIDATE",
        },
        "next_lot": {"lot": 46, "status": "LOCKED"},
    }
    paused = {
        "business_development": "PAUSED",
        "active_candidate": {
            "lot": 45,
            "pull_request": 66,
            "branch": business["candidate"]["branch"],
            "observed_head_sha": "e" * 40,
            "status": "SUSPENDED_CANDIDATE",
        },
        "next_lot": {"lot": 46, "status": "LOCKED"},
    }
    active = json.loads(json.dumps(paused))
    active["business_development"] = "ACTIVE"
    active["active_candidate"]["status"] = "ACTIVE_CANDIDATE"

    def probe(
        baseline_business: dict[str, Any],
        current_business: dict[str, Any],
        activation: dict[str, Any] | None,
    ) -> None:
        if baseline_business.get("development_status") != "PAUSED":
            raise CanonicalBaselineError("baseline PAUSED invariant")
        candidate = baseline_business["candidate"]
        current = current_business["active_candidate"]
        for left, right in (
            (candidate["lot"], current["lot"]),
            (candidate["pr"], current["pull_request"]),
            (candidate["branch"], current["branch"]),
            (candidate["observed_head"], current["observed_head_sha"]),
        ):
            if left != right:
                raise CanonicalBaselineError("candidate identity drift")
        if current_business["business_development"] == "ACTIVE":
            if activation is None:
                raise CanonicalBaselineError("missing activation")
            if activation.get("candidate_mutated") is not False:
                raise CanonicalBaselineError("candidate mutation")
            if activation.get("candidate_merged") is not False:
                raise CanonicalBaselineError("candidate merge")
            if activation.get("lot45_head_sha") != candidate["observed_head"]:
                raise CanonicalBaselineError("activation head drift")

    probe(business, paused, None)
    activation = {
        "candidate_mutated": False,
        "candidate_merged": False,
        "lot45_head_sha": "e" * 40,
    }
    probe(business, active, activation)

    changed_baseline = json.loads(json.dumps(business))
    changed_baseline["development_status"] = "ACTIVE"
    _expect_baseline_error(
        lambda: probe(changed_baseline, active, activation),
        "rewritten historical lifecycle",
    )
    _expect_baseline_error(lambda: probe(business, active, None), "missing activation")
    wrong_head = json.loads(json.dumps(active))
    wrong_head["active_candidate"]["observed_head_sha"] = "f" * 40
    _expect_baseline_error(
        lambda: probe(business, wrong_head, activation),
        "candidate head drift",
    )
    mutated = dict(activation)
    mutated["candidate_mutated"] = True
    _expect_baseline_error(
        lambda: probe(business, active, mutated),
        "candidate mutation",
    )
    print("CANONICAL_BASELINE_LIFECYCLE_SELFTEST_PASS probes=6")


def main() -> int:
    try:
        _self_check_lifecycle()
        validate()
    except CanonicalBaselineError as exc:
        print(f"CANONICAL_BASELINE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("CANONICAL_BASELINE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
