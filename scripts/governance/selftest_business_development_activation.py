#!/usr/bin/env python3
"""Adversarial tests for staged business activation topology."""
from __future__ import annotations
import copy, importlib.util, sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
def mod():
    p=ROOT/"scripts/governance/validate_business_development_activation.py"
    s=importlib.util.spec_from_file_location("activation_selftest",p); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m); return m
def expect(exc,fn,label):
    try: fn()
    except exc: return
    raise AssertionError(f"activation negative scenario passed: {label}")
def main():
    m=mod(); p=m.load(m.POLICY); plan=m.load(m.PLAN); s=m.load(m.STATE); bm=m.load(m.BM); ba=m.load(m.BA)
    lifecycle=s["business_track"]["development_status"]
    if lifecycle=="PAUSED":
        m.validate_staged(plan,s,bm,ba,p)
        ns,nm,na=m.synthetic_activation(s,bm,ba); m.validate_activated(ns,nm,na,p)
        x=copy.deepcopy(s); x["business_track"]["development_status"]="ACTIVE"; expect(m.ActivationError,lambda:m.validate_staged(plan,x,bm,ba,p),"staging auto-activation")
    elif lifecycle=="ACTIVE":
        active_awu=m.load_active_business_awu()
        m.validate_activated(s,bm,active_awu,p)
        ns,nm,na=copy.deepcopy(s),copy.deepcopy(bm),copy.deepcopy(active_awu)
    else:
        raise AssertionError(f"unsupported lifecycle in activation selftest: {lifecycle}")
    x=copy.deepcopy(ns); x["business_track"]["candidate"]["status"]="SUSPENDED_CANDIDATE"; expect(m.ActivationError,lambda:m.validate_activated(x,nm,na,p),"suspended candidate")
    x=copy.deepcopy(ns); x["business_track"]["next_lot"]["status"]="OPEN"; expect(m.ActivationError,lambda:m.validate_activated(x,nm,na,p),"Lot46 unlock")
    x=copy.deepcopy(ns); x["safety"]["trade_allowed"]=True; expect(m.ActivationError,lambda:m.validate_activated(x,nm,na,p),"trade authority")
    x=copy.deepcopy(nm); x["tasks"][1]["status"]="IN_PROGRESS"; expect(m.ActivationError,lambda:m.validate_activated(ns,x,na,p),"multiple business tasks")
    x=copy.deepcopy(na); x["parent"]["task_id"]="LOT-45.2"; expect(m.ActivationError,lambda:m.validate_activated(ns,nm,x,p),"wrong active business task")
    if lifecycle=="PAUSED":
        x=copy.deepcopy(ba); x["status"]="IN_PROGRESS"; expect(m.ActivationError,lambda:m.validate_staged(plan,s,bm,x,p),"premature business AWU")
    x=copy.deepcopy(p); x["explicit_human_action"]="continue"; expect(m.ActivationError,lambda:m.validate_policy(x),"generic continue authorization")
    print("BUSINESS_ACTIVATION_SELFTEST_PASS probes=9"); return 0
if __name__ == "__main__":
    raise SystemExit(main())
