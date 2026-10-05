#!/usr/bin/env python3
"""Adversarial qualification for terminal ENGINEERING -> BUSINESS cold-start routing."""

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


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"terminal-routing negative scenario unexpectedly passed: {label}")


def main() -> int:
    resolver = _module("terminal_route_resolver", ROOT / "scripts/governance/resolve_active_awu.py")
    context = _module("terminal_route_context", ROOT / "scripts/governance/render_context_map.py")
    state = json.loads(
        (ROOT / "config/governance/project_state.json").read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "config/governance/active_work_routing_policy_v1.json").read_text(
            encoding="utf-8"
        )
    )
    resolver.validate_routing_policy(policy)

    assert resolver.resolve_active_track(state, policy) == "BUSINESS"

    building = copy.deepcopy(state)
    building["engineering_track"]["phase"] = "BUILDING"
    building["engineering_track"]["active_lot"] = "ENG-09"
    building["engineering_track"]["active_task"] = "ENG-09.6"
    building["engineering_track"]["next_lot"] = "ENGINE_COMPLETE"
    building["engineering_track"]["active_manifest"] = "engineering/lots/ENG-09.json"
    building["business_track"]["development_status"] = "PAUSED"
    building["business_track"]["candidate"]["status"] = "SUSPENDED_CANDIDATE"
    building["authority"]["active_manifest"] = "engineering/lots/ENG-09.json"
    assert resolver.resolve_active_track(building, policy) == "ENGINEERING"

    terminal = copy.deepcopy(state)
    terminal["engineering_track"]["phase"] = "STABLE"
    for key in ("active_lot", "active_task", "next_lot", "active_manifest"):
        terminal["engineering_track"][key] = None
    terminal["business_track"]["development_status"] = "ACTIVE"
    terminal["business_track"]["candidate"]["status"] = "ACTIVE_CANDIDATE"
    terminal["business_track"]["candidate"]["state"] = "OPEN"
    terminal["business_track"]["candidate"]["merged"] = False
    terminal["business_track"]["next_lot"] = {"lot": 46, "status": "LOCKED"}
    terminal["authority"]["active_manifest"] = "business/lots/LOT-45.json"
    assert resolver.resolve_active_track(terminal, policy) == "BUSINESS"

    paused = copy.deepcopy(terminal)
    paused["business_track"]["development_status"] = "PAUSED"
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.resolve_active_track(paused, policy),
        "terminal engineering with paused business",
    )

    suspended = copy.deepcopy(terminal)
    suspended["business_track"]["candidate"]["status"] = "SUSPENDED_CANDIDATE"
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.resolve_active_track(suspended, policy),
        "suspended candidate",
    )

    unlocked_next = copy.deepcopy(terminal)
    unlocked_next["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.resolve_active_track(unlocked_next, policy),
        "Lot46 unlocked",
    )

    one = {
        Path("business/work_units/LOT-45.1-WU01.json"): {"status": "IN_PROGRESS"}
    }
    path, _awu = resolver.select_active_awu(one)
    assert path.as_posix().endswith("LOT-45.1-WU01.json")
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.select_active_awu({}),
        "zero active business AWUs",
    )
    two = dict(one)
    two[Path("business/work_units/LOT-45.1-WU02.json")] = {"status": "IN_PROGRESS"}
    _expect(
        resolver.ActiveAwuError,
        lambda: resolver.select_active_awu(two),
        "multiple active business AWUs",
    )

    business_awu = {
        "status": "IN_PROGRESS",
        "id": "LOT-45.1-WU01",
        "parent": {
            "work_item_id": "LOT-45",
            "task_id": "LOT-45.1",
            "manifest": "business/lots/LOT-45.json",
        },
        "planning": {"risk_class": "R2", "complexity_score": 6},
    }
    descriptor = context._active_descriptor(
        terminal,
        "business/work_units/LOT-45.1-WU01.json",
        business_awu,
        "BUSINESS",
    )
    assert descriptor["track"] == "BUSINESS"
    assert descriptor["lot"] == "LOT-45"

    wrong = copy.deepcopy(business_awu)
    wrong["parent"]["work_item_id"] = "LOT-46"
    _expect(
        context.ContextMapError,
        lambda: context._active_descriptor(
            terminal, "business/work_units/LOT-46.1-WU01.json", wrong, "BUSINESS"
        ),
        "business AWU candidate mismatch",
    )

    context._validate_handoff(
        {
            "next_engineering": {
                "active_lot": None,
                "active_task": None,
                "active_manifest": None,
            },
            "current_objective": "Resume Lot45",
            "next_action": "Execute bounded Lot45 remediation",
        },
        terminal["engineering_track"],
        "BUSINESS",
    )

    print("TERMINAL_BUSINESS_ROUTING_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
