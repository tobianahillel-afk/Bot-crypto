#!/usr/bin/env python3
"""Validate post-remediation business-development unlock eligibility without activating authority."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/governance/business_unlock_eligibility_policy_v1.json"
EVIDENCE_PATH = ROOT / "engineering/BUSINESS_DEVELOPMENT_UNLOCK_ELIGIBILITY.json"
STATE_PATH = ROOT / "config/governance/project_state.json"
BLOCKED_DECISION_PATH = ROOT / "engineering/BUSINESS_DEVELOPMENT_UNLOCK_DECISION.json"
SECURITY_PATH = ROOT / "engineering/SECURITY_ENGINE_VERIFICATION.json"
CERT_PATH = ROOT / "engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json"


class BusinessUnlockEligibilityError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BusinessUnlockEligibilityError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BusinessUnlockEligibilityError(f"{path} must contain an object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BusinessUnlockEligibilityError(message)


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BusinessUnlockEligibilityError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rules_by_type(ruleset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rules = ruleset.get("rules")
    _require(isinstance(rules, list), "ruleset rules missing")
    result: dict[str, dict[str, Any]] = {}
    for rule in rules:
        _require(isinstance(rule, dict) and isinstance(rule.get("type"), str), "invalid ruleset rule")
        _require(rule["type"] not in result, f"duplicate ruleset rule: {rule['type']}")
        result[rule["type"]] = rule
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    _require(policy.get("schema_version") == 1, "unsupported eligibility policy version")
    _require(policy.get("policy_kind") == "business_unlock_eligibility_policy_v1", "invalid eligibility policy kind")
    _require(
        policy.get("semantics") == "LIVE_PROTECTION_ELIGIBILITY_NO_AUTHORITY_ACTIVATION",
        "eligibility policy semantics drift",
    )
    _require(policy.get("repository") == "tobianahillel-afk/Bot-crypto", "repository identity drift")
    _require(policy.get("default_branch") == "main", "default branch drift")
    required = policy.get("required_ruleset")
    _require(isinstance(required, dict), "required ruleset policy missing")
    _require(required.get("enforcement") == "active", "ruleset must require active enforcement")
    _require(required.get("ref_include") == ["refs/heads/main"], "main ruleset scope drift")
    _require(required.get("ref_exclude") == [], "ruleset exclusions drift")
    _require(
        required.get("required_rule_types")
        == ["deletion", "non_fast_forward", "pull_request", "required_status_checks"],
        "required ruleset types drift",
    )
    _require(
        required.get("required_check_contexts")
        == ["CodeQL Python security-extended", "Gitleaks pinned CLI", "quality"],
        "required check contexts drift",
    )
    _require(required.get("bypass_actors") == [], "ruleset bypass floor drift")
    _require(required.get("current_user_can_bypass") == "never", "current-user bypass floor drift")
    floor = policy.get("required_floor")
    _require(isinstance(floor, dict) and floor and all(value is True for value in floor.values()), "protection floor drift")
    _require(
        policy.get("optional_hardening_not_required_for_floor")
        == [
            "strict_required_status_checks_policy",
            "required_approving_review_count_gt_0",
            "required_review_thread_resolution",
        ],
        "optional hardening declaration drift",
    )
    activation = policy.get("activation_policy")
    _require(isinstance(activation, dict), "activation policy missing")
    for key in (
        "eligibility_is_not_activation",
        "explicit_human_unlock_transition_required",
        "lot45_merge_not_granted",
        "lot46_unlock_not_granted",
        "runtime_unlock_not_granted",
    ):
        _require(activation.get(key) is True, f"activation separation weakened: {key}")
    cost = policy.get("cost_policy")
    _require(isinstance(cost, dict) and not any(cost.values()), "eligibility path must remain zero-cost")


def validate_ruleset(ruleset: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    required = policy["required_ruleset"]
    _require(ruleset.get("name") == required["name"], "ruleset name drift")
    _require(ruleset.get("target") == required["target"], "ruleset target drift")
    _require(ruleset.get("enforcement") == required["enforcement"], "ruleset is not active")
    conditions = ruleset.get("conditions", {}).get("ref_name", {})
    _require(conditions.get("include") == required["ref_include"], "ruleset main include drift")
    _require(conditions.get("exclude") == required["ref_exclude"], "ruleset main exclude drift")
    _require(ruleset.get("bypass_actors") == required["bypass_actors"], "ruleset bypass actors present")
    _require(
        ruleset.get("current_user_can_bypass") == required["current_user_can_bypass"],
        "current user can bypass ruleset",
    )

    by_type = _rules_by_type(ruleset)
    for rule_type in required["required_rule_types"]:
        _require(rule_type in by_type, f"required ruleset rule missing: {rule_type}")

    status_params = by_type["required_status_checks"].get("parameters")
    _require(isinstance(status_params, dict), "required status-check parameters missing")
    checks = status_params.get("required_status_checks")
    _require(isinstance(checks, list), "required status-check list missing")
    contexts = sorted(
        item.get("context")
        for item in checks
        if isinstance(item, dict) and isinstance(item.get("context"), str)
    )
    _require(contexts == required["required_check_contexts"], f"required check contexts drift: {contexts}")

    pr_params = by_type["pull_request"].get("parameters")
    _require(isinstance(pr_params, dict), "pull-request parameters missing")
    hardening = {
        "strict_required_status_checks_policy": status_params.get("strict_required_status_checks_policy"),
        "required_approving_review_count": pr_params.get("required_approving_review_count"),
        "required_review_thread_resolution": pr_params.get("required_review_thread_resolution"),
    }
    _require(isinstance(hardening["strict_required_status_checks_policy"], bool), "strict-check hardening state invalid")
    _require(
        isinstance(hardening["required_approving_review_count"], int)
        and hardening["required_approving_review_count"] >= 0,
        "approval hardening state invalid",
    )
    _require(isinstance(hardening["required_review_thread_resolution"], bool), "thread-resolution hardening state invalid")

    return {
        "compliance": {
            "pull_request_required": True,
            "required_status_checks": True,
            "force_pushes_blocked": True,
            "branch_deletions_blocked": True,
            "no_bypass": True,
            "required_check_contexts_present": True,
        },
        "hardening": hardening,
    }


def validate_snapshot(
    evidence: dict[str, Any],
    policy: dict[str, Any],
    state: dict[str, Any],
    blocked: dict[str, Any],
    security: dict[str, Any],
    certification: dict[str, Any],
) -> None:
    validate_policy(policy)
    _require(evidence.get("schema_version") == 1, "unsupported eligibility evidence version")
    _require(
        evidence.get("evidence_kind") == "business_development_unlock_eligibility_v1",
        "invalid eligibility evidence kind",
    )
    _require(
        evidence.get("semantics") == "POST_REMEDIATION_ELIGIBILITY_WITHOUT_ACTIVATION",
        "eligibility evidence semantics drift",
    )
    _require(evidence.get("project") == "Crypto Quant Bot V3.1-Ops", "project identity drift")
    _require(blocked.get("verdict") == "BLOCKED_NO_UNLOCK", "historical blocked decision was rewritten")
    _require(security.get("verdict") == "PASS_ENGINEERING_SECURITY", "security engine verification missing")
    _require(
        certification.get("verdict") == "PASS_DEVELOPMENT_ENGINE_V1_EXACT_HEAD_CERTIFIED",
        "Development Engine V1 certification missing",
    )
    evaluated = evidence.get("evaluated_engine")
    _require(isinstance(evaluated, dict), "evaluated engine binding missing")
    _require(evaluated.get("version") == "V1", "evaluated engine version drift")
    _require(evaluated.get("certification_verdict") == certification.get("verdict"), "engine certification verdict binding drift")
    _require(evaluated.get("certification_candidate_id") == certification.get("candidate_id"), "engine candidate binding drift")
    _require(evaluated.get("certified_head_sha") == certification.get("qualified_head_sha"), "engine certified-head binding drift")

    historical = evidence.get("historical_checkpoint")
    _require(isinstance(historical, dict), "historical checkpoint missing")
    _require(historical.get("blocked_decision_path") == "engineering/BUSINESS_DEVELOPMENT_UNLOCK_DECISION.json", "blocked decision path drift")
    _require(historical.get("blocked_verdict") == "BLOCKED_NO_UNLOCK", "blocked verdict drift")
    _require(historical.get("baseline_finding_id") == "BOOT-FINDING-001", "baseline finding binding drift")
    _require(historical.get("baseline_preserved") is True, "baseline must remain preserved")

    finding = next((x for x in state.get("findings", []) if x.get("id") == "BOOT-FINDING-001"), None)
    _require(isinstance(finding, dict) and finding.get("observed") is True, "canonical baseline finding changed")
    business = state.get("business_track", {})
    _require(business.get("development_status") == "PAUSED", "eligibility must not activate business")
    _require(business.get("candidate", {}).get("status") == "SUSPENDED_CANDIDATE", "Lot45 status changed")
    _require(business.get("next_lot") == {"lot": 46, "status": "LOCKED"}, "Lot46 was unlocked")

    live = evidence.get("live_reverification")
    _require(isinstance(live, dict), "live re-verification missing")
    baseline = state.get("external_observations", {})
    candidate = baseline.get("business_candidate", {})
    _require(live.get("main_sha") == baseline.get("main", {}).get("sha"), "live main SHA drift")
    _require(live.get("main_branch_protected") is True, "live main is not protected")
    _require(live.get("lot45_pr") == candidate.get("pr"), "Lot45 PR drift")
    _require(live.get("lot45_head_sha") == candidate.get("head"), "Lot45 head drift")
    _require(live.get("lot45_base_sha") == candidate.get("base"), "Lot45 base drift")
    _require(live.get("lot45_state") == candidate.get("state"), "Lot45 state drift")
    _require(live.get("lot45_merged") is False and candidate.get("merged") is False, "Lot45 merge state drift")
    _require(live.get("live_rulesets_count") == 1, "exactly one live ruleset required")
    _require(live.get("active_rulesets_count") == 1, "exactly one active live ruleset required")
    ruleset = live.get("observed_ruleset")
    _require(isinstance(ruleset, dict), "live ruleset detail missing")
    evaluation = validate_ruleset(ruleset, policy)

    persisted = evidence.get("protection_compliance")
    expected = {
        "mechanism": "REPOSITORY_RULESET",
        "branch_is_protected": True,
        **evaluation["compliance"],
        "floor_satisfied": True,
    }
    _require(persisted == expected, "persisted protection compliance drift")

    hardening = evidence.get("hardening_snapshot")
    _require(isinstance(hardening, dict), "hardening snapshot missing")
    expected_hardening = {
        **evaluation["hardening"],
        "classification": "OPTIONAL_HARDENING_NOT_REQUIRED_FOR_CURRENT_FLOOR",
    }
    _require(hardening == expected_hardening, "hardening snapshot drift")

    _require(evidence.get("live_blocking_findings") == [], "live blockers remain")
    _require(evidence.get("verdict") == policy["eligibility_verdict"], "eligibility verdict drift")
    authority = evidence.get("authority")
    _require(isinstance(authority, dict), "eligibility authority block missing")
    expected_authority = {
        "business_development_unlock_eligible": True,
        "business_development_unlock_executed": False,
        "development_status": "PAUSED",
        "lot45_status": "SUSPENDED_CANDIDATE",
        "lot45_merge_allowed": False,
        "lot46_status": "LOCKED",
        "lot46_unlock_allowed": False,
        "runtime_unlock_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "withdrawals": "FORBIDDEN",
    }
    _require(authority == expected_authority, "eligibility improperly grants authority")
    next_transition = evidence.get("next_transition")
    _require(isinstance(next_transition, dict), "next-transition contract missing")
    _require(next_transition.get("requires_explicit_human_instruction") is True, "explicit human unlock requirement missing")
    _require(next_transition.get("automatic_transition_forbidden") is True, "automatic unlock was enabled")
    _require(next_transition.get("action") == "BUSINESS_DEVELOPMENT_UNLOCK", "next action drift")
    _require(next_transition.get("candidate_merge_separate") is True, "candidate merge separation missing")
    _require(next_transition.get("lot46_unlock_separate") is True, "Lot46 separation missing")


def validate_live(
    evidence: dict[str, Any],
    policy: dict[str, Any],
    state: dict[str, Any],
    *,
    token: str | None,
) -> None:
    blocked_module = _module(
        "unlock_eligibility_live_source",
        ROOT / "scripts/governance/validate_business_development_unlock_decision.py",
    )
    try:
        observed = blocked_module.collect_live_reverification(state, token=token)
    except blocked_module.BusinessUnlockDecisionError as exc:
        raise BusinessUnlockEligibilityError(str(exc)) from exc
    persisted = evidence["live_reverification"]
    for key in (
        "main_sha","main_branch_protected","lot45_pr","lot45_head_sha","lot45_base_sha",
        "lot45_state","lot45_merged","live_rulesets_count","active_rulesets_count","observed_ruleset",
    ):
        _require(observed.get(key) == persisted.get(key), f"live GitHub drift requires re-evaluation: {key}")
    _require(observed.get("main_branch_protected") is True, "live main lost protection")
    validate_ruleset(observed["observed_ruleset"], policy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["snapshot", "github"], default="snapshot")
    args = parser.parse_args()
    try:
        evidence = _json(EVIDENCE_PATH)
        policy = _json(POLICY_PATH)
        state = _json(STATE_PATH)
        blocked = _json(BLOCKED_DECISION_PATH)
        security = _json(SECURITY_PATH)
        certification = _json(CERT_PATH)
        validate_snapshot(evidence, policy, state, blocked, security, certification)
        if args.mode == "github":
            validate_live(evidence, policy, state, token=os.environ.get("GITHUB_TOKEN"))
    except (BusinessUnlockEligibilityError, KeyError, TypeError) as exc:
        print(f"BUSINESS_UNLOCK_ELIGIBILITY_INVALID: {exc}", file=sys.stderr)
        return 1
    suffix = " live=EXACT_MATCH" if args.mode == "github" else ""
    print(
        "BUSINESS_UNLOCK_ELIGIBILITY_VALID "
        "verdict=ELIGIBLE_AWAITING_EXPLICIT_HUMAN_UNLOCK authority=UNCHANGED"
        + suffix
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
