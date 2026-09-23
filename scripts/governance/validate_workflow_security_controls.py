#!/usr/bin/env python3
"""Validate ENG-04.4 WU01 actionlint workflow controls."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "workflow_security_policy_v1.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "security-actions.yml"


class WorkflowSecurityError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowSecurityError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowSecurityError(f"{path} must contain an object")
    return value


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise WorkflowSecurityError(f"missing {label}: {needle}")


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise WorkflowSecurityError("unsupported workflow-security policy version")
    if policy.get("policy_kind") != "workflow_security_policy_v1":
        raise WorkflowSecurityError("invalid workflow-security policy kind")
    if policy.get("semantics") != "CHANGED_WORKFLOW_ACTIONLINT_FAIL_CLOSED_V1":
        raise WorkflowSecurityError("workflow-security semantics drift")
    actionlint = policy.get("actionlint")
    if not isinstance(actionlint, dict):
        raise WorkflowSecurityError("actionlint policy missing")
    expected = {
        "repository":"rhysd/actionlint",
        "tag":"v1.7.12",
        "commit":"914e7df21a07ef503a81201c76d2b11c789d3fca",
        "version":"1.7.12",
        "license":"MIT",
        "asset_name":"actionlint_1.7.12_linux_amd64.tar.gz",
        "asset_url":"https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz",
        "asset_sha256":"8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8",
    }
    for key, value in expected.items():
        if actionlint.get(key) != value:
            raise WorkflowSecurityError(f"actionlint policy drift: {key}")
    checkout = policy.get("toolchain", {}).get("checkout_action_sha")
    if checkout != "3d3c42e5aac5ba805825da76410c181273ba90b1":
        raise WorkflowSecurityError("checkout action pin drift")
    if re.fullmatch(r"[0-9a-f]{40}", str(checkout)) is None:
        raise WorkflowSecurityError("checkout action must be exact SHA")
    if policy.get("changed_target_globs") != [
        ".github/workflows/**/*.yml",
        ".github/workflows/**/*.yaml",
    ]:
        raise WorkflowSecurityError("changed workflow target globs drift")
    if policy.get("scan_semantics", {}).get("unchanged_legacy_blocking") is not False:
        raise WorkflowSecurityError("legacy unchanged workflows must not become WU01 blockers")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise WorkflowSecurityError("mandatory workflow-security path must remain zero-cost")


def validate_workflow(policy: dict[str, Any], text: str) -> None:
    if "permissions:\n  contents: read\n" not in text:
        raise WorkflowSecurityError("workflow must use contents: read only")
    for forbidden in (
        "permissions: write-all",
        "contents: write",
        "pull-requests: write",
        "security-events: write",
        "continue-on-error: true",
        "|| true",
        "-ignore ",
        "-ignore=",
    ):
        if forbidden in text:
            raise WorkflowSecurityError(f"forbidden workflow weakening token: {forbidden}")
    checkout = policy["toolchain"]["checkout_action_sha"]
    actionlint = policy["actionlint"]
    _require(text, "actions/checkout@" + checkout, "exact checkout action")
    _require(text, "fetch-depth: 0", "full Git history")
    _require(text, "persist-credentials: false", "disabled checkout credentials")
    _require(text, actionlint["asset_sha256"], "actionlint asset SHA-256")
    _require(text, actionlint["asset_name"], "actionlint exact asset")
    _require(
        text,
        "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/${ACTIONLINT_ASSET}",
        "exact release URL template",
    )
    _require(text, "sha256sum --check --strict", "asset digest verification")
    _require(text, '"${bin_dir}/actionlint" -version', "actionlint version verification")
    _require(text, "Prove actionlint rejects malformed workflow", "positive control")
    _require(text, "branch: main", "malformed positive-control key")
    _require(text, 'if [ "${status}" -eq 0 ]; then', "positive-control failure enforcement")
    _require(text, "git diff --name-only --diff-filter=ACMR", "changed-file discovery")
    _require(text, "git merge-base", "pull-request merge-base semantics")
    _require(text, "git ls-files", "root fallback")
    _require(text, '"${ACTIONLINT_BIN}" "${targets[@]}"', "fail-closed real actionlint execution")
    for trigger_path in policy["trigger_paths"]:
        if trigger_path not in text:
            raise WorkflowSecurityError(f"workflow trigger path missing: {trigger_path}")
    for glob in policy["changed_target_globs"]:
        if glob not in text:
            raise WorkflowSecurityError(f"changed target glob missing: {glob}")


def main() -> int:
    try:
        policy = _json(POLICY_PATH)
        validate_policy(policy)
        validate_workflow(policy, WORKFLOW_PATH.read_text(encoding="utf-8"))
    except (WorkflowSecurityError, OSError, KeyError) as exc:
        print(f"WORKFLOW_SECURITY_INVALID: {exc}", file=sys.stderr)
        return 1
    print("WORKFLOW_SECURITY_VALID_ACTIONLINT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
