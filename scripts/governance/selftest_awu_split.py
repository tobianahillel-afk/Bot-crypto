#!/usr/bin/env python3
"""Adversarial tests for mandatory AWU split enforcement."""

from __future__ import annotations

import copy,importlib.util,json,sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


def _module()->ModuleType:
    path=ROOT/"scripts/governance/validate_awu_split.py"; spec=importlib.util.spec_from_file_location("awu_split_selftest",path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module); return module


def _load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError("expected object")
    return value


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try: fn()
    except exc_type: return
    raise AssertionError(f"split negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module(); policy=_load(ROOT/"config/governance/awu_split_policy_v1.json"); base=_load(ROOT/"engineering/fixtures/agent_work_unit_v1.example.json")
    mod.validate_policy(policy); assert mod.validate_split(base,policy)==[]

    forged=copy.deepcopy(base); forged["planning"]["size_estimate"]["files_touched"]=16
    _expect(mod.AwuSplitError,lambda:mod.validate_split(forged,policy),"forged no-split")

    valid_split=copy.deepcopy(forged); valid_split["status"]="PLANNED"; valid_split["planning"]["split_required"]=True; valid_split["planning"]["split_reasons"]=["FILES_TOUCHED_GT_15"]
    assert mod.validate_split(valid_split,policy)==["FILES_TOUCHED_GT_15"]

    executable=copy.deepcopy(valid_split); executable["status"]="IN_PROGRESS"
    _expect(mod.AwuSplitError,lambda:mod.validate_split(executable,policy),"executable oversized AWU")

    complex_one=copy.deepcopy(base); complex_one["planning"]["complexity_factors"]["production_modules"]=9; complex_one["planning"]["complexity_score"]=11
    complex_one["status"]="PLANNED"; complex_one["planning"]["split_required"]=True; complex_one["planning"]["split_reasons"]=["COMPLEXITY_SCORE_GT_10"]
    assert mod.validate_split(complex_one,policy)==["COMPLEXITY_SCORE_GT_10"]

    multi=copy.deepcopy(base); multi["planning"]["size_estimate"].update({"business_domains":2,"contract_families":2,"trust_boundaries":2})
    multi["status"]="PLANNED"; multi["planning"]["split_required"]=True
    multi["planning"]["split_reasons"]=["BUSINESS_DOMAINS_GT_1","CONTRACT_FAMILIES_GT_1","TRUST_BOUNDARIES_GT_1"]
    assert mod.validate_split(multi,policy)==multi["planning"]["split_reasons"]

    wrong_reasons=copy.deepcopy(multi); wrong_reasons["planning"]["split_reasons"]=["BUSINESS_DOMAINS_GT_1"]
    _expect(mod.AwuSplitError,lambda:mod.validate_split(wrong_reasons,policy),"incomplete split reasons")

    print("AWU_SPLIT_SELFTEST_PASS probes=6"); return 0


if __name__=="__main__": raise SystemExit(main())
