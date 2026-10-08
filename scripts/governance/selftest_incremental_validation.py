#!/usr/bin/env python3
"""Adversarial qualification for single-pass incremental validation orchestration."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


def _module()->ModuleType:
    path=ROOT/"scripts"/"governance"/"run_incremental_validation.py"
    spec=importlib.util.spec_from_file_location("incremental_validation_selftest",path)
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
    raise AssertionError(f"incremental-validation negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    policy=mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)
    observed={"T0":0,"T1":0,"T2":0,"T3":0}

    def fake_t0()->dict[str,Any]:
        observed["T0"]+=1
        return {
            "t0_version":1,"elapsed_ms":1.0,"full_suite_executed":False,
            "network_used":False,
        }

    def fake_t1(t0:dict[str,Any])->dict[str,Any]:
        observed["T1"]+=1
        assert t0["t0_version"]==1
        return {
            "t1_version":1,"prerequisite_t0_source":"PRECOMPUTED","elapsed_ms":2.0,
            "selected_checks":["DIFF_CHECK"],"full_suite_executed":False,"network_used":False,
        }

    def fake_t2(t1:dict[str,Any])->dict[str,Any]:
        observed["T2"]+=1
        assert t1["t1_version"]==1
        return {
            "t2_version":1,"prerequisite_t1_source":"PRECOMPUTED","elapsed_ms":3.0,
            "selected_groups":[],"remaining_uncovered_impacts":["WORKFLOW_SYNTAX"],
            "pytest":{"pytest_invoked":False},"full_suite_executed":False,"network_used":False,
        }

    def fake_selector(t2:dict[str,Any])->dict[str,Any]:
        observed["T3"]+=1
        assert t2["t2_version"]==1
        return {
            "selector_version":1,"prerequisite_t2_source":"PRECOMPUTED","elapsed_ms":4.0,
            "active_awu":"ENG-X","assurance_executed":False,"certification_executed":False,
            "t3_requirements":["WORKFLOW_ASSURANCE"],"t4_requirements":[],
            "completed_validation_tiers":["T0","T1","T2"],
            "selected_validation_tiers":["T0","T1","T2","T3"],
            "full_suite_executed":False,"network_used":False,
        }

    result=mod.run_chain(
        t0_func=fake_t0,t1_func=fake_t1,t2_func=fake_t2,
        selector_func=fake_selector,policy=policy,
    )
    assert observed=={"T0":1,"T1":1,"T2":1,"T3":1}
    assert result["stage_invocations"]=={
        "T0":1,"T1":1,"T2":1,"T3_T4_SELECTOR":1
    }
    assert result["avoided_stage_invocations"]==6
    assert result["recomputation_reduction_ratio"]==0.6
    assert result["routine_path"] is True
    assert result["pytest_invoked"] is False
    assert result["deep_assurance_executed"] is False
    assert result["certification_executed"] is False

    bad_policy=copy.deepcopy(policy)
    bad_policy["expected_avoided_invocations"]=5
    _expect(
        mod.IncrementalValidationError,
        lambda:mod.validate_policy(bad_policy),
        "forged avoided count",
    )

    def bad_t1(_t0:dict[str,Any])->dict[str,Any]:
        value=fake_t1(_t0)
        value["prerequisite_t0_source"]="COMPUTED"
        return value
    _expect(
        mod.IncrementalValidationError,
        lambda:mod.run_chain(
            t0_func=fake_t0,t1_func=bad_t1,t2_func=fake_t2,
            selector_func=fake_selector,policy=policy,
        ),
        "T0 recomputation",
    )

    def pytest_t2(t1:dict[str,Any])->dict[str,Any]:
        value=fake_t2(t1)
        value["pytest"]={"pytest_invoked":True}
        return value
    nonroutine=mod.run_chain(
        t0_func=fake_t0,t1_func=fake_t1,t2_func=pytest_t2,
        selector_func=fake_selector,policy=policy,
    )
    assert nonroutine["routine_path"] is False

    print("INCREMENTAL_VALIDATION_SELFTEST_PASS probes=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
