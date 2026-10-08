#!/usr/bin/env python3
"""Qualify ENG-08.4 mandatory zero-paid-requirement evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "mandatory_cost_zero_policy_v1.json"


class MandatoryCostQualificationError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MandatoryCostQualificationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MandatoryCostQualificationError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise MandatoryCostQualificationError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MandatoryCostQualificationError(message)


def validate_evidence(evidence: dict[str, Any], policy: dict[str, Any]) -> None:
    _require(evidence.get("schema_version") == 1, "unsupported live evidence schema_version")
    _require(
        evidence.get("evidence_kind") == "mandatory_cost_zero_live_evidence_v1",
        "invalid live evidence kind",
    )
    _require(evidence.get("observed_date") == "2026-09-24", "qualification observation date drift")

    qualification = policy.get("qualification")
    _require(isinstance(qualification, dict), "qualification policy missing")
    required_repo = qualification.get("required_repository")
    _require(isinstance(required_repo, dict), "required repository binding missing")
    repo = evidence.get("repository_observation")
    _require(isinstance(repo, dict), "repository observation missing")
    _require(repo.get("source") == "GITHUB_CONNECTOR_GET_REPO", "repository evidence source drift")
    for key in ("id", "full_name", "visibility", "archived", "default_branch"):
        _require(repo.get(key) == required_repo.get(key), f"repository observation mismatch: {key}")
    _require(repo.get("private") is False, "repository must not be private")
    _require(repo.get("visibility") == "public", "repository visibility must be public")
    _require(repo.get("archived") is False, "repository must not be archived")

    binding = evidence.get("static_wu01_binding")
    _require(isinstance(binding, dict), "WU01 static binding missing")
    _require(
        binding.get("head_sha") == "e341ad2693e246ddee32939b452c87f5a3ce55a0",
        "WU01 static head binding drift",
    )
    _require(binding.get("bootstrap_run_id") == 36057570058, "WU01 bootstrap run binding drift")
    _require(binding.get("bootstrap_conclusion") == "success", "WU01 bootstrap must be successful")
    _require(
        binding.get("static_verdict") == "PASS_WITH_VISIBILITY_UNVERIFIED",
        "WU01 static verdict binding drift",
    )

    billing = evidence.get("github_actions_billing_observation")
    _require(isinstance(billing, dict), "GitHub billing observation missing")
    _require(billing.get("source_kind") == "OFFICIAL_GITHUB_DOCUMENTATION", "billing source kind drift")
    _require(billing.get("observed_date") == "2026-09-24", "billing observation date drift")
    sources = billing.get("sources")
    required_sources = {
        "actions_billing": "https://docs.github.com/en/billing/concepts/product-billing/github-actions",
        "hosted_runners": "https://docs.github.com/en/actions/reference/runners/github-hosted-runners",
        "larger_runners": "https://docs.github.com/en/actions/concepts/runners/larger-runners",
        "dependency_cache": "https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching",
        "advanced_security_billing": "https://docs.github.com/en/billing/concepts/product-billing/github-advanced-security",
    }
    _require(sources == required_sources, "official GitHub documentation source set drift")

    facts = billing.get("facts")
    _require(isinstance(facts, dict), "GitHub billing facts missing")
    for key in (
        "standard_public_runner_usage_free",
        "standard_public_runner_usage_unlimited",
        "larger_runners_always_billed",
        "cache_overage_requires_usage_above_included_allowance",
        "increasing_cache_limit_beyond_default_can_incur_cost",
        "code_scanning_free_for_public_repositories",
        "dependency_review_free_for_public_repositories",
    ):
        _require(facts.get(key) is True, f"required GitHub billing fact is not true: {key}")
    _require(facts.get("standard_public_runner_labels") == ["ubuntu-latest"], "standard runner label drift")
    _require(facts.get("default_cache_included_gb_per_repository") == 10, "included cache allowance drift")

    storage = evidence.get("engine_storage_observation")
    _require(isinstance(storage, dict), "engine storage observation missing")
    _require(storage.get("upload_artifact_action_required") is False, "artifact upload must not be required")
    _require(storage.get("explicit_actions_cache_action_required") is False, "actions/cache must not be required")
    _require(
        storage.get("setup_python_cache_workflows") == [".github/workflows/security-dependencies.yml"],
        "setup-python cache workflow binding drift",
    )
    _require(storage.get("paid_cache_limit_expansion_required") is False, "paid cache expansion must not be required")

    claim = evidence.get("claim_scope")
    _require(isinstance(claim, dict), "claim scope missing")
    _require(claim.get("mandatory_paid_requirement_only") is True, "claim must be mandatory-path scoped")
    _require(claim.get("account_wide_no_bill_claim") is False, "account-wide no-bill claim is forbidden")
    _require(claim.get("optional_paid_products_excluded") is True, "optional paid products must be excluded")
    _require(claim.get("optional_cache_limit_expansion_excluded") is True, "optional cache expansion must be excluded")
    _require(claim.get("payment_method_or_balance_queried") is False, "billing/payment query is forbidden")


def qualify(
    static_result: dict[str, Any],
    evidence: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_evidence(evidence, policy)
    _require(
        static_result.get("verdict") == "PASS_WITH_VISIBILITY_UNVERIFIED",
        "qualification requires WU01 PASS_WITH_VISIBILITY_UNVERIFIED",
    )
    _require(static_result.get("mandatory_workflow_count") == 6, "mandatory workflow count drift")
    for key in (
        "paid_external_api_required",
        "paid_license_required",
        "paid_llm_required",
        "paid_runner_required_by_configuration",
        "paid_saas_required",
        "network_required_by_auditor",
        "billing_api_queried",
    ):
        _require(static_result.get(key) is False, f"static paid/network flag is not false: {key}")

    workflows = static_result.get("mandatory_workflows")
    _require(isinstance(workflows, list) and len(workflows) == 6, "mandatory workflow inventory invalid")
    standard = set(
        evidence["github_actions_billing_observation"]["facts"]["standard_public_runner_labels"]
    )
    for workflow in workflows:
        _require(isinstance(workflow, dict), "workflow inventory entry invalid")
        runners = workflow.get("runners")
        _require(isinstance(runners, list) and runners, "workflow runner inventory missing")
        _require(set(runners) <= standard, f"non-standard runner in mandatory workflow: {workflow.get('path')}")
        _require(workflow.get("repository_secret_refs") == [], f"repository secret required by {workflow.get('path')}")

    expected_actions = set(policy["zero_cost_action_allowlist"])
    actual_actions = set(static_result.get("remote_action_repositories", []))
    _require(actual_actions <= expected_actions, "unclassified remote action repository present")

    repo = evidence["repository_observation"]
    facts = evidence["github_actions_billing_observation"]["facts"]
    _require(repo["visibility"] == "public" and repo["private"] is False, "public repository condition not satisfied")
    _require(facts["standard_public_runner_usage_free"] is True, "standard public runners are not proven free")
    _require(facts["standard_public_runner_usage_unlimited"] is True, "standard public runners are not proven unlimited")
    _require(facts["larger_runners_always_billed"] is True, "larger-runner billing guard missing")
    _require(facts["code_scanning_free_for_public_repositories"] is True, "public CodeQL/code scanning free-use evidence missing")
    _require(facts["dependency_review_free_for_public_repositories"] is True, "public dependency-review free-use evidence missing")

    return {
        "schema_version": 1,
        "qualification_kind": "mandatory_cost_zero_qualification_v1",
        "verdict": policy["qualification"]["expected_final_verdict"],
        "repository": {
            "id": repo["id"],
            "full_name": repo["full_name"],
            "visibility": repo["visibility"],
        },
        "mandatory_workflow_count": static_result["mandatory_workflow_count"],
        "runner_labels": sorted({
            runner
            for workflow in workflows
            for runner in workflow["runners"]
        }),
        "mandatory_paid_requirement": False,
        "mandatory_paid_spend_required_usd": 0,
        "paid_api_required": False,
        "paid_llm_required": False,
        "paid_saas_required": False,
        "paid_license_required": False,
        "paid_larger_runner_required": False,
        "paid_cache_expansion_required": False,
        "account_wide_no_bill_claim": False,
        "optional_paid_products_excluded": True,
        "optional_cache_limit_expansion_excluded": True,
        "billing_balance_queried": False,
        "evidence_observed_date": evidence["observed_date"],
        "claim_scope": policy["qualification"]["claim_scope"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-evidence", action="store_true")
    args = parser.parse_args()
    if not args.check_evidence:
        print("MANDATORY_COST_QUALIFICATION_INVALID: --check-evidence is required", file=sys.stderr)
        return 2
    try:
        policy = _json(POLICY_PATH)
        auditor = _module(
            "mandatory_cost_static_for_qualification",
            ROOT / "scripts/governance/verify_mandatory_cost_zero.py",
        )
        static_result = auditor.static_audit(policy)
        evidence = _json(ROOT / policy["qualification"]["evidence_path"])
        result = qualify(static_result, evidence, policy)
    except (MandatoryCostQualificationError, KeyError, TypeError, auditor.MandatoryCostError) as exc:
        print(f"MANDATORY_COST_QUALIFICATION_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
