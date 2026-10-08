#!/usr/bin/env python3
"""Calculate and enforce mandatory Agent Work Unit split decisions."""

from __future__ import annotations

import argparse,importlib.util,json,sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=ROOT/"config/governance/awu_split_policy_v1.json"


class AwuSplitError(ValueError): pass


def _load(path:Path)->dict[str,Any]:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise AwuSplitError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict): raise AwuSplitError(f"{path} must contain an object")
    return value


def _module(name:str,path:Path)->ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise AwuSplitError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module); return module


def validate_policy(policy:dict[str,Any])->None:
    if policy.get("schema_version")!=1 or policy.get("policy_kind")!="awu_mandatory_split_policy_v1": raise AwuSplitError("invalid split policy identity")
    rules=policy.get("rules")
    if not isinstance(rules,list) or not rules: raise AwuSplitError("split rules are required")
    codes=[]
    for rule in rules:
        if not isinstance(rule,dict) or set(rule)!={"code","source","operator","threshold"}: raise AwuSplitError("invalid split rule shape")
        if rule["operator"]!="GT": raise AwuSplitError("only GT split rules are supported")
        if not isinstance(rule["threshold"],int) or isinstance(rule["threshold"],bool) or rule["threshold"]<0: raise AwuSplitError("split threshold must be non-negative integer")
        codes.append(rule["code"])
    if len(codes)!=len(set(codes)): raise AwuSplitError("split rule codes must be unique")


def calculate_reasons(awu:dict[str,Any],policy:dict[str,Any])->list[str]:
    size=awu["planning"]["size_estimate"]; factors=awu["planning"]["complexity_factors"]
    sources={"complexity_score":awu["planning"]["complexity_score"],**size,"cross_domain_interfaces":factors["cross_domain_interfaces"]}
    reasons=[]
    for rule in policy["rules"]:
        source=rule["source"]
        if source not in sources: raise AwuSplitError(f"unknown split source {source}")
        value=sources[source]
        if not isinstance(value,int) or isinstance(value,bool): raise AwuSplitError(f"split source {source} must be integer")
        if value>rule["threshold"]: reasons.append(rule["code"])
    return sorted(reasons)


def validate_split(awu:dict[str,Any],policy:dict[str,Any])->list[str]:
    contract=_module("awu_contract_for_split",ROOT/"scripts/governance/validate_agent_work_unit.py")
    complexity=_module("awu_complexity_for_split",ROOT/"scripts/governance/validate_awu_complexity.py")
    try: contract.validate_awu(awu)
    except contract.AgentWorkUnitError as exc: raise AwuSplitError(str(exc)) from exc
    complexity_policy=_load(ROOT/"config/governance/awu_complexity_policy_v1.json")
    try: complexity.validate_complexity(awu,complexity_policy)
    except complexity.AwuComplexityError as exc: raise AwuSplitError(str(exc)) from exc

    reasons=calculate_reasons(awu,policy)
    required=bool(reasons)
    planning=awu["planning"]
    if planning["split_required"] is not required: raise AwuSplitError(f"split_required mismatch: declared={planning['split_required']} calculated={required}")
    if planning["split_reasons"]!=reasons: raise AwuSplitError(f"split_reasons mismatch: declared={planning['split_reasons']} calculated={reasons}")
    if required and awu["status"] not in set(policy["split_required_allowed_statuses"]): raise AwuSplitError(f"split-required AWU cannot be {awu['status']}")
    return reasons


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("paths",nargs="*",type=Path); args=parser.parse_args()
    policy=_load(POLICY_PATH)
    paths=args.paths or [ROOT/"engineering/fixtures/agent_work_unit_v1.example.json",*sorted((ROOT/"engineering/fixtures/awu_graph_valid").glob("*.json"))]
    try:
        validate_policy(policy)
        results=[]
        for path in paths:
            awu=_load(path); results.append((awu["id"],validate_split(awu,policy)))
    except AwuSplitError as exc:
        print(f"AWU_SPLIT_INVALID: {exc}",file=sys.stderr); return 1
    print("AWU_SPLIT_VALID "+",".join(f"{i}:{'|'.join(r) if r else 'NO_SPLIT'}" for i,r in results)); return 0


if __name__=="__main__": raise SystemExit(main())
