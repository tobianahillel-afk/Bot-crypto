#!/usr/bin/env python3
"""Offline final verification for ENG-04 security and supply-chain controls."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "security_engine_verification_policy_v1.json"
EVIDENCE_PATH = ROOT / "engineering" / "SECURITY_ENGINE_VERIFICATION.json"


class SecurityEngineError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecurityEngineError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SecurityEngineError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SecurityEngineError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SecurityEngineError(f"missing {label}: {needle}")


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise SecurityEngineError("unsupported security-engine policy schema_version")
    if policy.get("policy_kind") != "security_engine_verification_policy_v1":
        raise SecurityEngineError("invalid security-engine policy kind")
    if policy.get("semantics") != "ZERO_COST_RISK_PROPORTIONAL_FINAL_VERDICT":
        raise SecurityEngineError("security-engine verification semantics drift")
    workflows = policy.get("security_workflows")
    if not isinstance(workflows, list) or len(workflows) != 5 or len(workflows) != len(set(workflows)):
        raise SecurityEngineError("security workflow set must contain exactly five unique paths")
    scoped = policy.get("path_scoped_workflows")
    if not isinstance(scoped, list) or len(scoped) != 4 or not set(scoped) < set(workflows):
        raise SecurityEngineError("path-scoped workflow set drift")
    if policy.get("secret_workflow") not in workflows:
        raise SecurityEngineError("secret workflow missing from security workflow set")
    if policy.get("secret_weekly_cron") != "41 4 * * 1":
        raise SecurityEngineError("secret full-assurance schedule drift")
    costs = policy.get("cost_policy_files")
    if not isinstance(costs, list) or len(costs) != 7 or len(costs) != len(set(costs)):
        raise SecurityEngineError("cost policy file set drift")
    expected = policy.get("expected")
    required = {
        "engineering_verdict": "PASS_ENGINEERING_SECURITY",
        "business_unlock_status": "BUSINESS_UNLOCK_BLOCKED_EXTERNAL_PROTECTION",
        "blocking_finding_id": "BOOT-FINDING-001",
        "protection_status": "UNPROTECTED",
    }
    if expected != required:
        raise SecurityEngineError("final ENG-04 expected verdict drift")


def validate_zero_cost(policy: dict[str, Any]) -> None:
    for rel in policy["cost_policy_files"]:
        payload = _json(ROOT / rel)
        cost = payload.get("cost_policy")
        if not isinstance(cost, dict) or not cost:
            raise SecurityEngineError(f"cost policy missing: {rel}")
        enabled = sorted(key for key, value in cost.items() if value is not False)
        if enabled:
            raise SecurityEngineError(f"non-zero-cost control in {rel}: {enabled}")


def validate_secret_routing(text: str, policy: dict[str, Any]) -> None:
    for trigger in ("push:", "pull_request:", "schedule:", "workflow_dispatch:"):
        _require(text, trigger, f"secret trigger {trigger}")
    if "    paths:" in text:
        raise SecurityEngineError("secret scanning must remain universal and unfiltered by path")
    _require(text, f'cron: "{policy["secret_weekly_cron"]}"', "weekly full assurance cron")
    routine_if = "if: github.event_name == 'push' || github.event_name == 'pull_request'"
    assurance_if = "if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'"
    _require(text, "Resolve routine Git range", "routine range resolver")
    _require(text, "Scan introduced Git range", "routine range scan")
    if text.count(routine_if) < 2:
        raise SecurityEngineError("routine resolver and scan must both be push/PR only")
    _require(text, '--log-opts="${GITLEAKS_ROUTINE_LOG_OPTS}"', "Gitleaks exact range option")
    _require(text, "FULL_HISTORY_FALLBACK", "missing-base full-history fallback")
    _require(text, "Scan current repository tree\n        " + assurance_if, "scheduled current-tree assurance")
    _require(text, "Scan full Git history\n        " + assurance_if, "scheduled full-history assurance")
    _require(text, 'case "$' + '{GITHUB_EVENT_NAME}" in', "event-specific final gate")
    _require(text, 'test "$' + '{GITLEAKS_RANGE_STATUS}" = "0"', "routine range fail-closed gate")
    _require(text, 'test "$' + '{GITLEAKS_CURRENT_STATUS}" = "0"', "current-tree assurance gate")
    _require(text, 'test "$' + '{GITLEAKS_HISTORY_STATUS}" = "0"', "full-history assurance gate")
    _require(text, "fetch-depth: 0", "complete Git objects for exact ranges")


def validate_path_scoping(policy: dict[str, Any]) -> None:
    for rel in policy["path_scoped_workflows"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        _require(text, "pull_request:", f"{rel} pull_request trigger")
        _require(text, "push:", f"{rel} push trigger")
        if text.count("    paths:") < 2:
            raise SecurityEngineError(f"{rel} must path-scope both push and pull_request")


def validate_permissions_and_pins(policy: dict[str, Any]) -> None:
    permission = _module(
        "eng04_final_permission_audit",
        ROOT / "scripts" / "governance" / "audit_workflow_permissions.py",
    )
    supply = _module(
        "eng04_final_supply_audit",
        ROOT / "scripts" / "governance" / "audit_action_supply_chain.py",
    )
    permission_policy = _json(ROOT / policy["workflow_permission_policy"])
    supply_policy = _json(ROOT / policy["action_supply_chain_policy"])
    permission.validate_policy(permission_policy)
    supply.validate_policy(supply_policy)
    registry = supply.load_pin_registry(supply_policy)

    for rel in policy["security_workflows"]:
        path = ROOT / rel
        record = permission.parse_workflow(path)
        violations = permission._block_violations(record, permission_policy)
        if violations:
            raise SecurityEngineError(f"permission violations in {rel}: {violations}")
        result = supply.audit([path], supply_policy)
        blocked = supply.changed_gate(result, registry)
        if blocked:
            raise SecurityEngineError(f"action pin violations in {rel}: {blocked}")


def validate_protection(policy: dict[str, Any]) -> dict[str, Any]:
    status = _json(ROOT / policy["repository_protection_status"])
    if status.get("overall_status") != policy["expected"]["protection_status"]:
        raise SecurityEngineError("repository protection status drift")
    if status.get("business_unlock_allowed") is not False:
        raise SecurityEngineError("business unlock must remain denied while main is unprotected")
    if status.get("manual_admin_action_required") is not True:
        raise SecurityEngineError("manual repository-admin action must remain explicit")
    if status.get("blocking_finding_id") != policy["expected"]["blocking_finding_id"]:
        raise SecurityEngineError("repository protection blocker identity drift")
    return status


def build_result(policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    validate_zero_cost(policy)
    secret_text = (ROOT / policy["secret_workflow"]).read_text(encoding="utf-8")
    validate_secret_routing(secret_text, policy)
    validate_path_scoping(policy)
    validate_permissions_and_pins(policy)
    protection = validate_protection(policy)
    return {
        "schema_version": 1,
        "verification_kind": "eng04_security_engine_verification_v1",
        "verdict": policy["expected"]["engineering_verdict"],
        "business_unlock_status": policy["expected"]["business_unlock_status"],
        "blocking_finding_id": policy["expected"]["blocking_finding_id"],
        "zero_cost": True,
        "least_privilege": True,
        "approved_exact_action_pins": True,
        "risk_proportional": True,
        "security_workflows": sorted(policy["security_workflows"]),
        "path_scoped_workflows": sorted(policy["path_scoped_workflows"]),
        "secret_routing": {
            "routine_events": ["pull_request", "push"],
            "assurance_events": ["schedule", "workflow_dispatch"],
            "weekly_cron": policy["secret_weekly_cron"],
            "missing_base_fallback": "FULL_HISTORY_FALLBACK",
        },
        "external_protection": {
            "overall_status": protection["overall_status"],
            "business_unlock_allowed": protection["business_unlock_allowed"],
            "manual_admin_action_required": protection["manual_admin_action_required"],
        },
    }


def check_evidence(result: dict[str, Any]) -> None:
    evidence = _json(EVIDENCE_PATH)
    if evidence != result:
        raise SecurityEngineError("committed ENG-04 verification evidence does not match current controls")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-evidence", action="store_true")
    args = parser.parse_args()
    try:
        policy = _json(POLICY_PATH)
        result = build_result(policy)
        if args.check_evidence:
            check_evidence(result)
    except (SecurityEngineError, OSError, KeyError) as exc:
        print(f"SECURITY_ENGINE_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
