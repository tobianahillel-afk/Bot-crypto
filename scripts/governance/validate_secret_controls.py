#!/usr/bin/env python3
"""Validate ENG-04.1 secret-control configuration without executing Gitleaks."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "secret_control_policy_v1.json"
CONFIG_PATH = ROOT / ".gitleaks.toml"


class SecretControlError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecretControlError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SecretControlError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise SecretControlError("unsupported secret-control policy schema_version")
    if policy.get("policy_kind") != "secret_control_policy_v1":
        raise SecretControlError("invalid secret-control policy kind")
    if policy.get("semantics") != "PINNED_MIT_GITLEAKS_REDACTED_FAIL_CLOSED":
        raise SecretControlError("secret-control semantics drift")
    gl = policy.get("gitleaks")
    if not isinstance(gl, dict):
        raise SecretControlError("gitleaks pin missing")
    if gl.get("tag") != "v8.30.1":
        raise SecretControlError("Gitleaks tag drift")
    if gl.get("commit") != "83d9cd684c87d95d656c1458ef04895a7f1cbd8e":
        raise SecretControlError("Gitleaks commit drift")
    if gl.get("version") != "8.30.1" or gl.get("license") != "MIT":
        raise SecretControlError("Gitleaks version/license drift")
    toolchain = policy.get("toolchain")
    if not isinstance(toolchain, dict):
        raise SecretControlError("toolchain pin missing")
    if toolchain.get("go_version") != "1.24.11":
        raise SecretControlError("Go version drift")
    for key in ("checkout_action_sha", "setup_go_action_sha"):
        value = toolchain.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise SecretControlError(f"{key} must be exact 40-hex SHA")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise SecretControlError("mandatory secret-control path must remain zero-cost")
    if policy.get("required_redaction_percent") != 100:
        raise SecretControlError("full redaction is mandatory")
    if policy.get("required_scans") != [
        "SYNTHETIC_POSITIVE_CONTROL", "CURRENT_TREE", "FULL_GIT_HISTORY"
    ]:
        raise SecretControlError("required scan set drift")


def validate_config(config_text: str) -> None:
    try:
        parsed = tomllib.loads(config_text)
    except tomllib.TOMLDecodeError as exc:
        raise SecretControlError(f"invalid .gitleaks.toml: {exc}") from exc
    extend = parsed.get("extend")
    if not isinstance(extend, dict) or extend.get("useDefault") is not True:
        raise SecretControlError("default Gitleaks rules must remain enabled")
    if "allowlist" in config_text.lower():
        raise SecretControlError("secret allowlists require separate finding-specific review")


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SecretControlError(f"workflow missing {label}: {needle}")


def validate_workflow(policy: dict[str, Any], workflow_text: str) -> None:
    for token in policy["forbidden_tokens"]:
        if token in workflow_text:
            raise SecretControlError(f"forbidden workflow token present: {token}")
    if "permissions:\n  contents: read\n" not in workflow_text:
        raise SecretControlError("workflow permissions must be contents: read only")
    toolchain = policy["toolchain"]
    _require(
        workflow_text,
        "actions/checkout@" + toolchain["checkout_action_sha"],
        "exact checkout pin",
    )
    _require(
        workflow_text,
        "actions/setup-go@" + toolchain["setup_go_action_sha"],
        "exact setup-go pin",
    )
    _require(workflow_text, 'go-version: "' + toolchain["go_version"] + '"', "exact Go version")
    gl = policy["gitleaks"]
    _require(workflow_text, 'GITLEAKS_TAG: "' + gl["tag"] + '"', "Gitleaks tag")
    _require(workflow_text, 'GITLEAKS_COMMIT: "' + gl["commit"] + '"', "Gitleaks commit")
    _require(
        workflow_text,
        'GITLEAKS_EXPECTED_VERSION: "' + gl["version"] + '"',
        "Gitleaks version",
    )
    _require(workflow_text, 'git -C "${src}" rev-parse HEAD', "source commit verification")
    _require(workflow_text, 'test "${actual}" = "${GITLEAKS_COMMIT}"', "commit equality check")
    _require(
        workflow_text,
        "github.com/zricethezav/gitleaks/v8/version.Version=${GITLEAKS_TAG}",
        "official version ldflags",
    )
    _require(workflow_text, "--redact=100", "full redaction")
    if workflow_text.count("--redact=100") < 3:
        raise SecretControlError("all three scans must use full redaction")
    _require(workflow_text, '"${GITLEAKS_BIN}" dir', "directory scan")
    _require(workflow_text, '"${GITLEAKS_BIN}" git', "Git history scan")
    _require(workflow_text, "--report-format json", "ephemeral JSON report")
    _require(workflow_text, "path.unlink(missing_ok=True)", "ephemeral report deletion")
    _require(workflow_text, "GITLEAKS_CURRENT_STATUS", "current-scan status binding")
    _require(workflow_text, "GITLEAKS_HISTORY_STATUS", "history-scan status binding")
    _require(workflow_text, "Enforce clean secret scans", "fail-closed final gate")
    for forbidden_field in ('finding.get("Secret")', 'finding.get("Match")'):
        if forbidden_field in workflow_text:
            raise SecretControlError("workflow must not print secret or match values")
    _require(workflow_text, "fetch-depth: 0", "full checkout history")
    _require(workflow_text, "persist-credentials: false", "credential persistence disabled")
    _require(workflow_text, 'token = "gh" + "p_" + suffix', "runtime-only positive control")
    _require(workflow_text, "for i in range(36)", "high-entropy synthetic suffix")
    if "ghp_" in workflow_text:
        raise SecretControlError("synthetic secret literal must not be committed")
    for trigger in ("push:", "pull_request:", "workflow_dispatch:"):
        _require(workflow_text, trigger, f"{trigger} trigger")


def validate_documents(policy: dict[str, Any], workflow_text: str, config_text: str) -> None:
    validate_policy(policy)
    validate_config(config_text)
    validate_workflow(policy, workflow_text)


def main() -> int:
    try:
        policy = _json(POLICY_PATH)
        workflow_path = ROOT / policy["workflow_path"]
        workflow_text = workflow_path.read_text(encoding="utf-8")
        config_text = CONFIG_PATH.read_text(encoding="utf-8")
        validate_documents(policy, workflow_text, config_text)
    except (SecretControlError, OSError, KeyError) as exc:
        print(f"SECRET_CONTROLS_INVALID: {exc}", file=sys.stderr)
        return 1
    print("SECRET_CONTROLS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
