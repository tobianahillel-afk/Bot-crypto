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


def _load_module(name: str, relative: str) -> ModuleType:
    path=ROOT/relative
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _module() -> ModuleType:
    return _load_module("t3t4_selector_selftest","scripts/governance/select_t3_t4.py")


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

    bad_r3_t3=copy.deepcopy(policy)
    bad_r3_t3["risk_to_t3"]["R3"]=[]
    _expect(
        mod.T3T4SelectionError,
        lambda:mod.validate_policy(bad_r3_t3),
        "R3 T3 floor removal",
    )

    bad_r3_t4=copy.deepcopy(policy)
    bad_r3_t4["risk_to_t4"]["R3"]=[]
    _expect(
        mod.T3T4SelectionError,
        lambda:mod.validate_policy(bad_r3_t4),
        "R3 T4 floor removal",
    )

    deep=_load_module(
        "t3t4_deep_assurance_crosscheck",
        "scripts/governance/validate_certification_deep_assurance.py",
    )
    deep_policy,deep_selection,deep_exact,deep_security,deep_evidence=deep._load_policies()
    deep.validate_policy(
        deep_policy,deep_selection,deep_exact,deep_security,deep_evidence
    )
    deep_bad_t3=copy.deepcopy(deep_selection)
    deep_bad_t3["risk_to_t3"]["R3"]=[]
    _expect(
        deep.DeepAssuranceError,
        lambda:deep.validate_policy(
            deep_policy,deep_bad_t3,deep_exact,deep_security,deep_evidence
        ),
        "deep assurance accepts missing R3 T3 floor",
    )
    deep_bad_t4=copy.deepcopy(deep_selection)
    deep_bad_t4["risk_to_t4"]["R3"]=["EXACT_HEAD_CERTIFICATION"]
    _expect(
        deep.DeepAssuranceError,
        lambda:deep.validate_policy(
            deep_policy,deep_bad_t4,deep_exact,deep_security,deep_evidence
        ),
        "deep assurance accepts incomplete R3 T4 floor",
    )
    r3_plan=deep.build_assurance_plan(r3,"a"*40,deep_policy,deep_selection)
    assert {item["control_id"] for item in r3_plan["material"]["controls"]} == {
        "ENGINEERING_BOOTSTRAP","SAST","SECRET_SCANNING"
    }
    incomplete_r3=deep.evaluate_assurance(r3_plan,[],deep_policy)
    assert incomplete_r3["status"]=="INCOMPLETE"
    assert incomplete_r3["satisfied"] is False

    exact=_load_module(
        "t3t4_exact_head_crosscheck",
        "scripts/governance/validate_certification_exact_head_binding.py",
    )
    exact_policy,lifecycle,evidence_policy,proof_policy,assurance_policy=exact._load_policies()
    exact.validate_policy(
        exact_policy,lifecycle,evidence_policy,proof_policy,assurance_policy
    )
    exact_bad_t3=copy.deepcopy(assurance_policy)
    exact_bad_t3["risk_to_t3"]["R3"]=[]
    _expect(
        exact.ExactHeadBindingError,
        lambda:exact.validate_policy(
            exact_policy,lifecycle,evidence_policy,proof_policy,exact_bad_t3
        ),
        "exact-head accepts missing R3 T3 floor",
    )
    exact_bad_t4=copy.deepcopy(assurance_policy)
    exact_bad_t4["risk_to_t4"]["R3"]=["EXACT_HEAD_CERTIFICATION"]
    _expect(
        exact.ExactHeadBindingError,
        lambda:exact.validate_policy(
            exact_policy,lifecycle,evidence_policy,proof_policy,exact_bad_t4
        ),
        "exact-head accepts incomplete R3 T4 floor",
    )

    overlap=_t2(
        remaining=("EVIDENCE_PROVENANCE",),
        covered=("EVIDENCE_PROVENANCE",),
    )
    _expect(
        mod.T3T4SelectionError,
        lambda:mod.select_requirements(overlap,"R1",policy),
        "covered/uncovered overlap",
    )

    print("T3_T4_SELECTOR_SELFTEST_PASS probes=16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
