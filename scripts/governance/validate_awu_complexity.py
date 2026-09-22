#!/usr/bin/env python3
"""Recalculate and validate deterministic Agent Work Unit complexity scores."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=ROOT/"config/governance/awu_complexity_policy_v1.json"


class AwuComplexityError(ValueError):
    pass


def _json(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise AwuComplexityError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict):
        raise AwuComplexityError(f"{path} must contain an object")
    return value


def _contract()->ModuleType:
    path=ROOT/"scripts/governance/validate_agent_work_unit.py"
    spec=importlib.util.spec_from_file_location("awu_contract_for_complexity",path)
    if spec is None or spec.loader is None:
        raise AwuComplexityError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def validate_policy(policy:dict[str,Any])->None:
    if policy.get("schema_version")!=1 or policy.get("policy_kind")!="awu_complexity_policy_v1":
        raise AwuComplexityError("invalid complexity policy identity")
    factors=policy.get("factors")
    if not isinstance(factors,dict) or not factors:
        raise AwuComplexityError("complexity policy factors are required")
    for name,rule in factors.items():
        if not isinstance(rule,dict) or set(rule)!={"kind","weight","description"}:
            raise AwuComplexityError(f"factor {name} has invalid rule")
        if rule["kind"] not in {"count","boolean"}:
            raise AwuComplexityError(f"factor {name} has invalid kind")
        if not isinstance(rule["weight"],int) or isinstance(rule["weight"],bool) or rule["weight"]<=0:
            raise AwuComplexityError(f"factor {name} weight must be positive integer")
        if not isinstance(rule["description"],str) or not rule["description"]:
            raise AwuComplexityError(f"factor {name} description is required")


def calculate_score(awu:dict[str,Any],policy:dict[str,Any])->int:
    factors=awu["planning"]["complexity_factors"]
    rules=policy["factors"]
    if set(factors)!=set(rules):
        raise AwuComplexityError("AWU complexity factor set disagrees with policy")
    total=0
    for name,rule in rules.items():
        value=factors[name]
        if rule["kind"]=="boolean":
            if not isinstance(value,bool):
                raise AwuComplexityError(f"{name} must be boolean")
            units=1 if value else 0
        else:
            if not isinstance(value,int) or isinstance(value,bool) or value<0:
                raise AwuComplexityError(f"{name} must be non-negative integer")
            units=value
        total+=units*rule["weight"]
    return total


def _underdeclaration_checks(awu:dict[str,Any])->None:
    factors=awu["planning"]["complexity_factors"]
    output_kinds={item.get("kind") for item in awu.get("outputs",[]) if isinstance(item,dict)}
    if output_kinds&{"SCHEMA","CONTRACT"} and factors["contract_schema_families"]<1:
        raise AwuComplexityError("schema/contract output requires contract_schema_families >= 1")
    allowed=awu.get("scope",{}).get("allowed_paths",[])
    if any(path.startswith(".github/workflows") for path in allowed) and factors["ci_evidence_topology_change"] is not True:
        raise AwuComplexityError("workflow scope requires ci_evidence_topology_change=true")
    if any(path.startswith("src/crypto_quant_bot") for path in allowed) and factors["production_modules"]<1:
        raise AwuComplexityError("production scope requires production_modules >= 1")


def validate_complexity(awu:dict[str,Any],policy:dict[str,Any])->int:
    contract=_contract()
    try:
        contract.validate_awu(awu)
    except contract.AgentWorkUnitError as exc:
        raise AwuComplexityError(str(exc)) from exc
    _underdeclaration_checks(awu)
    score=calculate_score(awu,policy)
    declared=awu["planning"]["complexity_score"]
    if declared!=score:
        raise AwuComplexityError(f"complexity_score mismatch: declared={declared} calculated={score}")
    return score


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths",nargs="*",type=Path)
    args=parser.parse_args()
    policy=_json(POLICY_PATH)
    paths=args.paths or [
        ROOT/"engineering/fixtures/agent_work_unit_v1.example.json",
        *sorted((ROOT/"engineering/fixtures/awu_graph_valid").glob("*.json")),
    ]
    try:
        validate_policy(policy)
        scores=[]
        for path in paths:
            awu=_json(path)
            scores.append((awu["id"],validate_complexity(awu,policy)))
    except AwuComplexityError as exc:
        print(f"AWU_COMPLEXITY_INVALID: {exc}",file=sys.stderr)
        return 1
    print("AWU_COMPLEXITY_VALID "+",".join(f"{awu_id}:{score}" for awu_id,score in scores))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
