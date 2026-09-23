#!/usr/bin/env python3
"""Run the incremental validation chain once, passing prior-tier results forward."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=ROOT/"config"/"governance"/"incremental_validation_policy_v1.json"


class IncrementalValidationError(ValueError):
    pass


def _json(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise IncrementalValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict):
        raise IncrementalValidationError(f"{path} must contain an object")
    return value


def _module(name:str,path:Path)->ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise IncrementalValidationError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def validate_policy(policy:dict[str,Any])->None:
    if policy.get("schema_version")!=1:
        raise IncrementalValidationError("unsupported incremental policy schema_version")
    if policy.get("policy_kind")!="incremental_validation_policy_v1":
        raise IncrementalValidationError("invalid incremental validation policy kind")
    if policy.get("semantics")!="SINGLE_PASS_NO_PREREQUISITE_RECOMPUTATION":
        raise IncrementalValidationError("incremental validation semantics drift")
    order=policy.get("expected_stage_order")
    if order!=["T0","T1","T2","T3_T4_SELECTOR"]:
        raise IncrementalValidationError("stage order drift")
    baseline=policy.get("nested_baseline_invocations")
    single=policy.get("single_pass_invocations")
    if baseline!={"T0":4,"T1":3,"T2":2,"T3_T4_SELECTOR":1}:
        raise IncrementalValidationError("nested baseline invocation model drift")
    if single!={"T0":1,"T1":1,"T2":1,"T3_T4_SELECTOR":1}:
        raise IncrementalValidationError("single-pass invocation model drift")
    avoided=sum(baseline.values())-sum(single.values())
    if avoided!=policy.get("expected_avoided_invocations"):
        raise IncrementalValidationError("avoided invocation count mismatch")
    ratio=avoided/sum(baseline.values())
    floor=policy.get("minimum_recomputation_reduction_ratio")
    if not isinstance(floor,(int,float)) or ratio<float(floor):
        raise IncrementalValidationError("recomputation reduction ratio below policy floor")
    limit=policy.get("routine_max_elapsed_ms")
    if not isinstance(limit,int) or not 100<=limit<=10000:
        raise IncrementalValidationError("invalid routine elapsed limit")


def run_chain(
    *,
    t0_func:Callable[[],dict[str,Any]],
    t1_func:Callable[[dict[str,Any]],dict[str,Any]],
    t2_func:Callable[[dict[str,Any]],dict[str,Any]],
    selector_func:Callable[[dict[str,Any]],dict[str,Any]],
    policy:dict[str,Any],
)->dict[str,Any]:
    validate_policy(policy)
    started=time.perf_counter()
    calls={"T0":0,"T1":0,"T2":0,"T3_T4_SELECTOR":0}

    calls["T0"]+=1
    t0=t0_func()
    calls["T1"]+=1
    t1=t1_func(t0)
    calls["T2"]+=1
    t2=t2_func(t1)
    calls["T3_T4_SELECTOR"]+=1
    selector=selector_func(t2)

    if t0.get("t0_version")!=1:
        raise IncrementalValidationError("T0 result version invalid")
    if t1.get("t1_version")!=1 or t1.get("prerequisite_t0_source")!="PRECOMPUTED":
        raise IncrementalValidationError("T1 did not consume precomputed T0")
    if t2.get("t2_version")!=1 or t2.get("prerequisite_t1_source")!="PRECOMPUTED":
        raise IncrementalValidationError("T2 did not consume precomputed T1")
    if (
        selector.get("selector_version")!=1
        or selector.get("prerequisite_t2_source")!="PRECOMPUTED"
    ):
        raise IncrementalValidationError("selector did not consume precomputed T2")
    if calls!=policy["single_pass_invocations"]:
        raise IncrementalValidationError(f"stage invocation count drift: {calls}")

    baseline_total=sum(policy["nested_baseline_invocations"].values())
    actual_total=sum(calls.values())
    avoided=baseline_total-actual_total
    ratio=avoided/baseline_total
    elapsed=round((time.perf_counter()-started)*1000,3)

    pytest_invoked=bool(t2.get("pytest",{}).get("pytest_invoked"))
    full_suite=any(
        bool(result.get("full_suite_executed"))
        for result in (t0,t1,t2,selector)
        if isinstance(result,dict)
    )
    network=any(
        bool(result.get("network_used"))
        for result in (t0,t1,t2,selector)
        if isinstance(result,dict)
    )
    deep_executed=bool(
        selector.get("assurance_executed") or selector.get("certification_executed")
    )

    routine=not pytest_invoked and not full_suite and not network and not deep_executed
    if routine and elapsed>policy["routine_max_elapsed_ms"]:
        raise IncrementalValidationError(
            f"routine incremental chain exceeded {policy['routine_max_elapsed_ms']} ms: {elapsed}"
        )

    return {
        "incremental_validation_version":1,
        "active_awu":selector.get("active_awu") or t2.get("active_awu"),
        "stage_invocations":calls,
        "nested_baseline_invocations":policy["nested_baseline_invocations"],
        "avoided_stage_invocations":avoided,
        "recomputation_reduction_ratio":round(ratio,3),
        "stage_elapsed_ms":{
            "T0":t0.get("elapsed_ms"),
            "T1":t1.get("elapsed_ms"),
            "T2":t2.get("elapsed_ms"),
            "T3_T4_SELECTOR":selector.get("elapsed_ms"),
        },
        "elapsed_ms":elapsed,
        "routine_path":routine,
        "pytest_invoked":pytest_invoked,
        "full_suite_executed":full_suite,
        "network_used":network,
        "deep_assurance_executed":bool(selector.get("assurance_executed")),
        "certification_executed":bool(selector.get("certification_executed")),
        "selected_t1_checks":t1.get("selected_checks",[]),
        "selected_t2_groups":t2.get("selected_groups",[]),
        "remaining_uncovered_impacts":t2.get("remaining_uncovered_impacts",[]),
        "t3_requirements":selector.get("t3_requirements",[]),
        "t4_requirements":selector.get("t4_requirements",[]),
        "completed_validation_tiers":selector.get("completed_validation_tiers",[]),
        "selected_validation_tiers":selector.get("selected_validation_tiers",[]),
    }


def repository_run()->dict[str,Any]:
    policy=_json(POLICY_PATH)
    t0=_module("incremental_t0",ROOT/"scripts/governance/run_t0.py")
    t1=_module("incremental_t1",ROOT/"scripts/governance/run_t1.py")
    t2=_module("incremental_t2",ROOT/"scripts/governance/run_t2.py")
    selector=_module("incremental_selector",ROOT/"scripts/governance/select_t3_t4.py")
    try:
        return run_chain(
            t0_func=t0.repository_run,
            t1_func=t1.repository_run,
            t2_func=t2.repository_run,
            selector_func=selector.repository_run,
            policy=policy,
        )
    except (t0.T0Error,t1.T1Error,t2.T2Error,selector.T3T4SelectionError) as exc:
        raise IncrementalValidationError(str(exc)) from exc


def main()->int:
    try:
        result=repository_run()
    except IncrementalValidationError as exc:
        print(f"INCREMENTAL_VALIDATION_INVALID: {exc}",file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
