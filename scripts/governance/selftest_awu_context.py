#!/usr/bin/env python3
"""Adversarial tests for AWU context routing and budgets."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


def _module()->ModuleType:
    path=ROOT/"scripts/governance/validate_awu_context.py"
    spec=importlib.util.spec_from_file_location("awu_context_selftest",path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError("expected object")
    return value


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"context negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    policy=_load(ROOT/"config/governance/awu_context_policy_v1.json")
    path=ROOT/"engineering/fixtures/agent_work_unit_v1.example.json"
    base=_load(path)
    mod.validate_policy(policy)
    route=mod.validate_context(base,path,policy)
    assert route is not None and route["primary_count"]<=10

    missing=copy.deepcopy(base)
    missing["planning"]["context_budget"]={
        "max_primary_files":None,"max_reference_files":None,"max_total_kib":None
    }
    _expect(mod.AwuContextError,lambda:mod.validate_context(missing,path,policy),"missing executable budget")

    forged=copy.deepcopy(base)
    forged["planning"]["context_budget"]["max_primary_files"]=99
    _expect(mod.AwuContextError,lambda:mod.validate_context(forged,path,policy),"forged budget")

    escape=copy.deepcopy(base)
    escape["inputs"].append({"name":"escape","kind":"FILE","locator":"../outside.txt"})
    _expect(mod.AwuContextError,lambda:mod.validate_context(escape,path,policy),"path escape")

    planned=copy.deepcopy(base)
    planned["status"]="PLANNED"
    planned["planning"]["risk_class"]="UNCLASSIFIED"
    planned["planning"]["context_budget"]={
        "max_primary_files":None,"max_reference_files":None,"max_total_kib":None
    }
    assert mod.validate_context(planned,path,policy) is None

    too_small=copy.deepcopy(policy)
    too_small["budgets_by_risk"]["R1"]["max_primary_files"]=2
    _expect(mod.AwuContextError,lambda:mod.validate_context(base,path,too_small),"actual route exceeds budget")

    print("AWU_CONTEXT_SELFTEST_PASS probes=5")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
