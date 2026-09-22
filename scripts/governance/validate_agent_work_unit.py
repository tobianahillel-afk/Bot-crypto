#!/usr/bin/env python3
"""Validate one bounded Agent Work Unit V1 with standard-library semantics."""

from __future__ import annotations

import argparse,json,re,sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
ID_RE=re.compile(r"^[A-Z][A-Z0-9_-]*(?:[.-][A-Z0-9_-]+)*-WU[0-9]{2,}$")
PARENT_RE=re.compile(r"^[A-Z][A-Z0-9_-]*(?:[.-][A-Z0-9_-]+)*$")
SHA40=re.compile(r"^[0-9a-f]{40}$")
STATUSES={"PLANNED","READY","IN_PROGRESS","BLOCKED","DONE"}
RISKS={"UNCLASSIFIED","R0","R1","R2","R3"}
TIERS={"T0","T1","T2","T3","T4"}
ARTIFACT_KINDS={"FILE","SCHEMA","CONFIG","CONTRACT","TEST","EVIDENCE","STATE","API","OTHER"}
COUNT_FACTORS={"production_modules","contract_schema_families","policy_config_families","cross_domain_interfaces"}
BOOL_FACTORS={
    "persistence_checksum_boundary","math_numeric_semantics","temporal_lineage_semantics",
    "state_machine_or_concurrency","security_trust_boundary","risk_execution_permission",
    "dependency_change","ci_evidence_topology_change",
}
SIZE_FIELDS={
    "business_domains","files_touched","executable_loc_changed","new_public_behaviors",
    "contract_families","independent_algorithms","state_machines","trust_boundaries","new_dependencies",
}
REQUIRED={
    "schema_version","kind","id","status","parent","title","objective","non_goals",
    "depends_on","inputs","outputs","scope","contracts","planning","validation","done_when"
}


class AgentWorkUnitError(ValueError): pass


def _load(path:Path)->dict[str,Any]:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise AgentWorkUnitError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict): raise AgentWorkUnitError(f"{path} must contain an object")
    return value


def _string(value:Any,field:str)->str:
    if not isinstance(value,str) or not value.strip(): raise AgentWorkUnitError(f"{field} must be a non-empty string")
    return value


def _unique_strings(value:Any,field:str,*,non_empty:bool)->list[str]:
    if not isinstance(value,list) or (non_empty and not value): raise AgentWorkUnitError(f"{field} must be {'non-empty ' if non_empty else ''}list")
    if any(not isinstance(item,str) or not item.strip() for item in value): raise AgentWorkUnitError(f"{field} must contain non-empty strings")
    if len(value)!=len(set(value)): raise AgentWorkUnitError(f"{field} must not contain duplicates")
    return value


def _artifact_refs(value:Any,field:str)->None:
    if not isinstance(value,list) or not value: raise AgentWorkUnitError(f"{field} must be a non-empty list")
    seen:set[tuple[str,str]]=set()
    for index,item in enumerate(value):
        if not isinstance(item,dict) or set(item)!={"name","kind","locator"}: raise AgentWorkUnitError(f"{field}[{index}] must contain only name/kind/locator")
        name=_string(item["name"],f"{field}[{index}].name"); locator=_string(item["locator"],f"{field}[{index}].locator")
        if item["kind"] not in ARTIFACT_KINDS: raise AgentWorkUnitError(f"{field}[{index}].kind is invalid")
        key=(name,locator)
        if key in seen: raise AgentWorkUnitError(f"{field} contains duplicate artifact reference {key}")
        seen.add(key)


def validate_awu(awu:dict[str,Any],*,source:str="<awu>")->None:
    keys=set(awu); missing=sorted(REQUIRED-keys); unknown=sorted(keys-REQUIRED)
    if missing: raise AgentWorkUnitError(f"{source}: missing keys: {missing}")
    if unknown: raise AgentWorkUnitError(f"{source}: unknown top-level keys: {unknown}")
    if awu["schema_version"]!=1 or awu["kind"]!="agent_work_unit": raise AgentWorkUnitError(f"{source}: invalid schema identity")
    awu_id=_string(awu["id"],f"{source}.id")
    if ID_RE.fullmatch(awu_id) is None: raise AgentWorkUnitError(f"{source}: invalid AWU id {awu_id!r}")
    if awu["status"] not in STATUSES: raise AgentWorkUnitError(f"{source}: invalid status")
    _string(awu["title"],f"{source}.title"); _string(awu["objective"],f"{source}.objective")
    _unique_strings(awu["non_goals"],f"{source}.non_goals",non_empty=True)
    deps=_unique_strings(awu["depends_on"],f"{source}.depends_on",non_empty=False)
    if awu_id in deps: raise AgentWorkUnitError(f"{source}: AWU cannot depend on itself")
    if any(ID_RE.fullmatch(dep) is None for dep in deps): raise AgentWorkUnitError(f"{source}: dependency id is invalid")

    parent=awu["parent"]
    if not isinstance(parent,dict) or set(parent)!={"work_item_id","task_id","manifest"}: raise AgentWorkUnitError(f"{source}.parent has invalid keys")
    parent_id=_string(parent["work_item_id"],f"{source}.parent.work_item_id"); task_id=_string(parent["task_id"],f"{source}.parent.task_id")
    if PARENT_RE.fullmatch(parent_id) is None or PARENT_RE.fullmatch(task_id) is None or not task_id.startswith(f"{parent_id}."): raise AgentWorkUnitError(f"{source}: invalid parent binding")
    manifest=_load(ROOT/_string(parent["manifest"],f"{source}.parent.manifest"))
    if manifest.get("id")!=parent_id or task_id not in [t.get("id") for t in manifest.get("tasks",[]) if isinstance(t,dict)]: raise AgentWorkUnitError(f"{source}: parent manifest/task mismatch")

    _artifact_refs(awu["inputs"],f"{source}.inputs"); _artifact_refs(awu["outputs"],f"{source}.outputs")
    scope=awu["scope"]
    if not isinstance(scope,dict) or set(scope)!={"scope_base_sha","allowed_paths","forbidden_paths","forbidden_semantics"}: raise AgentWorkUnitError(f"{source}.scope has invalid keys")
    if not isinstance(scope["scope_base_sha"],str) or SHA40.fullmatch(scope["scope_base_sha"]) is None: raise AgentWorkUnitError(f"{source}: scope base must be SHA-40")
    allowed=_unique_strings(scope["allowed_paths"],f"{source}.scope.allowed_paths",non_empty=True)
    forbidden=_unique_strings(scope["forbidden_paths"],f"{source}.scope.forbidden_paths",non_empty=False)
    _unique_strings(scope["forbidden_semantics"],f"{source}.scope.forbidden_semantics",non_empty=True)
    if set(allowed)&set(forbidden): raise AgentWorkUnitError(f"{source}: exact allowed/forbidden overlap")

    contracts=awu["contracts"]
    if not isinstance(contracts,dict) or set(contracts)!={"required_invariants","acceptance_criteria"}: raise AgentWorkUnitError(f"{source}.contracts has invalid keys")
    _unique_strings(contracts["required_invariants"],f"{source}.contracts.required_invariants",non_empty=True)
    _unique_strings(contracts["acceptance_criteria"],f"{source}.contracts.acceptance_criteria",non_empty=True)

    planning=awu["planning"]
    expected={"risk_class","complexity_factors","complexity_score","size_estimate","split_required","split_reasons","context_budget"}
    if not isinstance(planning,dict) or set(planning)!=expected: raise AgentWorkUnitError(f"{source}.planning has invalid keys")
    if planning["risk_class"] not in RISKS: raise AgentWorkUnitError(f"{source}: invalid risk_class")
    factors=planning["complexity_factors"]
    if not isinstance(factors,dict) or set(factors)!=(COUNT_FACTORS|BOOL_FACTORS): raise AgentWorkUnitError(f"{source}: invalid complexity factor set")
    for key in COUNT_FACTORS:
        if not isinstance(factors[key],int) or isinstance(factors[key],bool) or factors[key]<0: raise AgentWorkUnitError(f"{source}: invalid count factor {key}")
    for key in BOOL_FACTORS:
        if not isinstance(factors[key],bool): raise AgentWorkUnitError(f"{source}: invalid boolean factor {key}")
    score=planning["complexity_score"]
    if not isinstance(score,int) or isinstance(score,bool) or score<0: raise AgentWorkUnitError(f"{source}: invalid complexity_score")

    size=planning["size_estimate"]
    if not isinstance(size,dict) or set(size)!=SIZE_FIELDS: raise AgentWorkUnitError(f"{source}: invalid size_estimate")
    for key,value in size.items():
        minimum=1 if key in {"business_domains","files_touched"} else 0
        if not isinstance(value,int) or isinstance(value,bool) or value<minimum: raise AgentWorkUnitError(f"{source}: invalid size estimate {key}")

    if not isinstance(planning["split_required"],bool): raise AgentWorkUnitError(f"{source}: split_required must be boolean")
    _unique_strings(planning["split_reasons"],f"{source}.planning.split_reasons",non_empty=False)

    budget=planning["context_budget"]
    if not isinstance(budget,dict) or set(budget)!={"max_primary_files","max_reference_files","max_total_kib"}: raise AgentWorkUnitError(f"{source}: invalid context_budget")
    for key,value in budget.items():
        minimum=0 if key=="max_reference_files" else 1
        if value is not None and (not isinstance(value,int) or isinstance(value,bool) or value<minimum): raise AgentWorkUnitError(f"{source}: invalid context budget {key}")

    validation=awu["validation"]
    if not isinstance(validation,dict) or set(validation)!={"required_tiers","target_commands"}: raise AgentWorkUnitError(f"{source}.validation has invalid keys")
    tiers=_unique_strings(validation["required_tiers"],f"{source}.validation.required_tiers",non_empty=True)
    if any(t not in TIERS for t in tiers): raise AgentWorkUnitError(f"{source}: invalid validation tier")
    _unique_strings(validation["target_commands"],f"{source}.validation.target_commands",non_empty=False)
    _unique_strings(awu["done_when"],f"{source}.done_when",non_empty=True)

    if awu["status"]=="DONE":
        if planning["risk_class"]=="UNCLASSIFIED": raise AgentWorkUnitError(f"{source}: DONE requires classified risk")
        if planning["split_required"]: raise AgentWorkUnitError(f"{source}: DONE cannot require split")
        if any(value is None for value in budget.values()): raise AgentWorkUnitError(f"{source}: DONE requires complete context budget")


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("paths",nargs="*",type=Path); args=parser.parse_args()
    paths=args.paths or [ROOT/"engineering/fixtures/agent_work_unit_v1.example.json"]
    try:
        for path in paths: validate_awu(_load(path),source=str(path))
    except AgentWorkUnitError as exc:
        print(f"AGENT_WORK_UNIT_INVALID: {exc}",file=sys.stderr); return 1
    print(f"AGENT_WORK_UNIT_VALID count={len(paths)}"); return 0


if __name__=="__main__": raise SystemExit(main())
