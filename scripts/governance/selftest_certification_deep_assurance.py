#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.3 risk-proportional assurance."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HEAD = "a" * 40


def _module() -> ModuleType:
    path = ROOT / "scripts/governance/validate_certification_deep_assurance.py"
    spec = importlib.util.spec_from_file_location("deep_assurance_selftest", path)
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
    raise AssertionError(f"deep-assurance negative scenario unexpectedly passed: {label}")


def _selector(requirement: str | None = None, reason: str | None = None) -> dict[str, Any]:
    if requirement is None:
        return {
            "selector_version": 1,
            "t3_required": False,
            "t3_requirements": [],
            "selection_reasons": [],
        }
    return {
        "selector_version": 1,
        "t3_required": True,
        "t3_requirements": [requirement],
        "selection_reasons": [
            {"tier": "T3", "requirement": requirement, "reason": reason}
        ],
    }


def _evidence(plan: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    run_id = 100
    for control in plan["material"]["controls"]:
        if not control["automatic"]:
            continue
        run_id += 1
        result.append(
            {
                "control_id": control["control_id"],
                "run_id": run_id,
                "workflow": control["workflow_name"],
                "head_sha": HEAD,
                "conclusion": "success",
            }
        )
    return result


def main() -> int:
    mod = _module()
    policy, selection, exact_head, security, evidence_policy = mod._load_policies()
    mod.validate_policy(policy, selection, exact_head, security, evidence_policy)

    empty = mod.build_assurance_plan(_selector(), HEAD, policy, selection)
    empty_verdict = mod.evaluate_assurance(empty, [], policy)
    assert empty_verdict["status"] == "NOT_REQUIRED"
    assert empty_verdict["satisfied"] is True

    workflow = mod.build_assurance_plan(
        _selector("WORKFLOW_ASSURANCE", "RESIDUAL_IMPACT:WORKFLOW_SYNTAX"),
        HEAD, policy, selection,
    )
    assert [x["control_id"] for x in workflow["material"]["controls"]] == [
        "WORKFLOW_SECURITY"
    ]

    actions = mod.build_assurance_plan(
        _selector("SECURITY_ASSURANCE", "RESIDUAL_IMPACT:ACTIONS_SECURITY"),
        HEAD, policy, selection,
    )
    assert {x["control_id"] for x in actions["material"]["controls"]} == {
        "SUPPLY_CHAIN", "WORKFLOW_SECURITY"
    }
    actions_verdict = mod.evaluate_assurance(actions, _evidence(actions), policy)
    assert actions_verdict["status"] == "PASS"
    assert actions_verdict["satisfied"] is True

    sast = mod.build_assurance_plan(
        _selector("STATIC_ANALYSIS_ASSURANCE", "RESIDUAL_IMPACT:STATIC_ANALYSIS"),
        HEAD, policy, selection,
    )
    assert [x["control_id"] for x in sast["material"]["controls"]] == ["SAST"]

    security_sast = mod.build_assurance_plan(
        _selector("SECURITY_ASSURANCE", "RESIDUAL_IMPACT:SECURITY_STATIC_ANALYSIS"),
        HEAD, policy, selection,
    )
    assert [x["control_id"] for x in security_sast["material"]["controls"]] == ["SAST"]

    secrets = mod.build_assurance_plan(
        _selector("SECURITY_ASSURANCE", "RESIDUAL_IMPACT:SECRET_CONTROLS"),
        HEAD, policy, selection,
    )
    assert [x["control_id"] for x in secrets["material"]["controls"]] == [
        "SECRET_SCANNING"
    ]

    r3 = mod.build_assurance_plan(
        _selector("RISK_EXECUTION_ASSURANCE", "RISK_CLASS:R3"),
        HEAD, policy, selection,
    )
    assert {x["control_id"] for x in r3["material"]["controls"]} == {
        "ENGINEERING_BOOTSTRAP", "SAST", "SECRET_SCANNING"
    }

    manual = mod.build_assurance_plan(
        _selector("MANUAL_DEEP_REVIEW", "RESIDUAL_IMPACT:HUMAN_REVIEW_REQUIRED"),
        HEAD, policy, selection,
    )
    manual_verdict = mod.evaluate_assurance(manual, [], policy)
    assert manual_verdict["status"] == "MANUAL_REVIEW_REQUIRED"
    assert manual_verdict["satisfied"] is False

    unknown = _selector("SECURITY_ASSURANCE", "RESIDUAL_IMPACT:NOT_REAL")
    _expect(
        mod.DeepAssuranceError,
        lambda: mod.build_assurance_plan(unknown, HEAD, policy, selection),
        "unknown selection reason",
    )

    missing_reason = _selector("SECURITY_ASSURANCE", "RESIDUAL_IMPACT:ACTIONS_SECURITY")
    missing_reason["selection_reasons"] = []
    _expect(
        mod.DeepAssuranceError,
        lambda: mod.build_assurance_plan(missing_reason, HEAD, policy, selection),
        "selected requirement without reason",
    )

    incomplete = mod.evaluate_assurance(actions, _evidence(actions)[:1], policy)
    assert incomplete["status"] == "INCOMPLETE"
    assert incomplete["satisfied"] is False
    assert len(incomplete["missing_controls"]) == 1

    wrong_head = _evidence(actions)
    wrong_head[0]["head_sha"] = "b" * 40
    _expect(
        mod.DeepAssuranceError,
        lambda: mod.evaluate_assurance(actions, wrong_head, policy),
        "wrong-head evidence",
    )

    failed = _evidence(actions)
    failed[0]["conclusion"] = "failure"
    _expect(
        mod.DeepAssuranceError,
        lambda: mod.evaluate_assurance(actions, failed, policy),
        "failed evidence",
    )

    duplicate = _evidence(actions)
    duplicate.append(copy.deepcopy(duplicate[0]))
    _expect(
        mod.DeepAssuranceError,
        lambda: mod.evaluate_assurance(actions, duplicate, policy),
        "duplicate control evidence",
    )

    extra = _evidence(workflow)
    extra.append(
        {
            "control_id": "SECRET_SCANNING",
            "run_id": 999,
            "workflow": "Security Secrets",
            "head_sha": HEAD,
            "conclusion": "success",
        }
    )
    _expect(
        mod.DeepAssuranceError,
        lambda: mod.evaluate_assurance(workflow, extra, policy),
        "extra unselected evidence",
    )

    changed_run = _evidence(actions)
    verdict1 = mod.evaluate_assurance(actions, changed_run, policy)
    changed_run[0]["run_id"] += 1000
    verdict2 = mod.evaluate_assurance(actions, changed_run, policy)
    assert verdict1["assurance_identity_sha256"] != verdict2["assurance_identity_sha256"]

    print("CERTIFICATION_DEEP_ASSURANCE_SELFTEST_PASS probes=16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
