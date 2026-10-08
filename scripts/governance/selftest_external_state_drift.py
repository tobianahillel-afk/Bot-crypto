#!/usr/bin/env python3
"""Adversarial qualification for permanent external Git state-drift detection."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "verify_external_git_state.py"
    spec = importlib.util.spec_from_file_location("external_git_state_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _state() -> dict[str, Any]:
    value = json.loads(
        (ROOT / "config/governance/project_state.json").read_text(encoding="utf-8")
    )
    if not isinstance(value, dict):
        raise RuntimeError("project state must be an object")
    return value


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"drift scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    state = _state()
    expected = copy.deepcopy(state["external_observations"])
    mod.compare_observations(state, expected)

    main_moved = copy.deepcopy(expected)
    main_moved["main"]["sha"] = "0" * 40
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(state, main_moved),
        "main head moved",
    )

    protection_changed = copy.deepcopy(expected)
    protection_changed["main"]["branch_protected"] = not expected["main"]["branch_protected"]
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(state, protection_changed),
        "main protection changed",
    )

    rules_changed = copy.deepcopy(expected)
    rules_changed["rulesets_count"] = expected["rulesets_count"] + 1
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(state, rules_changed),
        "ruleset count changed",
    )

    pr_head_moved = copy.deepcopy(expected)
    pr_head_moved["business_candidate"]["head"] = "1" * 40
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(state, pr_head_moved),
        "candidate head moved",
    )

    pr_closed = copy.deepcopy(expected)
    pr_closed["business_candidate"]["state"] = "closed"
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(state, pr_closed),
        "candidate state changed",
    )

    pr_merged = copy.deepcopy(expected)
    pr_merged["business_candidate"]["merged"] = True
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(state, pr_merged),
        "candidate merge status changed",
    )

    unsafe_state = copy.deepcopy(state)
    unsafe_state["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        mod.StateDriftError,
        lambda: mod.compare_observations(unsafe_state, expected),
        "Lot46 unlock",
    )

    print("EXTERNAL_STATE_DRIFT_SELFTEST_PASS probes=7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
