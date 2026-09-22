#!/usr/bin/env python3
"""Validate risk-aware AWU context budgets and build deterministic context routes."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=ROOT/"config/governance/awu_context_policy_v1.json"


class AwuContextError(ValueError):
    pass


def _load(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise AwuContextError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict):
        raise AwuContextError(f"{path} must contain an object")
    return value


def _module(name:str,path:Path)->ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise AwuContextError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _dedupe(values:list[str])->list[str]:
    seen:set[str]=set()
    result=[]
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _safe_repo_path(locator:str)->Path|None:
    candidate=Path(locator)
    if candidate.is_absolute():
        raise AwuContextError(f"absolute context locator is forbidden: {locator}")
    resolved=(ROOT/candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise AwuContextError(f"context locator escapes repository: {locator}") from exc
    if resolved.is_file():
        return resolved
    return None


def validate_policy(policy:dict[str,Any])->None:
    if policy.get("schema_version")!=1 or policy.get("policy_kind")!="awu_context_policy_v1":
        raise AwuContextError("invalid context policy identity")
    budgets=policy.get("budgets_by_risk")
    if not isinstance(budgets,dict) or set(budgets)!={"R0","R1","R2","R3"}:
        raise AwuContextError("context budgets must exist for R0-R3")
    for risk,budget in budgets.items():
        if not isinstance(budget,dict) or set(budget)!={"max_primary_files","max_reference_files","max_total_kib"}:
            raise AwuContextError(f"{risk} context budget has invalid keys")
        for key,value in budget.items():
            minimum=0 if key=="max_reference_files" else 1
            if not isinstance(value,int) or isinstance(value,bool) or value<minimum:
                raise AwuContextError(f"{risk}.{key} is invalid")


def build_context_route(
    awu:dict[str,Any],
    awu_path:Path,
    policy:dict[str,Any],
)->dict[str,Any]:
    parent=awu["parent"]["manifest"]
    primary=list(policy["always_primary"])+[parent,str(awu_path.relative_to(ROOT))]
    local_kinds=set(policy["local_input_kinds"])
    for item in awu.get("inputs",[]):
        if not isinstance(item,dict) or item.get("kind") not in local_kinds:
            continue
        locator=item.get("locator")
        if not isinstance(locator,str):
            continue
        if _safe_repo_path(locator) is not None:
            primary.append(locator)
    primary=_dedupe(primary)
    reference=_dedupe(list(policy["always_reference"]))
    reference=[path for path in reference if path not in set(primary)]

    for path in primary+reference:
        if _safe_repo_path(path) is None:
            raise AwuContextError(f"required context file does not exist: {path}")

    total_bytes=sum((ROOT/path).stat().st_size for path in primary+reference)
    return {
        "awu_id":awu["id"],
        "primary_files":primary,
        "reference_files":reference,
        "primary_count":len(primary),
        "reference_count":len(reference),
        "total_bytes":total_bytes,
        "total_kib_ceil":(total_bytes+1023)//1024,
    }


def validate_context(
    awu:dict[str,Any],
    awu_path:Path,
    policy:dict[str,Any],
)->dict[str,Any]|None:
    contract=_module("awu_contract_for_context",ROOT/"scripts/governance/validate_agent_work_unit.py")
    risk=_module("awu_risk_for_context",ROOT/"scripts/governance/validate_awu_risk.py")
    try:
        contract.validate_awu(awu,source=str(awu_path))
        risk.validate_risk(awu,_load(ROOT/"config/governance/awu_risk_policy_v1.json"))
    except (contract.AgentWorkUnitError,risk.AwuRiskError) as exc:
        raise AwuContextError(str(exc)) from exc

    status=awu["status"]
    declared=awu["planning"]["context_budget"]
    risk_class=awu["planning"]["risk_class"]
    if status in set(policy["optional_statuses"]) and risk_class=="UNCLASSIFIED":
        if any(value is not None for value in declared.values()):
            raise AwuContextError("unclassified optional AWU must keep context budget null")
        return None

    if risk_class=="UNCLASSIFIED":
        raise AwuContextError("classified context budget requires classified risk")
    expected=policy["budgets_by_risk"][risk_class]
    if declared!=expected:
        raise AwuContextError(
            f"context budget mismatch for {risk_class}: declared={declared} expected={expected}"
        )

    route=build_context_route(awu,awu_path,policy)
    if route["primary_count"]>declared["max_primary_files"]:
        raise AwuContextError("primary context file budget exceeded")
    if route["reference_count"]>declared["max_reference_files"]:
        raise AwuContextError("reference context file budget exceeded")
    if route["total_kib_ceil"]>declared["max_total_kib"]:
        raise AwuContextError("context byte budget exceeded")
    return route


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths",nargs="*",type=Path)
    args=parser.parse_args()
    policy=_load(POLICY_PATH)
    paths=args.paths or [
        ROOT/"engineering/fixtures/agent_work_unit_v1.example.json",
        *sorted((ROOT/"engineering/fixtures/awu_graph_valid").glob("*.json")),
    ]
    try:
        validate_policy(policy)
        results=[]
        for path in paths:
            awu=_load(path)
            route=validate_context(awu,path.resolve(),policy)
            results.append((awu["id"],route))
    except AwuContextError as exc:
        print(f"AWU_CONTEXT_INVALID: {exc}",file=sys.stderr)
        return 1
    rendered=[]
    for awu_id,route in results:
        if route is None:
            rendered.append(f"{awu_id}:DEFERRED")
        else:
            rendered.append(
                f"{awu_id}:P{route['primary_count']}:R{route['reference_count']}:K{route['total_kib_ceil']}"
            )
    print("AWU_CONTEXT_VALID "+",".join(rendered))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
