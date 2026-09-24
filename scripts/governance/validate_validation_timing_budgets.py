#!/usr/bin/env python3
"""Validate deterministic routine-path timing budgets without executing validation tiers."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "validation_timing_budget_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class TimingBudgetError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TimingBudgetError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TimingBudgetError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any], incremental: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise TimingBudgetError("unsupported timing-budget schema_version")
    if policy.get("policy_kind") != "validation_timing_budget_v1":
        raise TimingBudgetError("invalid timing-budget policy kind")
    if policy.get("semantics") != "ROUTINE_PATH_MEASURED_ELAPSED_FAIL_CLOSED":
        raise TimingBudgetError("timing-budget semantics drift")
    if policy.get("source_incremental_policy") != "config/governance/incremental_validation_policy_v1.json":
        raise TimingBudgetError("incremental-policy binding drift")

    applicability = policy.get("applicability")
    expected_applicability = {
        "routine_path": True,
        "pytest_invoked": False,
        "full_suite_executed": False,
        "network_used": False,
        "deep_assurance_executed": False,
        "certification_executed": False,
    }
    if applicability != expected_applicability:
        raise TimingBudgetError("timing budgets must remain routine-path only")

    required = policy.get("required_measurement_fields")
    if required != [
        "stage_elapsed_ms.T0",
        "stage_elapsed_ms.T1",
        "stage_elapsed_ms.T2",
        "elapsed_ms",
    ]:
        raise TimingBudgetError("required measured timing fields drift")

    budgets = policy.get("budgets_ms")
    if not isinstance(budgets, dict) or list(budgets) != ["T0", "T1", "T2", "TOTAL"]:
        raise TimingBudgetError("timing budgets must define T0 T1 T2 TOTAL in canonical order")
    for key, value in budgets.items():
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise TimingBudgetError(f"{key} budget must be a positive integer millisecond value")
    if not budgets["T0"] < budgets["T1"] <= budgets["T2"] < budgets["TOTAL"]:
        raise TimingBudgetError("timing budget ordering is invalid")

    if incremental.get("policy_kind") != "incremental_validation_policy_v1":
        raise TimingBudgetError("invalid bound incremental validation policy")
    ceiling = incremental.get("routine_max_elapsed_ms")
    if not isinstance(ceiling, int) or ceiling != 2000:
        raise TimingBudgetError("incremental routine ceiling drift")
    if budgets["TOTAL"] > ceiling:
        raise TimingBudgetError("TOTAL timing budget exceeds incremental routine ceiling")

    reference = policy.get("calibration_reference")
    if not isinstance(reference, dict):
        raise TimingBudgetError("calibration reference missing")
    if not isinstance(reference.get("workflow_run_id"), int) or reference["workflow_run_id"] <= 0:
        raise TimingBudgetError("calibration workflow run id invalid")
    head = reference.get("head_sha")
    if not isinstance(head, str) or SHA40.fullmatch(head) is None:
        raise TimingBudgetError("calibration head SHA invalid")
    observed = reference.get("observed_ms")
    if not isinstance(observed, dict) or set(observed) != {"T0", "T1", "T2", "TOTAL"}:
        raise TimingBudgetError("calibration timings incomplete")
    for key, value in observed.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise TimingBudgetError(f"calibration timing invalid: {key}")
        if value > budgets[key]:
            raise TimingBudgetError(f"calibration already exceeds budget: {key}")


def _number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise TimingBudgetError(f"measured timing missing/invalid: {label}")
    return float(value)


def measurement_applicable(result: dict[str, Any], policy: dict[str, Any]) -> bool:
    expected = policy["applicability"]
    return all(result.get(key) == value for key, value in expected.items())


def validate_measurement(result: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if result.get("incremental_validation_version") != 1:
        raise TimingBudgetError("measurement is not incremental validation v1")
    if not measurement_applicable(result, policy):
        if result.get("pytest_invoked") is True:
            return {"status": "NOT_APPLICABLE", "reason": "PYTEST_BACKED_T2"}
        return {"status": "NOT_APPLICABLE", "reason": "NON_ROUTINE_PATH"}

    stage = result.get("stage_elapsed_ms")
    if not isinstance(stage, dict):
        raise TimingBudgetError("stage_elapsed_ms missing")
    measured = {
        "T0": _number(stage.get("T0"), "T0"),
        "T1": _number(stage.get("T1"), "T1"),
        "T2": _number(stage.get("T2"), "T2"),
        "TOTAL": _number(result.get("elapsed_ms"), "TOTAL"),
    }
    exceeded = {
        key: {"measured_ms": value, "budget_ms": policy["budgets_ms"][key]}
        for key, value in measured.items()
        if value > policy["budgets_ms"][key]
    }
    if exceeded:
        raise TimingBudgetError(f"routine timing budget exceeded: {exceeded}")
    return {
        "status": "PASS",
        "measured_ms": measured,
        "budgets_ms": dict(policy["budgets_ms"]),
    }


def _routine(reference: dict[str, Any]) -> dict[str, Any]:
    observed = reference["observed_ms"]
    return {
        "incremental_validation_version": 1,
        "routine_path": True,
        "pytest_invoked": False,
        "full_suite_executed": False,
        "network_used": False,
        "deep_assurance_executed": False,
        "certification_executed": False,
        "stage_elapsed_ms": {
            "T0": observed["T0"],
            "T1": observed["T1"],
            "T2": observed["T2"],
            "T3_T4_SELECTOR": 0.0,
        },
        "elapsed_ms": observed["TOTAL"],
    }


def _expect(fn: Any, label: str) -> None:
    try:
        fn()
    except TimingBudgetError:
        return
    raise AssertionError(f"timing-budget negative scenario unexpectedly passed: {label}")


def self_check(policy: dict[str, Any], incremental: dict[str, Any]) -> None:
    validate_policy(policy, incremental)
    assert validate_measurement(_routine(policy["calibration_reference"]), policy)["status"] == "PASS"

    broken = copy.deepcopy(policy)
    broken["budgets_ms"]["T0"] = 0
    _expect(lambda: validate_policy(broken, incremental), "zero budget")

    broken = copy.deepcopy(policy)
    broken["budgets_ms"]["TOTAL"] = 2500
    _expect(lambda: validate_policy(broken, incremental), "ceiling relaxation")

    broken = copy.deepcopy(policy)
    broken["applicability"]["pytest_invoked"] = True
    _expect(lambda: validate_policy(broken, incremental), "pytest applicability")

    slow = _routine(policy["calibration_reference"])
    slow["stage_elapsed_ms"]["T1"] = policy["budgets_ms"]["T1"] + 0.001
    _expect(lambda: validate_measurement(slow, policy), "T1 over budget")

    missing = _routine(policy["calibration_reference"])
    del missing["stage_elapsed_ms"]["T2"]
    _expect(lambda: validate_measurement(missing, policy), "missing T2 measurement")

    pytest_backed = _routine(policy["calibration_reference"])
    pytest_backed["routine_path"] = False
    pytest_backed["pytest_invoked"] = True
    outcome = validate_measurement(pytest_backed, policy)
    assert outcome == {"status": "NOT_APPLICABLE", "reason": "PYTEST_BACKED_T2"}

    print("VALIDATION_TIMING_BUDGET_SELF_CHECK_PASS probes=7")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    try:
        policy = _json(POLICY_PATH)
        incremental = _json(ROOT / policy["source_incremental_policy"])
        if args.self_check:
            self_check(policy, incremental)
        else:
            validate_policy(policy, incremental)
    except (TimingBudgetError, AssertionError, KeyError) as exc:
        print(f"VALIDATION_TIMING_BUDGET_INVALID: {exc}", file=sys.stderr)
        return 1
    print(
        "VALIDATION_TIMING_BUDGET_SELF_CHECK_VALID"
        if args.self_check
        else "VALIDATION_TIMING_BUDGET_VALID"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
