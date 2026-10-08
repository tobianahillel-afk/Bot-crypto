#!/usr/bin/env python3
"""Adversarial qualification for targeted allowlisted T1 selection."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "run_t1.py"
    spec = importlib.util.spec_from_file_location("t1_selftest_runner", path)
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
    raise AssertionError(f"T1 negative scenario unexpectedly passed: {label}")


def _t0(*families: str) -> dict[str, Any]:
    return {
        "t0_version": 1,
        "test_suite_executed": False,
        "impact": {"impact_families": list(families)},
    }


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy, set(mod.CHECKS))

    docs = mod.select_checks(_t0("DOC_CONSISTENCY"), policy)
    assert docs["selected_checks"] == []
    assert docs["uncovered_impacts"] == []

    governance = mod.select_checks(
        _t0("GOVERNANCE_VALIDATORS", "CONFIG_POLICY_VALIDATION"),
        policy,
    )
    assert set(governance["selected_checks"]) == {"DIFF_CHECK", "GOVERNANCE_ACTIVE_SCOPE"}
    assert governance["uncovered_impacts"] == []

    harness = mod.select_checks(_t0("TEST_HARNESS_INTEGRITY"), policy)
    assert set(harness["selected_checks"]) == {"DIFF_CHECK", "SELFTEST_ENTRYPOINT_CHECK"}

    workflow = mod.select_checks(_t0("WORKFLOW_SYNTAX", "ACTIONS_SECURITY"), policy)
    assert workflow["selected_checks"] == []
    assert set(workflow["uncovered_impacts"]) == {"ACTIONS_SECURITY", "WORKFLOW_SYNTAX"}

    unknown = mod.select_checks(
        _t0("CONSERVATIVE_BROAD_IMPACT", "HUMAN_REVIEW_REQUIRED"),
        policy,
    )
    assert set(unknown["uncovered_impacts"]) == {
        "CONSERVATIVE_BROAD_IMPACT", "HUMAN_REVIEW_REQUIRED"
    }

    mixed = mod.select_checks(
        _t0("DOC_CONSISTENCY", "GOVERNANCE_VALIDATORS", "WORKFLOW_SYNTAX"),
        policy,
    )
    assert set(mixed["selected_checks"]) == {"DIFF_CHECK", "GOVERNANCE_ACTIVE_SCOPE"}
    assert mixed["uncovered_impacts"] == ["WORKFLOW_SYNTAX"]

    _expect(
        mod.T1Error,
        lambda: mod.execute_checks(["NOT_A_REAL_CHECK"], "0" * 40),
        "unknown executable check id",
    )

    broken = copy.deepcopy(policy)
    broken["impact_to_checks"]["DOC_CONSISTENCY"] = ["NOT_A_REAL_CHECK"]
    _expect(
        mod.T1Error,
        lambda: mod.validate_policy(broken, set(mod.CHECKS)),
        "policy command/check injection",
    )

    incomplete = copy.deepcopy(policy)
    incomplete["impact_to_checks"].pop("UNIT_BEHAVIOR")
    _expect(
        mod.T1Error,
        lambda: mod.validate_policy(incomplete, set(mod.CHECKS)),
        "missing impact mapping",
    )

    bad_t0 = _t0("DOC_CONSISTENCY")
    bad_t0["test_suite_executed"] = True
    _expect(
        mod.T1Error,
        lambda: mod.select_checks(bad_t0, policy),
        "invalid T0 prerequisite",
    )

    print("T1_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
