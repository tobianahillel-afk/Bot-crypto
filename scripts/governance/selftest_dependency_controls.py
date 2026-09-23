#!/usr/bin/env python3
"""Adversarial qualification for ENG-04.2 dependency controls."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_dependency_controls.py"
    spec = importlib.util.spec_from_file_location("dependency_controls_selftest", path)
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
    raise AssertionError(f"dependency-control negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    workflow = mod.WORKFLOW_PATH.read_text(encoding="utf-8")
    mod.validate_policy(policy)
    mod.validate_manifests(policy)
    mod.validate_workflow(policy, workflow)

    floating = workflow.replace(
        policy["dependency_review"]["action"] + "@" + policy["dependency_review"]["commit"],
        policy["dependency_review"]["action"] + "@v5",
    )
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, floating), "floating dependency-review action")

    weaker = workflow.replace("fail-on-severity: low", "fail-on-severity: high")
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, weaker), "weakened severity")

    scopes = workflow.replace("runtime,development,unknown", "runtime")
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, scopes), "development scope removed")

    warning = workflow.replace("warn-only: false", "warn-only: true")
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, warning), "warn-only enabled")

    comment = workflow.replace("comment-summary-in-pr: never", "comment-summary-in-pr: always")
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, comment), "PR comments enabled")

    writable = workflow.replace("contents: read", "contents: write")
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, writable), "write permission")

    resolver = workflow.replace("--disable-pip --strict", "--strict")
    _expect(mod.DependencyControlError, lambda: mod.validate_workflow(policy, resolver), "pip resolution re-enabled")

    paid = copy.deepcopy(policy)
    paid["cost_policy"]["paid_saas_required"] = True
    _expect(mod.DependencyControlError, lambda: mod.validate_policy(paid), "paid SaaS")

    bad_review = copy.deepcopy(policy)
    bad_review["dependency_review"]["commit"] = "0" * 40
    _expect(mod.DependencyControlError, lambda: mod.validate_policy(bad_review), "Dependency Review SHA drift")

    _expect(
        mod.DependencyControlError,
        lambda: mod._parse_pin("pytest>=9", "synthetic"),
        "floating requirement",
    )
    _expect(
        mod.DependencyControlError,
        lambda: mod._parse_pin("example @ https://example.invalid/pkg.whl", "synthetic"),
        "URL requirement",
    )

    print("DEPENDENCY_CONTROLS_SELFTEST_PASS probes=11")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
