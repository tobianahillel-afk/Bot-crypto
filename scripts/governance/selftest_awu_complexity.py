#!/usr/bin/env python3
"""Adversarial tests for deterministic AWU complexity scoring."""

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
    path=ROOT/"scripts/governance/validate_awu_complexity.py"
    spec=importlib.util.spec_from_file_location("awu_complexity_validator_selftest",path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"{path} must contain an object")
    return value


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"complexity negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    policy=_load(ROOT/"config/governance/awu_complexity_policy_v1.json")
    base=_load(ROOT/"engineering/fixtures/agent_work_unit_v1.example.json")
    mod.validate_policy(policy)
    assert mod.validate_complexity(base,policy)==2

    forged=copy.deepcopy(base)
    forged["planning"]["complexity_score"]=1
    _expect(mod.AwuComplexityError,lambda:mod.validate_complexity(forged,policy),"forged score")

    missing_contract=copy.deepcopy(base)
    missing_contract["planning"]["complexity_factors"]["contract_schema_families"]=0
    missing_contract["planning"]["complexity_score"]=1
    _expect(mod.AwuComplexityError,lambda:mod.validate_complexity(missing_contract,policy),"contract underdeclaration")

    missing_ci=copy.deepcopy(base)
    missing_ci["planning"]["complexity_factors"]["ci_evidence_topology_change"]=False
    missing_ci["planning"]["complexity_score"]=1
    _expect(mod.AwuComplexityError,lambda:mod.validate_complexity(missing_ci,policy),"CI underdeclaration")

    high=copy.deepcopy(base)
    high["planning"]["complexity_factors"].update({
        "production_modules":3,
        "contract_schema_families":2,
        "policy_config_families":1,
        "persistence_checksum_boundary":True,
        "math_numeric_semantics":True,
        "temporal_lineage_semantics":True,
        "cross_domain_interfaces":2,
        "state_machine_or_concurrency":True,
        "security_trust_boundary":True,
        "risk_execution_permission":True,
        "dependency_change":True,
        "ci_evidence_topology_change":True,
    })
    high["scope"]["allowed_paths"].append("src/crypto_quant_bot/example.py")
    high["planning"]["complexity_score"]=24
    assert mod.validate_complexity(high,policy)==24

    print("AWU_COMPLEXITY_SELFTEST_PASS probes=4")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
