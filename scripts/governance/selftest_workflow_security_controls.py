#!/usr/bin/env python3
"""Adversarial qualification for ENG-04.4 actionlint plus zizmor controls."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_workflow_security_controls.py"
    spec = importlib.util.spec_from_file_location("workflow_security_selftest", path)
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
    raise AssertionError(f"workflow-security negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    workflow = mod.WORKFLOW_PATH.read_text(encoding="utf-8")
    mod.validate_policy(policy)
    mod.validate_workflow(policy, workflow)

    wrong_digest = workflow.replace(policy["actionlint"]["asset_sha256"], "0" * 64)
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, wrong_digest), "asset digest drift")
    no_digest_check = workflow.replace("sha256sum --check --strict", "sha256sum")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, no_digest_check), "digest check weakened")
    floating_checkout = workflow.replace(
        "actions/checkout@" + policy["toolchain"]["checkout_action_sha"], "actions/checkout@v7"
    )
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, floating_checkout), "floating checkout")
    write_permission = workflow.replace("contents: read", "contents: write")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, write_permission), "write permission")
    persisted = workflow.replace("persist-credentials: false", "persist-credentials: true")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, persisted), "persisted credentials")
    no_positive = workflow.replace("branch: main", "branches: [main]")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, no_positive), "positive control neutralized")
    warn_only = workflow.replace(
        '"${ACTIONLINT_BIN}" "${targets[@]}"',
        '"${ACTIONLINT_BIN}" "${targets[@]}" || true',
    )
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, warn_only), "warn-only actionlint")
    no_diff = workflow.replace("git diff --name-only --diff-filter=ACMR", "git status --short")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, no_diff), "changed-file derivation removed")
    ignored = workflow.replace(
        '"${ACTIONLINT_BIN}" "${targets[@]}"',
        '"${ACTIONLINT_BIN}" -ignore ".*" "${targets[@]}"',
    )
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, ignored), "broad actionlint ignore")
    wrong_zizmor = workflow.replace(policy["zizmor"]["asset_sha256"], "0" * 64)
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, wrong_zizmor), "zizmor digest drift")
    online = workflow.replace("--offline --strict-collection", "--strict-collection")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, online), "zizmor offline removed")
    no_strict = workflow.replace("--offline --strict-collection --no-config", "--offline --no-config")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, no_strict), "zizmor strict collection removed")
    configured = workflow.replace("--no-config --format=json-v1", "--config zizmor.yml --format=json-v1")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, configured), "zizmor config enabled")
    tokenized = workflow + "\n# GITHUB_TOKEN\n"
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, tokenized), "zizmor token introduced")
    no_zizmor_positive = workflow.replace(
        'trigger = "pull_request" + "_target"',
        'trigger = "pull_request"',
    )
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, no_zizmor_positive), "zizmor positive control weakened")
    no_exit = workflow.replace("--format=json-v1", "--no-exit-codes --format=json-v1")
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_workflow(policy, no_exit), "zizmor exit codes disabled")

    no_filter = workflow.replace(
        "python scripts/governance/filter_zizmor_changed_findings.py",
        "python -c 'raise SystemExit(0)'",
    )
    _expect(
        mod.WorkflowSecurityError,
        lambda: mod.validate_workflow(policy, no_filter),
        "diff-local zizmor filter removed",
    )
    no_base = workflow.replace(
        "printf 'WORKFLOW_SECURITY_BASE=%s\\n' \"${base}\"",
        "printf 'REMOVED_WORKFLOW_SECURITY_BASE=%s\\n' \"${base}\"",
    )
    _expect(
        mod.WorkflowSecurityError,
        lambda: mod.validate_workflow(policy, no_base),
        "diff-base export removed",
    )
    no_base_consumer = workflow.replace(
        '--base "${WORKFLOW_SECURITY_BASE}"',
        '--base ""',
    )
    _expect(
        mod.WorkflowSecurityError,
        lambda: mod.validate_workflow(policy, no_base_consumer),
        "diff-base consumer removed",
    )
    unlocated = copy.deepcopy(policy)
    unlocated["scan_semantics"]["unlocated_findings_blocking"] = False
    _expect(
        mod.WorkflowSecurityError,
        lambda: mod.validate_policy(unlocated),
        "unlocated findings allowed",
    )

    paid = copy.deepcopy(policy)
    paid["cost_policy"]["paid_saas_required"] = True
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_policy(paid), "paid SaaS")
    broad = copy.deepcopy(policy)
    broad["scan_semantics"]["unchanged_legacy_blocking"] = True
    _expect(mod.WorkflowSecurityError, lambda: mod.validate_policy(broad), "legacy scope broadened")

    print("WORKFLOW_SECURITY_SELFTEST_PASS probes=22")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
