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


def _unprotected_status(status: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(status)
    value["branch_resource"]["protected"] = False
    value["rulesets"]["count"] = 0
    value["branch_protection_detail"]["state"] = "UNAVAILABLE_403_INTEGRATION_PERMISSION"
    value["enforcement"] = {
        "mechanism": "NONE_VERIFIED",
        "pull_request_required": "UNVERIFIED",
        "required_status_checks": "UNVERIFIED",
        "force_pushes_blocked": "UNVERIFIED",
        "branch_deletions_blocked": "UNVERIFIED",
    }
    value["overall_status"] = "UNPROTECTED"
    value["business_unlock_allowed"] = False
    value["manual_admin_action_required"] = True
    value["blocking_finding_id"] = "BOOT-FINDING-001"
    return value


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    status = mod._json(mod.STATUS_PATH)
    project_state = mod._json(mod.PROJECT_STATE_PATH)
    mod.validate_policy(policy)
    mod.validate_current_status(status, policy, project_state)

    assert mod.unlock_failures(status, policy) == []

    unverifiable = copy.deepcopy(status)
    unverifiable["enforcement"]["required_status_checks"] = "UNVERIFIED"
    assert any("required_status_checks" in item for item in mod.unlock_failures(unverifiable, policy))

    no_mechanism = copy.deepcopy(status)
    no_mechanism["branch_resource"]["protected"] = False
    no_mechanism["rulesets"]["count"] = 0
    assert "NO_VERIFIED_PROTECTION_MECHANISM" in mod.unlock_failures(no_mechanism, policy)

    historical = _unprotected_status(status)
    historical_state = copy.deepcopy(project_state)
    historical_state["external_observations"]["main"]["branch_protected"] = False
    historical_state["external_observations"]["rulesets_count"] = 0
    for finding in historical_state["findings"]:
        if finding.get("id") == "BOOT-FINDING-001":
            finding["observed"] = True
    mod.validate_current_status(historical, policy, historical_state)
    assert "NO_VERIFIED_PROTECTION_MECHANISM" in mod.unlock_failures(historical, policy)

    missing_finding = copy.deepcopy(historical_state)
    missing_finding["findings"] = [
        item for item in missing_finding["findings"]
        if item.get("id") != "BOOT-FINDING-001"
    ]
    _expect(
        mod.RepositoryProtectionError,
        lambda: mod.validate_current_status(historical, policy, missing_finding),
        "unprotected state without unresolved finding",
    )

    wrong_sha = copy.deepcopy(status)
    wrong_sha["main_sha"] = "0" * 40
    _expect(
        mod.RepositoryProtectionError,
        lambda: mod.validate_current_status(wrong_sha, policy, project_state),
        "stale main SHA",
    )

    branch_mismatch = copy.deepcopy(status)
    branch_mismatch["branch_resource"]["protected"] = False
    _expect(
        mod.RepositoryProtectionError,
        lambda: mod.validate_current_status(branch_mismatch, policy, project_state),
        "branch protection flag mismatch",
    )

    forged_403 = copy.deepcopy(status)
    forged_403["branch_protection_detail"]["state"] = "UNAVAILABLE_403_INTEGRATION_PERMISSION"
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

    print("REPOSITORY_PROTECTION_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
