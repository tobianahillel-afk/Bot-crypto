#!/usr/bin/env python3
"""Validate agent capability policy and individual evidence claims."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "engineering" / "AGENT_CAPABILITIES.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class EvidencePolicyError(ValueError):
    pass


def load_policy() -> dict[str, Any]:
    try:
        value = json.loads(POLICY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidencePolicyError(f"cannot load policy: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidencePolicyError("policy must be an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise EvidencePolicyError("unsupported schema_version")
    if policy.get("policy_kind") != "agent_execution_evidence_policy_v1":
        raise EvidencePolicyError("invalid policy_kind")

    cost = policy.get("mandatory_cost_policy")
    if not isinstance(cost, dict) or any(value is not False for value in cost.values()):
        raise EvidencePolicyError("mandatory execution/evidence path must remain zero-cost")

    evidence = policy.get("evidence_classes")
    claims = policy.get("claim_rules")
    profiles = policy.get("profiles")
    if not isinstance(evidence, dict) or not evidence:
        raise EvidencePolicyError("evidence_classes are required")
    if not isinstance(claims, dict) or not claims:
        raise EvidencePolicyError("claim_rules are required")
    if not isinstance(profiles, dict) or not profiles:
        raise EvidencePolicyError("profiles are required")

    required_profiles = {
        "GITHUB_CONNECTOR_ONLY",
        "LOCAL_REPOSITORY",
        "CI_EXECUTION",
        "READ_ONLY_AUDITOR",
    }
    if set(profiles) != required_profiles:
        raise EvidencePolicyError("capability profile set drift")

    for name, rule in evidence.items():
        if not isinstance(rule, dict):
            raise EvidencePolicyError(f"evidence class {name} must be an object")
        fields = rule.get("required_fields")
        if not isinstance(fields, list) or not fields or len(fields) != len(set(fields)):
            raise EvidencePolicyError(f"evidence class {name} has invalid required_fields")

    for claim_kind, rule in claims.items():
        if not isinstance(rule, dict):
            raise EvidencePolicyError(f"claim rule {claim_kind} must be an object")
        allowed = rule.get("allowed_evidence")
        if not isinstance(allowed, list) or not allowed:
            raise EvidencePolicyError(f"claim rule {claim_kind} must declare allowed_evidence")
        unknown = [item for item in allowed if item not in evidence]
        if unknown:
            raise EvidencePolicyError(f"claim rule {claim_kind} uses unknown evidence: {unknown}")

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            raise EvidencePolicyError(f"profile {profile_name} must be an object")
        allowed = profile.get("allowed_claim_kinds")
        forbidden = profile.get("forbidden_claim_kinds")
        valid = profile.get("valid_evidence")
        if not isinstance(allowed, list) or not isinstance(forbidden, list) or not isinstance(valid, list):
            raise EvidencePolicyError(f"profile {profile_name} claim/evidence lists are invalid")
        if set(allowed) & set(forbidden):
            raise EvidencePolicyError(f"profile {profile_name} allows and forbids the same claim")
        if any(item not in claims for item in allowed + forbidden):
            raise EvidencePolicyError(f"profile {profile_name} references unknown claim kind")
        if any(item not in evidence for item in valid):
            raise EvidencePolicyError(f"profile {profile_name} references unknown evidence class")

    github = profiles["GITHUB_CONNECTOR_ONLY"]
    if github.get("local_execution") is not False:
        raise EvidencePolicyError("GITHUB_CONNECTOR_ONLY local_execution must be false")
    if github.get("may_claim_local_test_pass") is not False:
        raise EvidencePolicyError("GITHUB_CONNECTOR_ONLY may never claim local test PASS")
    if "LOCAL_TEST_PASS" not in github.get("forbidden_claim_kinds", []):
        raise EvidencePolicyError("GITHUB_CONNECTOR_ONLY must explicitly forbid LOCAL_TEST_PASS")

    auditor = profiles["READ_ONLY_AUDITOR"]
    if auditor.get("github_write") is not False or auditor.get("may_mutate_repository") is not False:
        raise EvidencePolicyError("READ_ONLY_AUDITOR must be non-mutating")
    if "REPOSITORY_MUTATION" not in auditor.get("forbidden_claim_kinds", []):
        raise EvidencePolicyError("READ_ONLY_AUDITOR must forbid mutation claims")


def validate_claim(
    policy: dict[str, Any],
    profile_name: str,
    claim: dict[str, Any],
) -> None:
    validate_policy(policy)
    profiles = policy["profiles"]
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise EvidencePolicyError(f"unknown profile: {profile_name}")

    claim_kind = claim.get("claim_kind")
    evidence_class = claim.get("evidence_class")
    if claim_kind in profile.get("forbidden_claim_kinds", []):
        raise EvidencePolicyError(f"{profile_name} forbids claim kind {claim_kind}")
    if claim_kind not in profile.get("allowed_claim_kinds", []):
        raise EvidencePolicyError(f"{profile_name} does not allow claim kind {claim_kind}")
    if evidence_class not in profile.get("valid_evidence", []):
        raise EvidencePolicyError(f"{profile_name} cannot use evidence class {evidence_class}")

    claim_rule = policy["claim_rules"].get(claim_kind)
    evidence_rule = policy["evidence_classes"].get(evidence_class)
    if not isinstance(claim_rule, dict) or not isinstance(evidence_rule, dict):
        raise EvidencePolicyError("claim/evidence rule is missing")
    if evidence_class not in claim_rule.get("allowed_evidence", []):
        raise EvidencePolicyError(f"{evidence_class} cannot prove {claim_kind}")

    evidence = claim.get("evidence")
    if not isinstance(evidence, dict):
        raise EvidencePolicyError("claim evidence must be an object")
    missing = [
        field for field in evidence_rule.get("required_fields", [])
        if field not in evidence
    ]
    if missing:
        raise EvidencePolicyError(f"evidence missing required fields: {missing}")

    if evidence_class == "EXACT_GITHUB_REF":
        sha = evidence.get("sha")
        if not isinstance(sha, str) or SHA40.fullmatch(sha) is None:
            raise EvidencePolicyError("EXACT_GITHUB_REF requires lowercase SHA-40")
    if evidence_class == "EXACT_GITHUB_ACTIONS_RUN":
        run_id = evidence.get("run_id")
        head_sha = evidence.get("head_sha")
        if not isinstance(run_id, int) or run_id <= 0:
            raise EvidencePolicyError("workflow run_id must be a positive integer")
        if not isinstance(head_sha, str) or SHA40.fullmatch(head_sha) is None:
            raise EvidencePolicyError("workflow head_sha must be lowercase SHA-40")
        if claim_rule.get("requires_success_conclusion") is True:
            if evidence.get("conclusion") != "success":
                raise EvidencePolicyError("CI_PASS requires conclusion=success")
    if evidence_class == "LOCAL_COMMAND_OUTPUT":
        if claim_rule.get("requires_executed_local_command") is True and evidence.get("executed") is not True:
            raise EvidencePolicyError("LOCAL_TEST_PASS requires actual execution")
        if claim_rule.get("requires_exit_code_zero") is True and evidence.get("exit_code") != 0:
            raise EvidencePolicyError("LOCAL_TEST_PASS requires exit_code=0")


def main() -> int:
    try:
        validate_policy(load_policy())
    except EvidencePolicyError as exc:
        print(f"AGENT_EVIDENCE_POLICY_INVALID: {exc}", file=sys.stderr)
        return 1
    print("AGENT_EVIDENCE_POLICY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
