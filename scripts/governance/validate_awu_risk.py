#!/usr/bin/env python3
"""Calculate and enforce deterministic Agent Work Unit risk classes R0-R3."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=ROOT/"config/governance/awu_risk_policy_v1.json"


class AwuRiskError(ValueError):
    pass


def _load(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise AwuRiskError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict):
        raise AwuRiskError(f"{path} must contain an object")
    return value


def _module(name:str,path:Path)->ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise AwuRiskError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def validate_policy(policy:dict[str,Any])->None:
    if policy.get("schema_version")!=1 or policy.get("policy_kind")!="awu_risk_policy_v1":
        raise AwuRiskError("invalid risk policy identity")
    if policy.get("order")!=["R0","R1","R2","R3"]:
        raise AwuRiskError("risk order drift")
    mapping=policy.get("reason_to_class")
    if not isinstance(mapping,dict) or not mapping:
        raise AwuRiskError("reason_to_class mapping is required")
    if any(value not in {"R1","R2","R3"} for value in mapping.values()):
        raise AwuRiskError("risk reason maps to invalid class")
    threshold=policy.get("thresholds",{}).get("r2_complexity_score_min")
    if not isinstance(threshold,int) or isinstance(threshold,bool) or threshold<1:
        raise AwuRiskError("R2 complexity threshold must be positive integer")


def calculate_risk(awu:dict[str,Any],policy:dict[str,Any])->tuple[str,list[str]]:
    planning=awu["planning"]
    factors=planning["complexity_factors"]
    reasons:set[str]=set()

    if factors["production_modules"]>0:
        reasons.add("PRODUCTION_MODULE_CHANGE")
    if factors["contract_schema_families"]>0:
        reasons.add("CONTRACT_OR_SCHEMA_CHANGE")
    if factors["policy_config_families"]>0:
        reasons.add("POLICY_OR_CONFIG_CHANGE")
    if factors["ci_evidence_topology_change"]:
        reasons.add("CI_EVIDENCE_TOPOLOGY_CHANGE")

    if factors["persistence_checksum_boundary"]:
        reasons.add("PERSISTENCE_OR_CHECKSUM_BOUNDARY")
    if factors["math_numeric_semantics"]:
        reasons.add("MATH_OR_NUMERIC_SEMANTICS")
    if factors["temporal_lineage_semantics"]:
        reasons.add("TEMPORAL_OR_LINEAGE_SEMANTICS")
    if factors["cross_domain_interfaces"]>0:
        reasons.add("CROSS_DOMAIN_INTERFACE")
    if factors["state_machine_or_concurrency"]:
        reasons.add("STATE_MACHINE_OR_CONCURRENCY")
    if factors["security_trust_boundary"]:
        reasons.add("SECURITY_OR_TRUST_BOUNDARY")
    if factors["dependency_change"]:
        reasons.add("DEPENDENCY_CHANGE")
    if planning["complexity_score"]>=policy["thresholds"]["r2_complexity_score_min"]:
        reasons.add("HIGH_COMPLEXITY_SCORE")

    if factors["risk_execution_permission"]:
        reasons.add("RISK_OR_EXECUTION_PERMISSION")
    allowed=awu.get("scope",{}).get("allowed_paths",[])
    if any(
        any(path.startswith(prefix) for prefix in policy["critical_path_prefixes"])
        for path in allowed
    ):
        reasons.add("CRITICAL_EXECUTION_SCOPE")

    order=policy["order"]
    mapping=policy["reason_to_class"]
    level=0
    for reason in reasons:
        level=max(level,order.index(mapping[reason]))
    return order[level],sorted(reasons)


def validate_risk(awu:dict[str,Any],policy:dict[str,Any])->tuple[str,list[str]]:
    contract=_module("awu_contract_for_risk",ROOT/"scripts/governance/validate_agent_work_unit.py")
    complexity=_module("awu_complexity_for_risk",ROOT/"scripts/governance/validate_awu_complexity.py")
    split=_module("awu_split_for_risk",ROOT/"scripts/governance/validate_awu_split.py")
    try:
        contract.validate_awu(awu)
        complexity.validate_complexity(
            awu,_load(ROOT/"config/governance/awu_complexity_policy_v1.json")
        )
        split.validate_split(
            awu,_load(ROOT/"config/governance/awu_split_policy_v1.json")
        )
    except (contract.AgentWorkUnitError,complexity.AwuComplexityError,split.AwuSplitError) as exc:
        raise AwuRiskError(str(exc)) from exc

    calculated,reasons=calculate_risk(awu,policy)
    declared=awu["planning"]["risk_class"]
    if declared=="UNCLASSIFIED":
        if awu["status"] not in set(policy["unclassified_allowed_statuses"]):
            raise AwuRiskError(f"executable AWU cannot remain UNCLASSIFIED: {awu['status']}")
        return calculated,reasons
    if policy.get("exact_class_required") is True and declared!=calculated:
        raise AwuRiskError(f"risk_class mismatch: declared={declared} calculated={calculated}")
    return calculated,reasons


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
            risk,reasons=validate_risk(awu,policy)
            results.append((awu["id"],risk,reasons))
    except AwuRiskError as exc:
        print(f"AWU_RISK_INVALID: {exc}",file=sys.stderr)
        return 1
    print(
        "AWU_RISK_VALID "+
        ",".join(
            f"{awu_id}:{risk}:{'|'.join(reasons) if reasons else 'NO_REASON'}"
            for awu_id,risk,reasons in results
        )
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
