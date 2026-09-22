#!/usr/bin/env python3
"""Adversarial tests for deterministic AWU risk classification."""

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
    path=ROOT/"scripts/governance/validate_awu_risk.py"
    spec=importlib.util.spec_from_file_location("awu_risk_selftest",path)
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
    raise AssertionError(f"risk negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    policy=_load(ROOT/"config/governance/awu_risk_policy_v1.json")
    base=_load(ROOT/"engineering/fixtures/agent_work_unit_v1.example.json")
    mod.validate_policy(policy)
    assert mod.validate_risk(base,policy)[0]=="R1"

    under=copy.deepcopy(base)
    under["planning"]["risk_class"]="R0"
    _expect(mod.AwuRiskError,lambda:mod.validate_risk(under,policy),"R1 underclassified")

    r2=copy.deepcopy(base)
    r2["planning"]["complexity_factors"]["temporal_lineage_semantics"]=True
    r2["planning"]["complexity_score"]=4
    r2["planning"]["risk_class"]="R2"
    assert mod.validate_risk(r2,policy)[0]=="R2"

    r3=copy.deepcopy(base)
    r3["planning"]["complexity_factors"]["risk_execution_permission"]=True
    r3["planning"]["complexity_score"]=5
    r3["planning"]["risk_class"]="R3"
    assert mod.validate_risk(r3,policy)[0]=="R3"

    critical=copy.deepcopy(base)
    critical["scope"]["allowed_paths"].append("src/crypto_quant_bot/risk/example.py")
    critical["planning"]["complexity_factors"]["production_modules"]=1
    critical["planning"]["complexity_score"]=3
    critical["planning"]["size_estimate"]["files_touched"]=7
    critical["planning"]["risk_class"]="R3"
    assert mod.validate_risk(critical,policy)[0]=="R3"

    unclassified=copy.deepcopy(base)
    unclassified["planning"]["risk_class"]="UNCLASSIFIED"
    _expect(mod.AwuRiskError,lambda:mod.validate_risk(unclassified,policy),"executable unclassified")

    planned=copy.deepcopy(base)
    planned["status"]="PLANNED"
    planned["planning"]["risk_class"]="UNCLASSIFIED"
    assert mod.validate_risk(planned,policy)[0]=="R1"

    high=copy.deepcopy(base)
    high["status"]="PLANNED"
    high["planning"]["risk_class"]="R2"
    high["planning"]["complexity_factors"]["production_modules"]=9
    high["planning"]["complexity_score"]=11
    high["planning"]["split_required"]=True
    high["planning"]["split_reasons"]=["COMPLEXITY_SCORE_GT_10"]
    assert mod.validate_risk(high,policy)[0]=="R2"

    print("AWU_RISK_SELFTEST_PASS probes=7")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
