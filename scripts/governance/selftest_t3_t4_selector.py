#!/usr/bin/env python3
"""Adversarial qualification for symbolic T3/T4 requirement selection."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path=ROOT/"scripts"/"governance"/"select_t3_t4.py"
    spec=importlib.util.spec_from_file_location("t3t4_selector_selftest",path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"T3/T4 selector negative scenario unexpectedly passed: {label}")


def _t2(*,remaining:tuple[str,...]=(),covered:tuple[str,...]=())->dict[str,Any]:
    return {
        "t2_version":1,
        "remaining_uncovered_impacts":list(remaining),
        "t2_covered_impacts":list(covered),
    }


def main()->int:
    mod=_module()
    policy=mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)

    workflow=mod.select_requirements(
        _t2(remaining=("ACTIONS_SECURITY","WORKFLOW_SYNTAX")),"R1",policy
    )
    assert workflow["t3_required"] is True
    assert workflow["t4_required"] is False
    assert {"WORKFLOW_ASSURANCE","SECURITY_ASSURANCE"} <= set(workflow["t3_requirements"])
    assert workflow["requirements_executed"] == []

    security=mod.select_requirements(
        _t2(remaining=("SECURITY_STATIC_ANALYSIS","SECRET_CONTROLS")),"R2",policy
    )
    assert security["t3_requirements"] == ["SECURITY_ASSURANCE"]
    assert security["t4_required"] is False

    static=mod.select_requirements(_t2(remaining=("STATIC_ANALYSIS",)),"R1",policy)
    assert static["t3_requirements"] == ["STATIC_ANALYSIS_ASSURANCE"]

    unknown=mod.select_requirements(
        _t2(remaining=("CONSERVATIVE_BROAD_IMPACT","HUMAN_REVIEW_REQUIRED")),"R1",policy
    )
    assert unknown["t3_requirements"] == ["MANUAL_DEEP_REVIEW"]

    r3=mod.select_requirements(_t2(),"R3",policy)
    assert r3["t3_requirements"] == ["RISK_EXECUTION_ASSURANCE"]
    assert {"EXACT_HEAD_CERTIFICATION","R3_FULL_CERTIFICATION_CHAIN"} <= set(
        r3["t4_requirements"]
    )

    provenance=mod.select_requirements(
        _t2(covered=("EVIDENCE_PROVENANCE",)),"R1",policy
    )
    assert provenance["t3_required"] is False
    assert provenance["t4_required"] is True
    assert {"EXACT_HEAD_CERTIFICATION","PROVENANCE_CERTIFICATION"} <= set(
        provenance["t4_requirements"]
    )

    low=mod.select_requirements(_t2(),"R1",policy)
    assert low["t3_required"] is False
    assert low["t4_required"] is False

    disappearing=copy.deepcopy(policy)
    disappearing["residual_impact_to_t3"]["ACTIONS_SECURITY"]=[]
    _expect(
        mod.T3T4SelectionError,
        lambda:mod.select_requirements(
            _t2(remaining=("ACTIONS_SECURITY",)),"R1",disappearing
        ),
        "residual impact disappearance",
    )

    bad_r3=copy.deepcopy(policy)
    bad_r3["risk_to_t4"]["R3"]=[]
    _expect(mod.T3T4SelectionError,lambda:mod.validate_policy(bad_r3),"R3 floor removal")

    overlap=_t2(
        remaining=("EVIDENCE_PROVENANCE",),
        covered=("EVIDENCE_PROVENANCE",),
    )
    _expect(
        mod.T3T4SelectionError,
        lambda:mod.select_requirements(overlap,"R1",policy),
        "covered/uncovered overlap",
    )

    print("T3_T4_SELECTOR_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
