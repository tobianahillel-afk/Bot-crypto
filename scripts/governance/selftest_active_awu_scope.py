#!/usr/bin/env python3
"""Adversarial qualification for active-AWU resolution and Git scope enforcement."""

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
    raise AssertionError(f"active-AWU negative scenario unexpectedly passed: {label}")


def main() -> int:
    resolver = _module(
        "active_awu_resolver_selftest", ROOT / "scripts/governance/resolve_active_awu.py"
    )
    diff = _module(
        "active_awu_diff_selftest", ROOT / "scripts/governance/validate_bootstrap_diff.py"
    )

    state = _json(ROOT / "config/governance/project_state.json")
    units = resolver.load_work_units()
    path, active = resolver.select_active_awu(units)
    evidence = resolver.validate_full_awu(state, path, active)
    assert evidence["context_route"] is not None

    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.select_active_awu({}),
        "missing active AWU",
    )

    duplicate = dict(units)
    second = copy.deepcopy(active)
    second["id"] = "ENG-02.7-WU99"
    duplicate[ROOT / "engineering/work_units/duplicate.json"] = second
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.select_active_awu(duplicate),
        "duplicate active AWU",
    )

    foreign = copy.deepcopy(active)
    current_task = state["engineering_track"]["active_task"]
    foreign_task = "ENG-02.1" if current_task != "ENG-02.1" else "ENG-02.2"
    foreign["parent"]["task_id"] = foreign_task
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.validate_parent_binding(state, path, foreign),
        "foreign parent task",
    )

    parent_escape = copy.deepcopy(active)
    parent_escape["scope"]["allowed_paths"].append("README.md")
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.validate_parent_binding(state, path, parent_escape),
        "AWU allowlist outside parent scope",
    )

    allowed = active["scope"]["allowed_paths"]
    forbidden = active["scope"]["forbidden_paths"]
    parent_allowed = evidence["parent_manifest"]["allowed_paths"]
    _expect(
        diff.DiffScopeError,
        lambda: diff.validate_scope(["README.md"], allowed, forbidden, parent_allowed),
        "diff outside AWU allowlist",
    )
    _expect(
        diff.DiffScopeError,
        lambda: diff.validate_scope(
            ["src/crypto_quant_bot/example.py"],
            allowed + ["src/crypto_quant_bot/**"],
            forbidden,
            parent_allowed + ["src/crypto_quant_bot/**"],
        ),
        "forbidden path",
    )
    _expect(
        diff.DiffScopeError,
        lambda: diff.resolve_scope_base("0" * 40),
        "unknown scope base",
    )

    print("ACTIVE_AWU_SCOPE_SELFTEST_PASS probes=7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
