#!/usr/bin/env python3
"""Negative self-tests for governance validators."""

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
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain an object")
    return value


def _expect_failure(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"negative probe unexpectedly passed: {label}")


def main() -> int:
    state_mod = _module("state_validator", ROOT / "scripts/governance/validate_bootstrap_state.py")
    item_mod = _module("item_validator", ROOT / "scripts/governance/validate_work_item.py")
    handoff_mod = _module("handoff_validator", ROOT / "scripts/governance/validate_handoff.py")

    state = _json(ROOT / "engineering/STATE.json")
    permanent_state = _json(ROOT / "config/governance/project_state.json")
    policy = _json(ROOT / "engineering/STATE_TRANSITIONS.json")
    phase = state["bootstrap_engine"]["phase"]
    engine = state["bootstrap_engine"] if phase == "BUILDING" else state["engineering_engine"]
    if engine.get("phase") in {"STABLE", "COMPLETE"}:
        state_manifest = None
        work_manifest = _json(ROOT / "engineering/lots/ENG-09.json")
    else:
        declared_manifest = engine.get("active_manifest")
        if not isinstance(declared_manifest, str):
            raise AssertionError("building lifecycle requires engineering active_manifest")
        state_manifest = _json(ROOT / declared_manifest)
        work_manifest = state_manifest
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")

    state_mod.validate_state(state, policy, state_manifest)
    item_mod.validate_manifest(work_manifest, source=work_manifest["id"])
    handoff_mod.validate_handoff(permanent_state, handoff)

    unsafe_state = copy.deepcopy(state)
    unsafe_state["safety"]["trade_allowed"] = True
    _expect_failure(
        state_mod.BootstrapStateError,
        lambda: state_mod.validate_state(unsafe_state, policy, state_manifest),
        "unsafe state",
    )

    invalid_prefix = copy.deepcopy(state)
    invalid_prefix["bootstrap_engine"]["completed"] = invalid_prefix["bootstrap_engine"]["completed"][:-1]
    _expect_failure(
        state_mod.BootstrapStateError,
        lambda: state_mod.validate_state(invalid_prefix, policy, state_manifest),
        "bootstrap completed prefix",
    )

    invalid_manifest = copy.deepcopy(work_manifest)
    invalid_manifest["status"] = "DONE"
    if engine.get("phase") in {"STABLE", "COMPLETE"}:
        invalid_manifest["tasks"][-1]["status"] = "PLANNED"
    _expect_failure(
        item_mod.WorkItemError,
        lambda: item_mod.validate_manifest(invalid_manifest, source="negative-manifest"),
        "DONE item with unfinished tasks",
    )

    stale_handoff = copy.deepcopy(handoff)
    stale_handoff["state_snapshot"]["engineering_phase"] = "CORRUPT"
    _expect_failure(
        handoff_mod.HandoffError,
        lambda: handoff_mod.validate_handoff(permanent_state, stale_handoff),
        "stale handoff",
    )

    if engine.get("phase") in {"STABLE", "COMPLETE"}:
        terminal_engine_active = copy.deepcopy(state)
        terminal_engine_active["engineering_engine"]["active_lot"] = "ENG-99"
        _expect_failure(
            state_mod.BootstrapStateError,
            lambda: state_mod.validate_state(
                terminal_engine_active,
                policy,
                work_manifest,
            ),
            "terminal engineering active lot",
        )

    print("GOVERNANCE_VALIDATOR_SELFTEST_PASS probes=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
