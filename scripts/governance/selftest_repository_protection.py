#!/usr/bin/env python3
"""Adversarial qualification for repository-protection unlock policy."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_repository_protection.py"
    spec = importlib.util.spec_from_file_location("repository_protection_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"repository-protection negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    status = mod._json(mod.STATUS_PATH)
    project_state = mod._json(mod.PROJECT_STATE_PATH)
    mod.validate_policy(policy)
    mod.validate_current_status(status, policy, project_state)

    current_failures = mod.unlock_failures(status, policy)
    assert "NO_VERIFIED_PROTECTION_MECHANISM" in current_failures
    assert "BUSINESS_UNLOCK_FLAG_FALSE" in current_failures

    protected = copy.deepcopy(status)
    protected["branch_resource"]["protected"] = True
    protected["rulesets"]["count"] = 1
    protected["branch_protection_detail"]["state"] = "VERIFIED_BY_ADMIN_OR_RULESET_EVIDENCE"
    protected["enforcement"] = {
        "mechanism": "REPOSITORY_RULESET",
        "pull_request_required": True,
        "required_status_checks": True,
        "force_pushes_blocked": True,
        "branch_deletions_blocked": True,
    }
    protected["overall_status"] = "PROTECTED_VERIFIED"
    protected["business_unlock_allowed"] = True
    protected["manual_admin_action_required"] = False
    assert mod.unlock_failures(protected, policy) == []

    unverifiable = copy.deepcopy(protected)
    unverifiable["enforcement"]["required_status_checks"] = "UNVERIFIED"
    assert any("required_status_checks" in item for item in mod.unlock_failures(unverifiable, policy))

    no_mechanism = copy.deepcopy(protected)
    no_mechanism["branch_resource"]["protected"] = False
    no_mechanism["rulesets"]["count"] = 0
    assert "NO_VERIFIED_PROTECTION_MECHANISM" in mod.unlock_failures(no_mechanism, policy)

    bad_state = copy.deepcopy(project_state)
    bad_state["findings"] = [x for x in bad_state["findings"] if x.get("id") != "BOOT-FINDING-001"]
    _expect(
        mod.RepositoryProtectionError,
        lambda: mod.validate_current_status(status, policy, bad_state),
        "removed unresolved protection finding",
    )

    wrong_sha = copy.deepcopy(status)
    wrong_sha["main_sha"] = "0" * 40
    _expect(
        mod.RepositoryProtectionError,
        lambda: mod.validate_current_status(wrong_sha, policy, project_state),
        "stale main SHA",
    )

    forged_403 = copy.deepcopy(status)
    forged_403["overall_status"] = "PROTECTED_VERIFIED"
    _expect(
        mod.RepositoryProtectionError,
        lambda: mod.validate_current_status(forged_403, policy, project_state),
        "403 treated as protection proof",
    )

    paid = copy.deepcopy(policy)
    paid["cost_policy"]["paid_api_required"] = True
    _expect(mod.RepositoryProtectionError, lambda: mod.validate_policy(paid), "paid API requirement")

    weakened = copy.deepcopy(policy)
    weakened["required_enforcement"]["force_pushes_blocked"] = False
    _expect(mod.RepositoryProtectionError, lambda: mod.validate_policy(weakened), "weakened force-push policy")

    print("REPOSITORY_PROTECTION_SELFTEST_PASS probes=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
