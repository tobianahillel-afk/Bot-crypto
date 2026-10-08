#!/usr/bin/env python3
"""Adversarial qualification for ENG-08.4 mandatory zero-paid-requirement proof."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(error_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except error_type:
        return
    raise AssertionError(f"mandatory-cost negative scenario unexpectedly passed: {label}")


def run_selftests(
    static_result: dict[str, Any],
    evidence: dict[str, Any],
    policy: dict[str, Any],
) -> int:
    q = _module(
        "mandatory_cost_qualifier_for_selftest",
        ROOT / "scripts/governance/qualify_mandatory_cost_zero.py",
    )
    error = q.MandatoryCostQualificationError
    valid = q.qualify(static_result, evidence, policy)
    assert valid["verdict"] == "PASS_MANDATORY_PATH_ZERO_PAID_REQUIREMENT"
    assert valid["mandatory_paid_spend_required_usd"] == 0
    assert valid["account_wide_no_bill_claim"] is False
    probes = 3

    def mutated_evidence(mutator: Any) -> dict[str, Any]:
        value = copy.deepcopy(evidence)
        mutator(value)
        return value

    def mutated_static(mutator: Any) -> dict[str, Any]:
        value = copy.deepcopy(static_result)
        mutator(value)
        return value

    cases = [
        ("private visibility", lambda e: e["repository_observation"].update({"visibility": "private", "private": True})),
        ("repository id mismatch", lambda e: e["repository_observation"].update({"id": "0"})),
        ("archived repository", lambda e: e["repository_observation"].update({"archived": True})),
        ("default branch drift", lambda e: e["repository_observation"].update({"default_branch": "dev"})),
        ("public runner not free", lambda e: e["github_actions_billing_observation"]["facts"].update({"standard_public_runner_usage_free": False})),
        ("public runner not unlimited", lambda e: e["github_actions_billing_observation"]["facts"].update({"standard_public_runner_usage_unlimited": False})),
        ("larger runner billing guard removed", lambda e: e["github_actions_billing_observation"]["facts"].update({"larger_runners_always_billed": False})),
        ("ubuntu latest not standard", lambda e: e["github_actions_billing_observation"]["facts"].update({"standard_public_runner_labels": []})),
        ("cache allowance drift", lambda e: e["github_actions_billing_observation"]["facts"].update({"default_cache_included_gb_per_repository": 0})),
        ("paid cache expansion required", lambda e: e["engine_storage_observation"].update({"paid_cache_limit_expansion_required": True})),
        ("account-wide no-bill overclaim", lambda e: e["claim_scope"].update({"account_wide_no_bill_claim": True})),
        ("unofficial billing source", lambda e: e["github_actions_billing_observation"]["sources"].update({"actions_billing": "https://example.invalid"})),
    ]
    for label, mutator in cases:
        candidate = mutated_evidence(mutator)
        _expect(error, lambda candidate=candidate: q.qualify(static_result, candidate, policy), label)
        probes += 1

    static_cases = [
        ("wrong static verdict", lambda s: s.update({"verdict": "PASS"})),
        ("paid API required", lambda s: s.update({"paid_external_api_required": True})),
        ("paid runner required", lambda s: s.update({"paid_runner_required_by_configuration": True})),
        ("repository secret introduced", lambda s: s["mandatory_workflows"][0].update({"repository_secret_refs": ["OPENAI_API_KEY"]})),
        ("larger runner introduced", lambda s: s["mandatory_workflows"][0].update({"runners": ["ubuntu-latest-16-cores"]})),
        ("unclassified action introduced", lambda s: s.update({"remote_action_repositories": s["remote_action_repositories"] + ["vendor/paid-action"]})),
    ]
    for label, mutator in static_cases:
        candidate = mutated_static(mutator)
        _expect(error, lambda candidate=candidate: q.qualify(candidate, evidence, policy), label)
        probes += 1

    return probes


def main() -> int:
    auditor = _module(
        "mandatory_cost_static_for_selftest",
        ROOT / "scripts/governance/verify_mandatory_cost_zero.py",
    )
    policy = auditor._json(ROOT / "config/governance/mandatory_cost_zero_policy_v1.json")
    static_result = auditor.static_audit(policy)
    evidence = auditor._json(ROOT / policy["qualification"]["evidence_path"])
    count = run_selftests(static_result, evidence, policy)
    print(f"MANDATORY_COST_SELFTEST_PASS probes={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
