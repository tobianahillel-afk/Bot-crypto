#!/usr/bin/env python3
"""Adversarial qualification for conditional bounded T2 domain validation."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "run_t2.py"
    spec = importlib.util.spec_from_file_location("t2_selftest_runner", path)
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
    raise AssertionError(f"T2 negative scenario unexpectedly passed: {label}")


def _t1(*uncovered: str) -> dict[str, Any]:
    return {
        "t1_version":1,
        "full_suite_executed":False,
        "uncovered_impacts":list(uncovered),
    }


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)

    current = mod.select_groups(_t1("ACTIONS_SECURITY","WORKFLOW_SYNTAX"), policy)
    assert current["selected_groups"] == []
    assert set(current["remaining_uncovered_impacts"]) == {
        "ACTIONS_SECURITY","WORKFLOW_SYNTAX"
    }

    contracts = mod.select_groups(
        _t1("CONTRACT_SCHEMA_VALIDATION","CONTRACT_COMPATIBILITY"), policy
    )
    assert contracts["selected_groups"] == ["CONTRACT_TESTS"]

    data = mod.select_groups(
        _t1("DATA_CONTRACTS","TEMPORAL_CAUSALITY","DETERMINISTIC_REPLAY"), policy
    )
    assert data["selected_groups"] == ["DATA_TESTS"]

    risk = mod.select_groups(_t1("RISK_INVARIANTS","EXECUTION_SAFETY"), policy)
    assert risk["selected_groups"] == ["RISK_EXECUTION_TESTS"]

    unit = mod.select_groups(_t1("UNIT_BEHAVIOR"), policy)
    assert unit["selected_groups"] == ["CHANGED_DOMAIN_TESTS"]

    fake_tests = [
        "tests/test_contract_schema.py",
        "tests/test_market_data_replay.py",
        "tests/microstructure/test_order_flow.py",
        "tests/risk/test_risk_execution.py",
        "tests/audit/test_evidence_provenance.py",
    ]
    contract_plan = mod.plan_targets(
        ["CONTRACT_TESTS"], policy, ["contracts/foo.schema.json"], fake_tests
    )
    assert contract_plan["pytest_targets"] == ["tests/test_contract_schema.py"]

    changed_plan = mod.plan_targets(
        ["CHANGED_DOMAIN_TESTS"],
        policy,
        ["src/crypto_quant_bot/microstructure/order_flow.py"],
        fake_tests,
    )
    assert changed_plan["pytest_targets"] == ["tests/microstructure/test_order_flow.py"]

    _expect(
        mod.T2Error,
        lambda: mod.plan_targets(
            ["CONTRACT_TESTS"], policy, ["contracts/x.json"], ["tests/test_unrelated.py"]
        ),
        "selected group with zero targets",
    )

    no_groups = mod.execute_pytest([], policy["pytest_timeout_seconds"])
    assert no_groups["pytest_invoked"] is False

    broken = copy.deepcopy(policy)
    broken["impact_to_groups"]["UNIT_BEHAVIOR"] = ["NOT_A_REAL_GROUP"]
    _expect(mod.T2Error, lambda: mod.validate_policy(broken), "unknown T2 group injection")

    too_many_policy = copy.deepcopy(policy)
    too_many_policy["max_targets_per_group"] = 1
    _expect(
        mod.T2Error,
        lambda: mod.plan_targets(
            ["DATA_TESTS"],
            too_many_policy,
            ["src/crypto_quant_bot/data/feed.py"],
            ["tests/test_data_a.py","tests/test_data_b.py"],
        ),
        "target flood",
    )

    print("T2_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
