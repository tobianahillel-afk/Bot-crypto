#!/usr/bin/env python3
"""Validate staged or activated business-development unlock topology."""

from __future__ import annotations
import argparse, copy, json, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
POLICY=ROOT/"config/governance/business_unlock_activation_policy_v1.json"
PLAN=ROOT/"engineering/BUSINESS_DEVELOPMENT_UNLOCK_ACTIVATION_PLAN.json"
STATE=ROOT/"config/governance/project_state.json"
BM=ROOT/"business/lots/LOT-45.json"
BA=ROOT/"business/work_units/LOT-45.1-WU01.json"
BUSINESS_WU_DIR=ROOT/"business/work_units"

class ActivationError(ValueError): pass
def load(p:Path)->dict[str,Any]:
    try: v=json.loads(p.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: raise ActivationError(f"cannot load {p}: {e}") from e
    if not isinstance(v,dict): raise ActivationError(f"{p} must contain object")
    return v
def req(c:bool,m:str)->None:
    if not c: raise ActivationError(m)

def validate_policy(p:dict[str,Any])->None:
    req(p.get("schema_version")==1,"policy version")
    req(p.get("policy_kind")=="business_unlock_activation_policy_v1","policy kind")
    req(p.get("semantics")=="ELIGIBILITY_PLUS_DIRECT_HUMAN_AUTHORIZATION_ATOMIC_TERMINAL_ROUTE","policy semantics")
    req(p.get("explicit_human_action")=="BUSINESS_DEVELOPMENT_UNLOCK","human action drift")
    req(set(p.get("forbidden_authorization_sources",[]))=={"handoff","chat_history","model_memory","eligibility_alone","prior_agent_summary"},"authorization source floor")
    s=p.get("invariant_safety",{})
    req(s=={"runtime_max":"OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY","trade_allowed":False,"execution_allowed":False,"live_execution":"DISABLED","leverage":"FORBIDDEN","withdrawals":"FORBIDDEN"},"safety floor drift")

def validate_staged(plan:dict[str,Any], state:dict[str,Any], bm:dict[str,Any], ba:dict[str,Any], policy:dict[str,Any])->None:
    validate_policy(policy)
    req(plan.get("semantics")=="STAGED_NOT_EXECUTED","plan must remain staged")
    req(plan.get("status")=="STAGED_AWAITING_DIRECT_EXPLICIT_HUMAN_ACTION","staged status drift")
    req(state["engineering_track"]["phase"]=="BUILDING","staging must keep engineering BUILDING")
    req(state["business_track"]["development_status"]=="PAUSED","staging must keep business PAUSED")
    req(state["business_track"]["candidate"]["status"]=="SUSPENDED_CANDIDATE","candidate must remain suspended")
    req(state["business_track"]["next_lot"]=={"lot":46,"status":"LOCKED"},"Lot46 lock weakened")
    req(bm.get("id")=="LOT-45" and bm.get("status")=="PLANNED","business manifest must be staged PLANNED")
    req([t.get("status") for t in bm.get("tasks",[])]==["PLANNED","PLANNED"],"business tasks activated during staging")
    req(ba.get("id")=="LOT-45.1-WU01" and ba.get("status")=="PLANNED","business AWU activated during staging")
    req("Lot45 candidate mutation" in ba.get("scope",{}).get("forbidden_semantics",[]),"read-only candidate invariant missing")
    req(ba.get("scope",{}).get("scope_base_sha")=="TO_BE_BOUND_AT_ACTIVATION_HEAD","staged AWU prematurely bound")
    for k,v in policy["invariant_safety"].items(): req(state["safety"].get(k)==v,f"safety weakened: {k}")

def synthetic_activation(staged_state:dict[str,Any], bm:dict[str,Any], ba:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
    s=copy.deepcopy(staged_state); m=copy.deepcopy(bm); a=copy.deepcopy(ba)
    e=s["engineering_track"]; b=s["business_track"]
    e["phase"]="STABLE"; e["completed"]=list(e["completed"])+["ENG-09"]; e["active_lot"]=None; e["active_task"]=None; e["active_manifest"]=None; e["next_lot"]=None; e["blockers"]=[]
    b["development_status"]="ACTIVE"; b["candidate"]["status"]="ACTIVE_CANDIDATE"
    s["authority"]["active_manifest"]="business/lots/LOT-45.json"
    m["status"]="IN_PROGRESS"; m["tasks"][0]["status"]="IN_PROGRESS"
    a["status"]="IN_PROGRESS"; a["scope"]["scope_base_sha"]="ACTIVATION_HEAD_PLACEHOLDER"
    return s,m,a

def load_active_business_awu()->dict[str,Any]:
    active=[]
    for path in sorted(BUSINESS_WU_DIR.glob("*.json")):
        value=load(path)
        if value.get("status")=="IN_PROGRESS":
            active.append((path,value))
    req(len(active)==1,f"exactly one active business AWU required, found {len(active)}")
    path,a=active[0]
    parent=a.get("parent",{})
    req(
        parent.get("work_item_id")=="LOT-45"
        and parent.get("task_id")=="LOT-45.1"
        and parent.get("manifest")=="business/lots/LOT-45.json",
        f"active business maintenance route invalid: {path.name}",
    )
    forbidden=a.get("scope",{}).get("forbidden_semantics",[])
    req("Lot45 candidate mutation" in forbidden,"active business AWU lost candidate-mutation guard")
    req("candidate merge" in forbidden,"active business AWU lost candidate-merge guard")
    return a

def validate_activated(s:dict[str,Any],m:dict[str,Any],a:dict[str,Any],policy:dict[str,Any])->None:
    validate_policy(policy)
    e=s["engineering_track"]; b=s["business_track"]
    req(e["phase"]=="STABLE" and e["active_lot"] is None and e["active_task"] is None and e["active_manifest"] is None,"engineering not terminal")
    req("ENG-09" in e["completed"] and e["blockers"]==[],"ENG-09 completion/blocker transition invalid")
    req(b["development_status"]=="ACTIVE","business not ACTIVE")
    req(b["candidate"]["status"]=="ACTIVE_CANDIDATE" and b["candidate"]["state"]=="OPEN" and b["candidate"]["merged"] is False,"candidate authority invalid")
    req(b["next_lot"]=={"lot":46,"status":"LOCKED"},"Lot46 unlock forbidden")
    req(s["authority"]["active_manifest"]=="business/lots/LOT-45.json","business manifest authority missing")
    req(m.get("status")=="IN_PROGRESS","business manifest not active")
    req(m["tasks"][0]["status"]=="IN_PROGRESS" and sum(t["status"]=="IN_PROGRESS" for t in m["tasks"])==1,"business task cardinality invalid")
    req(a["status"]=="IN_PROGRESS","business AWU not active")
    parent=a.get("parent",{})
    req(
        parent.get("work_item_id")=="LOT-45"
        and parent.get("task_id")=="LOT-45.1"
        and parent.get("manifest")=="business/lots/LOT-45.json",
        "active business AWU parent route invalid",
    )
    forbidden=a.get("scope",{}).get("forbidden_semantics",[])
    req("Lot45 candidate mutation" in forbidden,"candidate mutation guard missing")
    req("candidate merge" in forbidden,"candidate merge guard missing")
    for k,v in policy["invariant_safety"].items(): req(s["safety"].get(k)==v,f"safety weakened: {k}")

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=["staged","synthetic-activated","activated"],default="staged"); args=ap.parse_args()
    try:
        p=load(POLICY); plan=load(PLAN); s=load(STATE); bm=load(BM); ba=load(BA)
        if args.mode=="staged":
            validate_staged(plan,s,bm,ba,p)
        elif args.mode=="synthetic-activated":
            ns,nm,na=synthetic_activation(s,bm,ba); validate_activated(ns,nm,na,p)
        else:
            active_awu=load_active_business_awu()
            validate_activated(s,bm,active_awu,p)
    except (ActivationError,KeyError,TypeError) as e:
        print(f"BUSINESS_ACTIVATION_INVALID: {e}",file=sys.stderr); return 1
    print(f"BUSINESS_ACTIVATION_VALID mode={args.mode}"); return 0
if __name__=="__main__": raise SystemExit(main())
