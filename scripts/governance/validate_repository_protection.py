#!/usr/bin/env python3
"""Validate repository-protection evidence and fail closed for business unlock."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "repository_protection_policy_v1.json"
STATUS_PATH = ROOT / "engineering" / "REPOSITORY_PROTECTION_STATUS.json"
PROJECT_STATE_PATH = ROOT / "config" / "governance" / "project_state.json"


class RepositoryProtectionError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepositoryProtectionError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RepositoryProtectionError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise RepositoryProtectionError("unsupported protection policy schema_version")
    if policy.get("policy_kind") != "repository_protection_policy_v1":
        raise RepositoryProtectionError("invalid protection policy kind")
    if policy.get("semantics") != "BUSINESS_UNLOCK_REQUIRES_VERIFIED_MAIN_PROTECTION":
        raise RepositoryProtectionError("repository-protection semantics drift")
    if policy.get("repository") != "tobianahillel-afk/Bot-crypto":
        raise RepositoryProtectionError("repository identity drift")
    if policy.get("default_branch") != "main":
        raise RepositoryProtectionError("default branch drift")
    required = policy.get("required_enforcement")
    expected = {
        "branch_is_protected": True,
        "pull_request_required": True,
        "required_status_checks": True,
        "force_pushes_blocked": True,
        "branch_deletions_blocked": True,
    }
    if required != expected:
        raise RepositoryProtectionError("required repository protection floor drift")
    mechanisms = policy.get("accepted_mechanisms")
    if mechanisms != ["BRANCH_PROTECTION", "REPOSITORY_RULESET"]:
        raise RepositoryProtectionError("accepted protection mechanisms drift")
    capability = policy.get("current_connector_capability")
    if not isinstance(capability, dict):
        raise RepositoryProtectionError("connector capability declaration missing")
    if capability.get("administration_mutation_available") is not False:
        raise RepositoryProtectionError("connector must not claim unavailable admin mutation")
    unlock = policy.get("unlock_behavior")
    if not isinstance(unlock, dict):
        raise RepositoryProtectionError("unlock behavior missing")
    if unlock.get("fail_closed_on_unprotected") is not True:
        raise RepositoryProtectionError("unprotected main must fail closed")
    if unlock.get("fail_closed_on_unverifiable") is not True:
        raise RepositoryProtectionError("unverifiable protection must fail closed")
    if unlock.get("fresh_live_verification_required") is not True:
        raise RepositoryProtectionError("fresh live verification requirement missing")
    if unlock.get("unresolved_finding_id") != "BOOT-FINDING-001":
        raise RepositoryProtectionError("unlock finding binding drift")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise RepositoryProtectionError("protection requirement must remain zero-cost")


def _finding(project_state: dict[str, Any], finding_id: str) -> dict[str, Any] | None:
    findings = project_state.get("findings")
    if not isinstance(findings, list):
        raise RepositoryProtectionError("project findings list missing")
    for item in findings:
        if isinstance(item, dict) and item.get("id") == finding_id:
            return item
    return None


def validate_current_status(
    status: dict[str, Any],
    policy: dict[str, Any],
    project_state: dict[str, Any],
) -> None:
    if status.get("schema_version") != 1:
        raise RepositoryProtectionError("unsupported protection status schema_version")
    if status.get("status_kind") != "repository_protection_status_v1":
        raise RepositoryProtectionError("invalid protection status kind")
    if status.get("repository") != policy["repository"]:
        raise RepositoryProtectionError("status repository identity drift")
    if status.get("default_branch") != policy["default_branch"]:
        raise RepositoryProtectionError("status default branch drift")

    external = project_state.get("external_observations")
    if not isinstance(external, dict):
        raise RepositoryProtectionError("project external observations missing")
    main = external.get("main")
    if not isinstance(main, dict):
        raise RepositoryProtectionError("project main observation missing")
    if status.get("main_sha") != main.get("sha"):
        raise RepositoryProtectionError("protection status main SHA differs from project state")
    branch = status.get("branch_resource")
    rulesets = status.get("rulesets")
    detail = status.get("branch_protection_detail")
    if not isinstance(branch, dict) or not isinstance(rulesets, dict) or not isinstance(detail, dict):
        raise RepositoryProtectionError("protection observation components missing")
    if branch.get("protected") != main.get("branch_protected"):
        raise RepositoryProtectionError("branch protected flag differs from project state")
    if rulesets.get("count") != external.get("rulesets_count"):
        raise RepositoryProtectionError("ruleset count differs from project state")

    protected = branch.get("protected") is True
    ruleset_present = isinstance(rulesets.get("count"), int) and rulesets["count"] > 0
    if not protected and not ruleset_present:
        if status.get("overall_status") != "UNPROTECTED":
            raise RepositoryProtectionError("unprotected observation must remain UNPROTECTED")
        if status.get("business_unlock_allowed") is not False:
            raise RepositoryProtectionError("unprotected observation cannot allow business unlock")
        if status.get("manual_admin_action_required") is not True:
            raise RepositoryProtectionError("unprotected observation requires manual admin action")
        finding = _finding(project_state, policy["unlock_behavior"]["unresolved_finding_id"])
        if finding is None or finding.get("observed") is not True:
            raise RepositoryProtectionError("unprotected observation requires unresolved project finding")
    if detail.get("state") == "UNAVAILABLE_403_INTEGRATION_PERMISSION" and status.get("overall_status") == "PROTECTED_VERIFIED":
        raise RepositoryProtectionError("403 admin evidence cannot prove protection by itself")


def unlock_failures(status: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    branch = status.get("branch_resource", {})
    rulesets = status.get("rulesets", {})
    enforcement = status.get("enforcement", {})

    if status.get("overall_status") != "PROTECTED_VERIFIED":
        failures.append("OVERALL_STATUS_NOT_PROTECTED_VERIFIED")
    if branch.get("protected") is not True and not (
        isinstance(rulesets.get("count"), int) and rulesets.get("count", 0) > 0
    ):
        failures.append("NO_VERIFIED_PROTECTION_MECHANISM")
    expected = {
        "pull_request_required": True,
        "required_status_checks": True,
        "force_pushes_blocked": True,
        "branch_deletions_blocked": True,
    }
    for key, wanted in expected.items():
        if enforcement.get(key) is not wanted:
            failures.append(f"ENFORCEMENT_NOT_VERIFIED:{key}")
    if enforcement.get("mechanism") not in policy["accepted_mechanisms"]:
        failures.append("ENFORCEMENT_MECHANISM_NOT_ACCEPTED")
    if status.get("business_unlock_allowed") is not True:
        failures.append("BUSINESS_UNLOCK_FLAG_FALSE")
    if status.get("manual_admin_action_required") is not False:
        failures.append("MANUAL_ADMIN_ACTION_STILL_REQUIRED")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["policy", "unlock"], required=True)
    args = parser.parse_args()
    try:
        policy = _json(POLICY_PATH)
        status = _json(STATUS_PATH)
        project_state = _json(PROJECT_STATE_PATH)
        validate_policy(policy)
        validate_current_status(status, policy, project_state)
        failures = unlock_failures(status, policy)
        if args.mode == "unlock":
            if failures:
                for failure in failures:
                    print(f"REPOSITORY_PROTECTION_UNLOCK_BLOCKED:{failure}", file=sys.stderr)
                return 1
            print("REPOSITORY_PROTECTION_UNLOCK_PASS")
            return 0
        print(json.dumps({
            "overall_status": status["overall_status"],
            "business_unlock_allowed": status["business_unlock_allowed"],
            "manual_admin_action_required": status["manual_admin_action_required"],
            "unlock_failure_count": len(failures),
        }, sort_keys=True))
        print("REPOSITORY_PROTECTION_POLICY_VALID")
        return 0
    except (RepositoryProtectionError, OSError, KeyError) as exc:
        print(f"REPOSITORY_PROTECTION_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
