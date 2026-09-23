#!/usr/bin/env python3
"""Validate ENG-04.3 layered SAST controls without executing scanners."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "sast_control_policy_v1.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "security-sast.yml"
QUALITY_PATH = ROOT / ".github" / "workflows" / "code-quality.yml"


class SastControlError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SastControlError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SastControlError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise SastControlError("unsupported SAST policy schema_version")
    if policy.get("policy_kind") != "sast_control_policy_v1":
        raise SastControlError("invalid SAST policy kind")
    if policy.get("semantics") != "LAYERED_BANDIT_PLUS_PINNED_CODEQL_LOCAL_SARIF_GATE":
        raise SastControlError("SAST semantics drift")
    fast = policy.get("fast_sast")
    if not isinstance(fast, dict) or fast.get("version") != "1.8.0":
        raise SastControlError("Bandit version drift")
    if fast.get("command") != "bandit -q -r src -ll":
        raise SastControlError("Bandit fail-closed command drift")
    deep = policy.get("deep_sast")
    if not isinstance(deep, dict):
        raise SastControlError("deep SAST policy missing")
    expected = {
        "tag":"v4",
        "commit":"1c5b675653bb5c22dbe9b12b556ec555138e09fd",
        "license":"MIT",
        "default_bundle":"codeql-bundle-v2.27.0",
        "default_cli_version":"2.27.0",
        "language":"python",
        "queries":"security-extended",
        "source_root":"src/crypto_quant_bot",
        "upload":"never",
        "output":"codeql-results",
    }
    for key, value in expected.items():
        if deep.get(key) != value:
            raise SastControlError(f"deep SAST policy drift: {key}")
    checkout = policy.get("toolchain", {}).get("checkout_action_sha")
    if re.fullmatch(r"[0-9a-f]{40}", str(checkout or "")) is None:
        raise SastControlError("checkout action must be exact SHA")
    if policy.get("schedule") != {"cadence":"WEEKLY","cron":"37 4 * * 3"}:
        raise SastControlError("SAST schedule drift")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise SastControlError("mandatory SAST path must remain zero-cost")


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SastControlError(f"SAST workflow missing {label}: {needle}")


def validate_existing_bandit(policy: dict[str, Any], quality_text: str) -> None:
    fast = policy["fast_sast"]
    _require(quality_text, fast["command"], "existing Bandit gate")
    _require(quality_text, "python -m pip install -r requirements-dev.lock", "locked quality install")


def validate_workflow(policy: dict[str, Any], text: str) -> None:
    if "permissions:\n  contents: read\n" not in text:
        raise SastControlError("SAST workflow permissions must be contents: read only")
    for forbidden in (
        "security-events: write",
        "contents: write",
        "pull-requests: write",
        "permissions: write-all",
    ):
        if forbidden in text:
            raise SastControlError(f"forbidden SAST permission: {forbidden}")

    deep = policy["deep_sast"]
    pin = deep["action"] + "/" if False else "github/codeql-action/"
    action_ref = "@" + deep["commit"]
    if text.count("github/codeql-action/init" + action_ref) != 1:
        raise SastControlError("CodeQL init must use exact audited SHA once")
    if text.count("github/codeql-action/analyze" + action_ref) != 1:
        raise SastControlError("CodeQL analyze must use exact audited SHA once")
    tc = policy["toolchain"]
    _require(text, "actions/checkout@" + tc["checkout_action_sha"], "checkout exact SHA")
    _require(text, "persist-credentials: false", "disabled credential persistence")
    _require(text, "languages: " + deep["language"], "Python language")
    _require(text, "queries: " + deep["queries"], "security-extended suite")
    _require(text, "source-root: " + deep["source_root"], "production source root")
    _require(text, "upload: " + deep["upload"], "disabled SARIF upload")
    _require(text, "output: " + deep["output"], "local SARIF output")
    _require(text, 'Path("codeql-results").rglob("*.sarif")', "local SARIF parser")
    _require(text, 'raise SystemExit("CODEQL_SARIF_MISSING")', "missing SARIF fail-closed")
    _require(text, 'raise SystemExit("CODEQL_FINDINGS_DETECTED")', "finding fail-closed")
    _require(text, "CODEQL_SECURITY_EXTENDED_PASS", "zero-finding success marker")
    _require(text, 'cron: "37 4 * * 3"', "weekly schedule")
    _require(text, "workflow_dispatch:", "manual trigger")

    for item in (
        '"src/**/*.py"',
        '".github/workflows/security-sast.yml"',
        '"config/governance/sast_control_policy_v1.json"',
        '"scripts/governance/validate_sast_controls.py"',
    ):
        if text.count(item) < 2:
            raise SastControlError(f"SAST PR/push path filter missing: {item}")


def main() -> int:
    try:
        policy = _json(POLICY_PATH)
        validate_policy(policy)
        quality = QUALITY_PATH.read_text(encoding="utf-8")
        validate_existing_bandit(policy, quality)
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        validate_workflow(policy, workflow)
    except (SastControlError, OSError, KeyError) as exc:
        print(f"SAST_CONTROLS_INVALID: {exc}", file=sys.stderr)
        return 1
    print("SAST_CONTROLS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
