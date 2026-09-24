#!/usr/bin/env python3
"""Adversarial qualification for ENG-08.1 routine validation timing budgets."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_validation_timing_budgets.py"
    spec = importlib.util.spec_from_file_location("timing_budget_selftest_target", path)
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
    raise AssertionError(f"timing-budget negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    incremental = mod._json(ROOT / policy["source_incremental_policy"])
    mod.validate_policy(policy, incremental)

    # 1: calibrated routine measurement passes.
    baseline = mod._routine(policy["calibration_reference"])
    assert mod.validate_measurement(baseline, policy)["status"] == "PASS"

    # 2: exact stage/total boundaries pass (budgets are inclusive).
    boundary = copy.deepcopy(baseline)
    boundary["stage_elapsed_ms"]["T0"] = policy["budgets_ms"]["T0"]
    boundary["stage_elapsed_ms"]["T1"] = policy["budgets_ms"]["T1"]
    boundary["stage_elapsed_ms"]["T2"] = policy["budgets_ms"]["T2"]
    boundary["elapsed_ms"] = policy["budgets_ms"]["TOTAL"]
    assert mod.validate_measurement(boundary, policy)["status"] == "PASS"

    # 3-6: each routine budget fails independently when exceeded.
    for key in ("T0", "T1", "T2"):
        slow = copy.deepcopy(baseline)
        slow["stage_elapsed_ms"][key] = policy["budgets_ms"][key] + 0.001
        _expect(
            mod.TimingBudgetError,
            lambda value=slow: mod.validate_measurement(value, policy),
            f"{key} over budget",
        )
    slow_total = copy.deepcopy(baseline)
    slow_total["elapsed_ms"] = policy["budgets_ms"]["TOTAL"] + 0.001
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_measurement(slow_total, policy),
        "TOTAL over budget",
    )

    # 7: missing measured stage fails closed.
    missing = copy.deepcopy(baseline)
    del missing["stage_elapsed_ms"]["T2"]
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_measurement(missing, policy),
        "missing T2 measurement",
    )

    # 8: negative measured time fails closed.
    negative = copy.deepcopy(baseline)
    negative["stage_elapsed_ms"]["T0"] = -1
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_measurement(negative, policy),
        "negative timing",
    )

    # 9: booleans are not accepted as numeric timings.
    boolean = copy.deepcopy(baseline)
    boolean["elapsed_ms"] = True
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_measurement(boolean, policy),
        "boolean timing",
    )

    # 10: wrong measurement schema/version fails closed.
    wrong_version = copy.deepcopy(baseline)
    wrong_version["incremental_validation_version"] = 2
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_measurement(wrong_version, policy),
        "wrong incremental version",
    )

    # 11: pytest-backed T2 is deliberately outside routine timing policy.
    pytest_backed = copy.deepcopy(baseline)
    pytest_backed["routine_path"] = False
    pytest_backed["pytest_invoked"] = True
    assert mod.validate_measurement(pytest_backed, policy) == {
        "status": "NOT_APPLICABLE",
        "reason": "PYTEST_BACKED_T2",
    }

    # 12: another non-routine path is not silently judged by routine budgets.
    networked = copy.deepcopy(baseline)
    networked["routine_path"] = False
    networked["network_used"] = True
    assert mod.validate_measurement(networked, policy) == {
        "status": "NOT_APPLICABLE",
        "reason": "NON_ROUTINE_PATH",
    }

    # 13: total budget cannot relax the existing 2000ms incremental ceiling.
    relaxed = copy.deepcopy(policy)
    relaxed["budgets_ms"]["TOTAL"] = 2001
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_policy(relaxed, incremental),
        "incremental ceiling relaxation",
    )

    # 14: budget ordering cannot collapse.
    unordered = copy.deepcopy(policy)
    unordered["budgets_ms"]["T1"] = unordered["budgets_ms"]["T0"]
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_policy(unordered, incremental),
        "budget ordering drift",
    )

    # 15: policy cannot redefine pytest-backed execution as routine.
    unsafe = copy.deepcopy(policy)
    unsafe["applicability"]["pytest_invoked"] = True
    _expect(
        mod.TimingBudgetError,
        lambda: mod.validate_policy(unsafe, incremental),
        "pytest routine applicability",
    )

    print("VALIDATION_TIMING_BUDGET_SELFTEST_PASS probes=15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
