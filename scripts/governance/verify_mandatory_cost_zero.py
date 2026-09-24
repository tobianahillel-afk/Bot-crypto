#!/usr/bin/env python3
"""Statically prove that the mandatory Development Engine path has no paid requirement."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "mandatory_cost_zero_policy_v1.json"

USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
RUNS_ON_RE = re.compile(r"^\s*runs-on:\s*([^\n#]+)", re.MULTILINE)
SECRET_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")
GITHUB_TOKEN_RE = re.compile(r"\$\{\{\s*github\.token\s*\}\}")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class MandatoryCostError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MandatoryCostError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MandatoryCostError(f"{path} must contain an object")
    return value


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MandatoryCostError(f"cannot read {path}: {exc}") from exc


def _all_false(label: str, mapping: Any) -> dict[str, bool]:
    if not isinstance(mapping, dict) or not mapping:
        raise MandatoryCostError(f"{label} must be a non-empty object")
    result: dict[str, bool] = {}
    for key, value in sorted(mapping.items()):
        if not isinstance(key, str) or not key:
            raise MandatoryCostError(f"{label} contains invalid key")
        if value is not False:
            raise MandatoryCostError(f"{label}.{key} must be boolean false, got {value!r}")
        result[key] = False
    return result


def _find_cost_policies(value: Any, path: tuple[str, ...] = ()) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = path + (str(key),)
            if key == "cost_policy":
                if not isinstance(child, dict):
                    raise MandatoryCostError(f"{'.'.join(child_path)} must be an object")
                found.append((".".join(child_path), child))
            found.extend(_find_cost_policies(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_cost_policies(child, path + (str(index),)))
    return found


def _action_repository(action_ref: str) -> tuple[str, str]:
    if action_ref.startswith("./"):
        return "LOCAL", action_ref
    if action_ref.startswith("docker://"):
        raise MandatoryCostError(f"docker action is not statically approved: {action_ref}")
    if "@" not in action_ref:
        raise MandatoryCostError(f"remote action lacks exact ref: {action_ref}")
    action_path, ref = action_ref.rsplit("@", 1)
    parts = action_path.split("/")
    if len(parts) < 2:
        raise MandatoryCostError(f"invalid remote action reference: {action_ref}")
    return "/".join(parts[:2]), ref


def _approved_pins(registry: dict[str, Any]) -> dict[str, set[str]]:
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise MandatoryCostError("action pin registry entries missing")
    approved: dict[str, set[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise MandatoryCostError("action pin registry entry must be object")
        repository = entry.get("repository")
        if not isinstance(repository, str) or not repository:
            raise MandatoryCostError("action pin registry repository invalid")
        if entry.get("public") is not True or entry.get("license") != "MIT":
            raise MandatoryCostError(f"mandatory action repository not public MIT: {repository}")
        pins = entry.get("approved_pins")
        if not isinstance(pins, list) or not pins:
            raise MandatoryCostError(f"no approved pins for action repository: {repository}")
        values: set[str] = set()
        for pin in pins:
            if not isinstance(pin, dict):
                raise MandatoryCostError(f"invalid approved pin for {repository}")
            sha = pin.get("approved_commit_sha")
            if not isinstance(sha, str) or SHA40_RE.fullmatch(sha) is None:
                raise MandatoryCostError(f"invalid approved commit SHA for {repository}")
            values.add(sha)
        approved[repository] = values
    return approved


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise MandatoryCostError("unsupported mandatory-cost policy schema_version")
    if policy.get("policy_kind") != "mandatory_cost_zero_policy_v1":
        raise MandatoryCostError("invalid mandatory-cost policy kind")
    if policy.get("semantics") != "STATIC_ZERO_PAID_REQUIREMENTS_WITH_VISIBILITY_UNVERIFIED":
        raise MandatoryCostError("mandatory-cost policy semantics drift")
    workflows = policy.get("mandatory_workflows")
    if not isinstance(workflows, list) or len(workflows) != 6 or len(workflows) != len(set(workflows)):
        raise MandatoryCostError("mandatory workflow set must contain exactly six unique workflows")
    if policy.get("allowed_runner_labels") != ["ubuntu-latest"]:
        raise MandatoryCostError("runner allowlist drift")
    visibility = policy.get("visibility_binding")
    if not isinstance(visibility, dict):
        raise MandatoryCostError("visibility binding missing")
    if visibility.get("wu01_repository_visibility") != "UNVERIFIED":
        raise MandatoryCostError("WU01 must keep repository visibility UNVERIFIED")
    if visibility.get("total_runner_cost_claim_allowed") is not False:
        raise MandatoryCostError("WU01 must not make total runner cost claim")
    if visibility.get("wu02_requires_public_repository_evidence") is not True:
        raise MandatoryCostError("WU02 public-repository evidence requirement missing")
    if policy.get("expected_static_verdict") != "PASS_WITH_VISIBILITY_UNVERIFIED":
        raise MandatoryCostError("static verdict drift")
    allowlist = policy.get("zero_cost_action_allowlist")
    if not isinstance(allowlist, dict) or not allowlist:
        raise MandatoryCostError("zero-cost action allowlist missing")
    for repository, classification in allowlist.items():
        if not isinstance(classification, dict):
            raise MandatoryCostError(f"zero-cost action classification invalid: {repository}")
        if classification.get("paid_secret_required") is not False:
            raise MandatoryCostError(f"paid secret unexpectedly required: {repository}")
        if classification.get("paid_service_required") is not False:
            raise MandatoryCostError(f"paid service unexpectedly required: {repository}")


def _validate_cost_policies(policy: dict[str, Any]) -> list[dict[str, Any]]:
    state = _json(ROOT / policy["project_state"])
    capabilities = _json(ROOT / policy["agent_capabilities"])
    evidence: list[dict[str, Any]] = []
    evidence.append({
        "path": policy["project_state"],
        "binding": "cost_policy",
        "values": _all_false("project_state.cost_policy", state.get("cost_policy")),
    })
    evidence.append({
        "path": policy["agent_capabilities"],
        "binding": "mandatory_cost_policy",
        "values": _all_false(
            "agent_capabilities.mandatory_cost_policy",
            capabilities.get("mandatory_cost_policy"),
        ),
    })

    files = policy.get("governance_cost_policy_files")
    if not isinstance(files, list) or not files:
        raise MandatoryCostError("governance cost policy file set missing")
    for rel in files:
        doc = _json(ROOT / rel)
        found = _find_cost_policies(doc)
        if not found:
            raise MandatoryCostError(f"no cost_policy object found in {rel}")
        for dotted, values in found:
            evidence.append({
                "path": rel,
                "binding": dotted,
                "values": _all_false(f"{rel}:{dotted}", values),
            })
    return evidence


def _validate_security_policy_binding(policy: dict[str, Any]) -> None:
    source = _json(ROOT / policy["source_security_policy"])
    security = source.get("security_workflows")
    expected = policy["mandatory_workflows"][1:]
    if security != expected:
        raise MandatoryCostError(
            f"security workflow binding drift: expected {expected}, got {security}"
        )
    cost_files = source.get("cost_policy_files")
    if cost_files != policy["governance_cost_policy_files"]:
        raise MandatoryCostError("security-engine cost policy file binding drift")
    if source.get("action_pin_registry") != policy["action_pin_registry"]:
        raise MandatoryCostError("security-engine action pin registry binding drift")


def _validate_workflows(policy: dict[str, Any]) -> list[dict[str, Any]]:
    registry = _json(ROOT / policy["action_pin_registry"])
    approved = _approved_pins(registry)
    zero_cost = policy["zero_cost_action_allowlist"]
    allowed_runners = set(policy["allowed_runner_labels"])
    forbidden_runner_markers = [x.lower() for x in policy["forbidden_runner_markers"]]
    forbidden_secrets = set(policy["forbidden_secret_names"])
    inventory: list[dict[str, Any]] = []

    for rel in policy["mandatory_workflows"]:
        text = _text(ROOT / rel)
        runners = [match.group(1).strip().strip("'\"") for match in RUNS_ON_RE.finditer(text)]
        if not runners:
            raise MandatoryCostError(f"mandatory workflow has no runs-on declaration: {rel}")
        for runner in runners:
            lower = runner.lower()
            if runner not in allowed_runners:
                raise MandatoryCostError(f"runner not allowed in {rel}: {runner}")
            if any(marker in lower for marker in forbidden_runner_markers):
                raise MandatoryCostError(f"forbidden runner marker in {rel}: {runner}")

        secret_names = sorted(set(SECRET_RE.findall(text)))
        if secret_names:
            raise MandatoryCostError(f"repository secrets forbidden on mandatory path {rel}: {secret_names}")
        for name in forbidden_secrets:
            if name in text:
                raise MandatoryCostError(f"forbidden paid credential marker in {rel}: {name}")

        action_records: list[dict[str, str]] = []
        for action_ref in USES_RE.findall(text):
            repository, ref = _action_repository(action_ref)
            if repository == "LOCAL":
                action_records.append({"reference": action_ref, "repository": "LOCAL", "pin": "LOCAL"})
                continue
            if SHA40_RE.fullmatch(ref) is None:
                raise MandatoryCostError(f"mandatory action is not exact-SHA pinned: {action_ref}")
            if repository not in zero_cost:
                raise MandatoryCostError(f"action repository missing zero-cost classification: {repository}")
            if repository not in approved or ref not in approved[repository]:
                raise MandatoryCostError(f"action pin not approved by registry: {action_ref}")
            action_records.append({"reference": action_ref, "repository": repository, "pin": ref})

        inventory.append({
            "path": rel,
            "runners": sorted(set(runners)),
            "actions": action_records,
            "repository_secret_refs": secret_names,
            "github_token_refs": len(GITHUB_TOKEN_RE.findall(text)),
        })
    return inventory


def static_audit(policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    _validate_security_policy_binding(policy)
    cost_evidence = _validate_cost_policies(policy)
    workflow_inventory = _validate_workflows(policy)
    remote_actions = sorted({
        record["repository"]
        for workflow in workflow_inventory
        for record in workflow["actions"]
        if record["repository"] != "LOCAL"
    })
    return {
        "schema_version": 1,
        "audit_kind": "mandatory_cost_zero_static_v1",
        "verdict": policy["expected_static_verdict"],
        "mandatory_workflow_count": len(workflow_inventory),
        "mandatory_workflows": workflow_inventory,
        "cost_policy_bindings": cost_evidence,
        "remote_action_repositories": remote_actions,
        "allowed_runner_labels": policy["allowed_runner_labels"],
        "repository_visibility": "UNVERIFIED",
        "github_hosted_runner_cost": "UNVERIFIED",
        "total_mandatory_execution_cost_claim": "NOT_MADE_IN_WU01",
        "paid_external_api_required": False,
        "paid_llm_required": False,
        "paid_saas_required": False,
        "paid_license_required": False,
        "paid_runner_required_by_configuration": False,
        "billing_api_queried": False,
        "network_required_by_auditor": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    if not args.static:
        print("MANDATORY_COST_INVALID: --static is required", file=sys.stderr)
        return 2
    try:
        result = static_audit(_json(POLICY_PATH))
    except (MandatoryCostError, KeyError, TypeError) as exc:
        print(f"MANDATORY_COST_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
