#!/usr/bin/env python3
"""Execute conditional bounded T2 domain tests from T1-uncovered impacts."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "validation_t2_policy_v1.json"


class T2Error(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise T2Error(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise T2Error(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise T2Error(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _known_impact_families() -> set[str]:
    impact = _json(ROOT / "config" / "governance" / "diff_impact_policy_v1.json")
    families = impact.get("impact_families")
    if not isinstance(families, list):
        raise T2Error("impact policy families invalid")
    return set(families)


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise T2Error("unsupported T2 policy schema_version")
    if policy.get("policy_kind") != "validation_t2_policy_v1":
        raise T2Error("invalid T2 policy kind")
    if policy.get("semantics") != "CONDITIONAL_BOUNDED_DOMAIN_TESTS":
        raise T2Error("T2 semantics drift")

    group_ids = policy.get("group_ids")
    groups = policy.get("groups")
    if not isinstance(group_ids, list) or len(group_ids) != len(set(group_ids)):
        raise T2Error("T2 group ids must be unique")
    if not isinstance(groups, dict) or set(groups) != set(group_ids):
        raise T2Error("T2 groups must exactly match group_ids")

    for group_id, spec in groups.items():
        if not isinstance(spec, dict) or set(spec) != {"mode", "keywords"}:
            raise T2Error(f"invalid T2 group spec: {group_id}")
        if spec["mode"] not in {"KEYWORDS", "CHANGED_SOURCE_TOKENS"}:
            raise T2Error(f"invalid T2 group mode: {group_id}")
        keywords = spec["keywords"]
        if not isinstance(keywords, list) or any(
            not isinstance(x, str) or not x for x in keywords
        ):
            raise T2Error(f"invalid T2 keywords: {group_id}")
        if spec["mode"] == "KEYWORDS" and not keywords:
            raise T2Error(f"keyword T2 group has no keywords: {group_id}")
        if spec["mode"] == "CHANGED_SOURCE_TOKENS" and keywords:
            raise T2Error(f"changed-source T2 group must derive tokens dynamically: {group_id}")

    mapping = policy.get("impact_to_groups")
    impacts = _known_impact_families()
    if not isinstance(mapping, dict) or set(mapping) != impacts:
        raise T2Error("T2 must explicitly map every impact family")
    for impact, selected in mapping.items():
        if not isinstance(selected, list) or len(selected) != len(set(selected)):
            raise T2Error(f"invalid T2 groups for impact {impact}")
        unknown = sorted(set(selected) - set(group_ids))
        if unknown:
            raise T2Error(f"impact {impact} references unknown T2 groups: {unknown}")

    per_group = policy.get("max_targets_per_group")
    total = policy.get("max_total_targets")
    timeout = policy.get("pytest_timeout_seconds")
    if not isinstance(per_group, int) or not 1 <= per_group <= 100:
        raise T2Error("invalid T2 per-group target cap")
    if not isinstance(total, int) or not per_group <= total <= 200:
        raise T2Error("invalid T2 total target cap")
    if not isinstance(timeout, int) or not 10 <= timeout <= 600:
        raise T2Error("invalid T2 pytest timeout")


def select_groups(t1_result: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if t1_result.get("t1_version") != 1:
        raise T2Error("T2 requires T1 version 1")
    if t1_result.get("full_suite_executed") is not False:
        raise T2Error("T1 prerequisite unexpectedly ran full suite")
    uncovered = t1_result.get("uncovered_impacts")
    if not isinstance(uncovered, list):
        raise T2Error("T1 uncovered impacts missing")

    groups: set[str] = set()
    remaining: set[str] = set()
    covered: set[str] = set()
    for impact in sorted(set(uncovered)):
        if impact not in policy["impact_to_groups"]:
            raise T2Error(f"T1 emitted unknown impact family: {impact}")
        mapped = policy["impact_to_groups"][impact]
        if mapped:
            groups.update(mapped)
            covered.add(impact)
        else:
            remaining.add(impact)
    return {
        "selected_groups": sorted(groups),
        "t2_covered_impacts": sorted(covered),
        "remaining_uncovered_impacts": sorted(remaining),
    }


def _all_test_files(root: Path = ROOT) -> list[str]:
    tests = root / "tests"
    if not tests.is_dir():
        raise T2Error(f"tests directory missing: {tests}")
    return sorted(
        path.relative_to(root).as_posix()
        for path in tests.rglob("test_*.py")
        if path.is_file()
    )


def _changed_source_tokens(changed_paths: list[str]) -> set[str]:
    stop = {
        "src","crypto","quant","bot","crypto_quant_bot","python","test","tests",
        "impl","models","model","validation","policy","engine"
    }
    tokens: set[str] = set()
    for path in changed_paths:
        if not path.startswith("src/crypto_quant_bot/") or not path.endswith(".py"):
            continue
        for part in Path(path).parts[2:]:
            stem = part[:-3] if part.endswith(".py") else part
            for token in re.split(r"[^a-zA-Z0-9]+", stem.lower()):
                if len(token) >= 4 and token not in stop:
                    tokens.add(token)
    return tokens


def discover_group_targets(
    group_id: str,
    spec: dict[str, Any],
    test_files: list[str],
    changed_paths: list[str],
) -> list[str]:
    if spec["mode"] == "KEYWORDS":
        keywords = {x.lower() for x in spec["keywords"]}
    else:
        keywords = _changed_source_tokens(changed_paths)
    if not keywords:
        return []
    return sorted({
        path for path in test_files
        if any(keyword in path.lower() for keyword in keywords)
    })


def plan_targets(
    selected_groups: list[str],
    policy: dict[str, Any],
    changed_paths: list[str],
    test_files: list[str] | None = None,
) -> dict[str, Any]:
    if not selected_groups:
        return {"group_targets": {}, "pytest_targets": []}
    available = _all_test_files() if test_files is None else sorted(set(test_files))
    group_targets: dict[str, list[str]] = {}
    union: set[str] = set()

    for group_id in selected_groups:
        if group_id not in policy["groups"]:
            raise T2Error(f"unknown selected T2 group: {group_id}")
        targets = discover_group_targets(
            group_id, policy["groups"][group_id], available, changed_paths
        )
        if not targets:
            raise T2Error(f"selected T2 group discovered zero test targets: {group_id}")
        if len(targets) > policy["max_targets_per_group"]:
            raise T2Error(
                f"T2 group {group_id} exceeds target cap: "
                f"{len(targets)} > {policy['max_targets_per_group']}"
            )
        group_targets[group_id] = targets
        union.update(targets)

    if len(union) > policy["max_total_targets"]:
        raise T2Error(
            f"T2 target union exceeds cap: {len(union)} > {policy['max_total_targets']}"
        )
    return {"group_targets": group_targets, "pytest_targets": sorted(union)}


def execute_pytest(targets: list[str], timeout_seconds: int) -> dict[str, Any]:
    if not targets:
        return {
            "pytest_invoked": False,
            "pytest_targets": [],
            "elapsed_ms": 0.0,
            "status": "SKIPPED_NO_T2_GROUP",
        }
    if importlib.util.find_spec("pytest") is None:
        raise T2Error("pytest is required because T2 selected explicit domain targets")
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *targets],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise T2Error(f"targeted T2 pytest timed out after {timeout_seconds}s") from exc
    elapsed = round((time.perf_counter() - started) * 1000, 3)
    if proc.returncode != 0:
        tail = (proc.stdout + "\n" + proc.stderr)[-6000:]
        raise T2Error(f"targeted T2 pytest failed:\n{tail}")
    return {
        "pytest_invoked": True,
        "pytest_targets": targets,
        "elapsed_ms": elapsed,
        "status": "PASS",
        "output_tail": (proc.stdout + "\n" + proc.stderr)[-2000:],
    }


def repository_run() -> dict[str, Any]:
    started = time.perf_counter()
    policy = _json(POLICY_PATH)
    validate_policy(policy)

    t1 = _module("t2_prerequisite_t1", ROOT / "scripts/governance/run_t1.py")
    try:
        t1_result = t1.repository_run()
    except t1.T1Error as exc:
        raise T2Error(f"T1 prerequisite failed: {exc}") from exc

    selection = select_groups(t1_result, policy)

    active = _module("t2_active_awu", ROOT / "scripts/governance/resolve_active_awu.py")
    t0 = _module("t2_t0_paths", ROOT / "scripts/governance/run_t0.py")
    try:
        _path, awu, _evidence = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise T2Error(str(exc)) from exc
    changes = t0.changed_files(awu["scope"]["scope_base_sha"])
    changed_paths = [change.path for change in changes]

    plan = plan_targets(selection["selected_groups"], policy, changed_paths)
    execution = execute_pytest(plan["pytest_targets"], policy["pytest_timeout_seconds"])

    remaining = selection["remaining_uncovered_impacts"]
    return {
        "t2_version": 1,
        "active_awu": awu["id"],
        "scope_base_sha": awu["scope"]["scope_base_sha"],
        **selection,
        **plan,
        "pytest": execution,
        "requires_deeper_validation": bool(remaining),
        "selected_validation_tiers": ["T0","T1","T2"],
        "completed_validation_tiers": ["T0","T1","T2"],
        "deeper_tiers_executed": [],
        "full_suite_executed": False,
        "network_used": False,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def main() -> int:
    try:
        result = repository_run()
    except T2Error as exc:
        print(f"T2_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
