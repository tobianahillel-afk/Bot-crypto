#!/usr/bin/env python3
"""Execute allowlisted T1 checks selected from T0 impact output."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "validation_t1_policy_v1.json"


class T1Error(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise T1Error(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise T1Error(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise T1Error(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _known_impact_families() -> set[str]:
    impact_policy = _json(ROOT / "config" / "governance" / "diff_impact_policy_v1.json")
    families = impact_policy.get("impact_families")
    if not isinstance(families, list):
        raise T1Error("impact policy families are invalid")
    return set(families)


def validate_policy(policy: dict[str, Any], known_checks: set[str]) -> None:
    if policy.get("schema_version") != 1:
        raise T1Error("unsupported T1 policy schema_version")
    if policy.get("policy_kind") != "validation_t1_policy_v1":
        raise T1Error("invalid T1 policy kind")
    if policy.get("semantics") != "ALLOWLISTED_IMPACT_TARGETED_CHECKS":
        raise T1Error("T1 semantics drift")

    check_ids = policy.get("check_ids")
    if not isinstance(check_ids, list) or set(check_ids) != known_checks:
        raise T1Error("T1 policy check_ids must exactly match hardcoded registry")

    mapping = policy.get("impact_to_checks")
    known_impacts = _known_impact_families()
    if not isinstance(mapping, dict) or set(mapping) != known_impacts:
        raise T1Error("T1 policy must explicitly map every impact family")
    for impact, checks in mapping.items():
        if not isinstance(checks, list) or len(checks) != len(set(checks)):
            raise T1Error(f"invalid T1 check list for {impact}")
        unknown = sorted(set(checks) - known_checks)
        if unknown:
            raise T1Error(f"impact {impact} references unknown T1 checks: {unknown}")

    sufficient = policy.get("t0_sufficient_impacts")
    if not isinstance(sufficient, list) or set(sufficient) != {"DOC_CONSISTENCY"}:
        raise T1Error("only DOC_CONSISTENCY may currently be T0-sufficient")


def select_checks(t0_result: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if t0_result.get("t0_version") != 1:
        raise T1Error("T1 requires T0 version 1")
    if t0_result.get("test_suite_executed") is not False:
        raise T1Error("T0 prerequisite unexpectedly executed a test suite")
    impact = t0_result.get("impact")
    if not isinstance(impact, dict):
        raise T1Error("T0 impact output missing")
    families = impact.get("impact_families")
    if not isinstance(families, list) or not families:
        raise T1Error("T0 impact families missing")

    selected: set[str] = set()
    covered: set[str] = set()
    uncovered: set[str] = set()
    sufficient = set(policy["t0_sufficient_impacts"])

    for family in sorted(set(families)):
        if family not in policy["impact_to_checks"]:
            raise T1Error(f"T0 emitted unknown impact family: {family}")
        checks = policy["impact_to_checks"][family]
        if checks:
            selected.update(checks)
            covered.add(family)
        elif family in sufficient:
            covered.add(family)
        else:
            uncovered.add(family)

    return {
        "selected_checks": sorted(selected),
        "covered_impacts": sorted(covered),
        "uncovered_impacts": sorted(uncovered),
    }


def _check_diff(base: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "diff", "--check", f"{base}...HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise T1Error(f"git diff --check failed: {proc.stdout}{proc.stderr}".strip())
    return {"detail": "git diff --check passed"}


def _check_governance_active_scope(_base: str) -> dict[str, Any]:
    active = _module("t1_active_awu_check", ROOT / "scripts/governance/resolve_active_awu.py")
    diff = _module("t1_active_diff_check", ROOT / "scripts/governance/validate_bootstrap_diff.py")
    try:
        awu_path, awu, evidence = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise T1Error(str(exc)) from exc
    scope = awu["scope"]
    base = diff.resolve_scope_base(scope["scope_base_sha"])
    files = diff.changed_files(base)
    try:
        diff.validate_scope(
            files,
            scope["allowed_paths"],
            scope["forbidden_paths"],
            evidence["parent_manifest"]["allowed_paths"],
        )
    except diff.DiffScopeError as exc:
        raise T1Error(str(exc)) from exc
    return {
        "detail": f"active AWU scope valid: {awu['id']}",
        "active_awu": awu["id"],
        "awu_path": str(awu_path.relative_to(ROOT)),
        "changed_files": len(files),
    }


def _check_selftest_entrypoints(_base: str) -> dict[str, Any]:
    t0 = _module("t1_t0_for_selftests", ROOT / "scripts/governance/run_t0.py")
    active = _module("t1_active_for_selftests", ROOT / "scripts/governance/resolve_active_awu.py")
    try:
        _path, awu, _evidence = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise T1Error(str(exc)) from exc
    changes = t0.changed_files(awu["scope"]["scope_base_sha"])
    inspected: list[str] = []
    for change in changes:
        path = change.path
        if change.status.startswith("D"):
            continue
        if not path.startswith("scripts/governance/selftest_") or not path.endswith(".py"):
            continue
        full = ROOT / path
        try:
            text = full.read_text(encoding="utf-8")
        except OSError as exc:
            raise T1Error(f"cannot read changed selftest {path}: {exc}") from exc
        if 'if __name__ == "__main__":' not in text:
            raise T1Error(f"changed selftest lacks main guard: {path}")
        if "PASS" not in text:
            raise T1Error(f"changed selftest lacks explicit PASS marker: {path}")
        inspected.append(path)
    return {"detail": "changed governance selftest entrypoints valid", "inspected": inspected}


CHECKS: dict[str, Callable[[str], dict[str, Any]]] = {
    "DIFF_CHECK": _check_diff,
    "GOVERNANCE_ACTIVE_SCOPE": _check_governance_active_scope,
    "SELFTEST_ENTRYPOINT_CHECK": _check_selftest_entrypoints,
}


def execute_checks(selected: list[str], base: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check_id in selected:
        func = CHECKS.get(check_id)
        if func is None:
            raise T1Error(f"unknown executable T1 check id: {check_id}")
        started = time.perf_counter()
        detail = func(base)
        results.append({
            "check_id": check_id,
            "status": "PASS",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            **detail,
        })
    return results


def repository_run() -> dict[str, Any]:
    started = time.perf_counter()
    policy = _json(POLICY_PATH)
    validate_policy(policy, set(CHECKS))

    t0 = _module("t1_prerequisite_t0", ROOT / "scripts/governance/run_t0.py")
    try:
        t0_result = t0.repository_run()
    except t0.T0Error as exc:
        raise T1Error(f"T0 prerequisite failed: {exc}") from exc

    selection = select_checks(t0_result, policy)
    base = t0_result["scope_base_sha"]
    executed = execute_checks(selection["selected_checks"], base)

    return {
        "t1_version": 1,
        "active_awu": t0_result["active_awu"],
        "scope_base_sha": base,
        "t0_elapsed_ms": t0_result["elapsed_ms"],
        **selection,
        "executed_checks": executed,
        "requires_deeper_validation": bool(selection["uncovered_impacts"]),
        "selected_validation_tiers": ["T0", "T1"],
        "completed_validation_tiers": ["T0", "T1"],
        "deeper_tiers_executed": [],
        "full_suite_executed": False,
        "network_used": False,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def main() -> int:
    try:
        result = repository_run()
    except T1Error as exc:
        print(f"T1_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
