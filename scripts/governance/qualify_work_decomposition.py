#!/usr/bin/env python3
"""End-to-end adversarial qualification for the work-decomposition/context engine."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain an object")
    return value


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"decomposition negative scenario unexpectedly passed: {label}")


def main() -> int:
    active_mod = _module("qual_active_awu", ROOT / "scripts/governance/resolve_active_awu.py")
    graph_mod = _module("qual_awu_graph", ROOT / "scripts/governance/validate_agent_work_unit_graph.py")
    split_mod = _module("qual_awu_split", ROOT / "scripts/governance/validate_awu_split.py")
    risk_mod = _module("qual_awu_risk", ROOT / "scripts/governance/validate_awu_risk.py")
    context_mod = _module("qual_awu_context", ROOT / "scripts/governance/validate_awu_context.py")
    diff_mod = _module("qual_awu_diff", ROOT / "scripts/governance/validate_bootstrap_diff.py")
    next_mod = _module("qual_next_work", ROOT / "scripts/governance/resolve_next_work.py")

    state = _json(ROOT / "config/governance/project_state.json")
    capabilities = _json(ROOT / "engineering/AGENT_CAPABILITIES.json")
    split_policy = _json(ROOT / "config/governance/awu_split_policy_v1.json")
    risk_policy = _json(ROOT / "config/governance/awu_risk_policy_v1.json")
    context_policy = _json(ROOT / "config/governance/awu_context_policy_v1.json")

    paths = sorted((ROOT / "engineering/work_units").glob("*.json"))
    units = graph_mod.load_paths(paths)
    topo = graph_mod.validate_graph(units)
    awu_path, active, evidence = active_mod.resolve_active_awu()
    assert active["id"] in topo
    for dependency in active["depends_on"]:
        assert topo.index(dependency) < topo.index(active["id"])

    resolved = next_mod.resolve(
        state,
        capabilities,
        "GITHUB_CONNECTOR_ONLY",
        "engineering",
        (awu_path, active, evidence),
    )
    assert resolved["active_awu"]["id"] == active["id"]
    assert resolved["active_awu"]["path"] in resolved["required_read_order"]

    oversized = copy.deepcopy(active)
    oversized["planning"]["size_estimate"]["files_touched"] = 16
    _expect(
        split_mod.AwuSplitError,
        lambda: split_mod.validate_split(oversized, split_policy),
        "oversized executable AWU",
    )

    missing = copy.deepcopy(units)
    missing[active["id"]]["depends_on"] = ["ENG-02.8-WU99"]
    _expect(
        graph_mod.AgentWorkUnitGraphError,
        lambda: graph_mod.validate_graph(missing),
        "missing dependency",
    )

    cycle = copy.deepcopy(units)
    predecessor = active["depends_on"][0]
    cycle[predecessor]["depends_on"] = [active["id"]]
    _expect(
        graph_mod.AgentWorkUnitGraphError,
        lambda: graph_mod.validate_graph(cycle),
        "dependency cycle",
    )

    incomplete = copy.deepcopy(units)
    incomplete[predecessor]["status"] = "IN_PROGRESS"
    _expect(
        graph_mod.AgentWorkUnitGraphError,
        lambda: graph_mod.validate_graph(incomplete),
        "incomplete predecessor",
    )

    unclassified = copy.deepcopy(active)
    unclassified["planning"]["risk_class"] = "UNCLASSIFIED"
    _expect(
        risk_mod.AwuRiskError,
        lambda: risk_mod.validate_risk(unclassified, risk_policy),
        "unclassified executable AWU",
    )

    overbudget = copy.deepcopy(active)
    overbudget["planning"]["context_budget"]["max_primary_files"] = 1
    _expect(
        context_mod.AwuContextError,
        lambda: context_mod.validate_context(overbudget, awu_path, context_policy),
        "forged context budget",
    )

    duplicate = active_mod.load_work_units()
    second = copy.deepcopy(active)
    second["id"] = "ENG-02.8-WU99"
    duplicate[ROOT / "engineering/work_units/qual-duplicate.json"] = second
    _expect(
        active_mod.ActiveAwuError,
        lambda: active_mod.select_active_awu(duplicate),
        "duplicate active AWU",
    )

    _expect(
        diff_mod.DiffScopeError,
        lambda: diff_mod.validate_scope(
            ["docs/outside-awu.md"],
            active["scope"]["allowed_paths"],
            active["scope"]["forbidden_paths"],
            evidence["parent_manifest"]["allowed_paths"],
        ),
        "out-of-scope diff",
    )

    print(
        "WORK_DECOMPOSITION_QUALIFICATION_PASS "
        f"awu={active['id']} nodes={len(units)} scenarios=8 "
        f"context=P{evidence['context_route']['primary_count']}:"
        f"R{evidence['context_route']['reference_count']}:"
        f"K{evidence['context_route']['total_kib_ceil']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
