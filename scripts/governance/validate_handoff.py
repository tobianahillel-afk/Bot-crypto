#!/usr/bin/env python3
"""Validate Engineering Handoff V2 against permanent state and the active AWU."""

from __future__ import annotations
import argparse, copy, importlib.util, json, re, sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
STATE_PATH=ROOT/"config/governance/project_state.json"
HANDOFF_PATH=ROOT/"engineering/handoff/CURRENT.json"
SCHEMA_PATH=ROOT/"engineering/HANDOFF_SCHEMA.json"
SHA40_RE=re.compile(r"^[0-9a-f]{40}$")
RUN_RE=re.compile(r"^https://github\.com/tobianahillel-afk/Bot-crypto/actions/runs/[0-9]+$")
READ_ORDER=["AGENTS.md","config/governance/project_state.json","engineering/CONTEXT_MAP.json","engineering/handoff/CURRENT.json"]
STALE_WHEN=["STATE_ACTIVE_WORK_MISMATCH","ACTIVE_AWU_MISMATCH","MAIN_SHA_MISMATCH","BUSINESS_CANDIDATE_HEAD_MISMATCH","BUSINESS_HOLD_CHANGED","SAFETY_SNAPSHOT_CHANGED","STOP_CONDITIONS_CHANGED"]

class HandoffError(ValueError):
    pass

def _load(path:Path)->dict[str,Any]:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise HandoffError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict): raise HandoffError(f"{path} must contain an object")
    return value

def _module(name:str,path:Path)->ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise HandoffError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module); return module

def _expected_snapshot(state:dict[str,Any])->dict[str,Any]:
    e,b,s=state["engineering_track"],state["business_track"],state["safety"]
    return {"engineering_phase":e["phase"],"active_lot":e["active_lot"],"active_task":e["active_task"],"active_manifest":e["active_manifest"],"business_development":b["development_status"],"lot46_status":b["next_lot"]["status"],"runtime_max":s["runtime_max"],"trade_allowed":s["trade_allowed"],"execution_allowed":s["execution_allowed"],"live_execution":s["live_execution"],"open_findings":[x["id"] for x in state.get("findings",[]) if x.get("observed")]}

def _expected_external(state:dict[str,Any])->dict[str,Any]:
    o=state["external_observations"]; c=o["business_candidate"]
    return {"default_branch":"main","main_sha":o["main"]["sha"],"main_branch_protected":o["main"]["branch_protected"],"rulesets_count":o["rulesets_count"],"lot45_pr":c["pr"],"lot45_head_sha":c["head"],"lot45_state":c["state"],"lot45_merged":c["merged"]}

def _expected_next(state:dict[str,Any])->dict[str,Any]:
    e=state["engineering_track"]; return {"active_lot":e["active_lot"],"active_task":e["active_task"],"active_manifest":e["active_manifest"]}

def _validate_schema_contract(schema:dict[str,Any])->None:
    if schema.get("title")!="Crypto Quant Bot Engineering Handoff V2": raise HandoffError("handoff schema title/version drift")
    expected=["schema_version","kind","workstream","status","authority","external_git_observation","engineering_branch","state_snapshot","active_checkpoint","resume_read_order","recent_completed","current_objective","next_action","blockers","validation_evidence","stop_conditions","stale_when","next_engineering"]
    if schema.get("required")!=expected: raise HandoffError("handoff schema required-field order/set drift")
    props=schema.get("properties")
    if not isinstance(props,dict): raise HandoffError("handoff schema properties missing")
    if props.get("schema_version",{}).get("const")!=2 or props.get("kind",{}).get("const")!="engineering_handoff": raise HandoffError("handoff schema identity drift")
    if props.get("recent_completed",{}).get("maxItems")!=8 or props.get("validation_evidence",{}).get("maxItems")!=12: raise HandoffError("handoff bounds drift")

def _active_checkpoint()->dict[str,Any]:
    resolver=_module("handoff_active_awu",ROOT/"scripts/governance/resolve_active_awu.py")
    try: path,awu,_=resolver.resolve_active_awu()
    except resolver.ActiveAwuError as exc: raise HandoffError(str(exc)) from exc
    return {"track":"ENGINEERING","awu_id":awu["id"],"awu_path":path.relative_to(ROOT).as_posix(),"parent_manifest":awu["parent"]["manifest"],"scope_base_sha":awu["scope"]["scope_base_sha"],"risk_class":awu["planning"]["risk_class"],"complexity_score":awu["planning"]["complexity_score"]}

def validate_handoff(state:dict[str,Any],handoff:dict[str,Any])->None:
    _validate_schema_contract(_load(SCHEMA_PATH))
    if state.get("state_kind")!="project_state_v1": raise HandoffError("handoff authority must be permanent project_state_v1")
    if handoff.get("schema_version")!=2 or handoff.get("kind")!="engineering_handoff" or handoff.get("workstream")!="DEVELOPMENT_ENGINE": raise HandoffError("unsupported handoff identity")
    if handoff.get("authority")!={"state_source":"config/governance/project_state.json","context_map":"engineering/CONTEXT_MAP.json","handoff_role":"RESUME_HINT_NOT_AUTHORITY"}: raise HandoffError("handoff authority declaration drift")
    e=state["engineering_track"]
    expected_status="BLOCKED" if e["blockers"] else ("COMPLETE" if e["phase"]=="COMPLETE" else "IN_PROGRESS")
    if handoff.get("status")!=expected_status: raise HandoffError("handoff lifecycle status disagrees with engineering track")
    if handoff.get("engineering_branch")!=e["branch"]: raise HandoffError("handoff engineering branch disagrees with canonical state")
    if handoff.get("state_snapshot")!=_expected_snapshot(state): raise HandoffError("handoff state/safety snapshot is stale")
    if handoff.get("external_git_observation")!=_expected_external(state): raise HandoffError("handoff external Git observation is stale")
    if handoff.get("next_engineering")!=_expected_next(state): raise HandoffError("handoff next_engineering disagrees with canonical state")
    if handoff.get("blockers")!=e["blockers"]: raise HandoffError("handoff blockers disagree with engineering track")
    if handoff.get("stop_conditions")!=state["stop_conditions"]: raise HandoffError("handoff stop conditions disagree with canonical state")
    if handoff.get("resume_read_order")!=READ_ORDER or handoff.get("stale_when")!=STALE_WHEN: raise HandoffError("handoff resume/stale semantics drift")
    checkpoint=handoff.get("active_checkpoint")
    if checkpoint!=_active_checkpoint(): raise HandoffError("handoff active checkpoint disagrees with active AWU")
    recent=handoff.get("recent_completed")
    if not isinstance(recent,list) or not 1<=len(recent)<=8 or len(recent)!=len(set(recent)) or any(not isinstance(x,str) or not x.strip() for x in recent): raise HandoffError("handoff recent_completed invalid/unbounded")
    for field in ("current_objective","next_action"):
        value=handoff.get(field)
        if not isinstance(value,str) or not value.strip() or len(value)>2000: raise HandoffError(f"handoff {field} missing/unbounded")
    evidence=handoff.get("validation_evidence")
    if not isinstance(evidence,list) or not 1<=len(evidence)<=12: raise HandoffError("handoff validation_evidence invalid/unbounded")
    bound=False; refs=set()
    for item in evidence:
        if not isinstance(item,dict) or set(item)!={"class","status","ref","head_sha","scope"}: raise HandoffError("handoff evidence shape invalid")
        if item["class"]!="GITHUB_ACTIONS" or item["status"]!="PASS" or RUN_RE.fullmatch(item["ref"]) is None or SHA40_RE.fullmatch(item["head_sha"]) is None or not isinstance(item["scope"],str) or not item["scope"]: raise HandoffError("handoff evidence invalid")
        if item["ref"] in refs: raise HandoffError("handoff evidence ref duplicated")
        refs.add(item["ref"]); bound = bound or item["head_sha"]==checkpoint["scope_base_sha"]
    if not bound: raise HandoffError("handoff lacks PASS evidence bound to active AWU scope_base_sha")

def _expect(fn:Any,label:str)->None:
    try: fn()
    except HandoffError: return
    raise AssertionError(f"handoff negative scenario unexpectedly passed: {label}")

def self_check(state:dict[str,Any],handoff:dict[str,Any])->None:
    validate_handoff(state,handoff)
    cases=[]
    def add(label,mut):
        value=copy.deepcopy(handoff); mut(value); cases.append((label,lambda v=value:validate_handoff(state,v)))
    add("legacy schema",lambda x:x.__setitem__("schema_version",1))
    add("stale task",lambda x:x["state_snapshot"].__setitem__("active_task","ENG-99.99"))
    add("bridge authority",lambda x:x["authority"].__setitem__("state_source","engineering/STATE.json"))
    add("stale AWU",lambda x:x["active_checkpoint"].__setitem__("awu_id","ENG-99-WU99"))
    add("stale scope",lambda x:x["active_checkpoint"].__setitem__("scope_base_sha","0"*40))
    add("stale next",lambda x:x["next_engineering"].__setitem__("active_task","ENG-99.99"))
    add("stale main",lambda x:x["external_git_observation"].__setitem__("main_sha","0"*40))
    add("stale candidate",lambda x:x["external_git_observation"].__setitem__("lot45_head_sha","0"*40))
    add("malformed evidence",lambda x:x["validation_evidence"][0].__setitem__("head_sha","bad"))
    add("unbound evidence",lambda x:[item.__setitem__("head_sha","1"*40) for item in x["validation_evidence"]])
    add("stop drift",lambda x:x.__setitem__("stop_conditions",x["stop_conditions"][:-1]))
    add("history bound",lambda x:x.__setitem__("recent_completed",[f"item-{i}" for i in range(9)]))
    for label,fn in cases:_expect(fn,label)
    print(f"HANDOFF_SELF_CHECK_PASS probes={len(cases)}")

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--state",type=Path,default=STATE_PATH); parser.add_argument("--handoff",type=Path,default=HANDOFF_PATH); parser.add_argument("--self-check",action="store_true"); args=parser.parse_args()
    try:
        state=_load(args.state); handoff=_load(args.handoff)
        self_check(state,handoff) if args.self_check else validate_handoff(state,handoff)
    except (HandoffError,AssertionError) as exc:
        print(f"HANDOFF_INVALID: {exc}",file=sys.stderr); return 1
    print("HANDOFF_SELF_CHECK_VALID" if args.self_check else "HANDOFF_VALID"); return 0

if __name__=="__main__": raise SystemExit(main())
