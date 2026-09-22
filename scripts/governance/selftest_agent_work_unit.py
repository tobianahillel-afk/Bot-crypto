#!/usr/bin/env python3
"""Negative qualification for Agent Work Unit V1 contract."""

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
    path=ROOT/"scripts/governance/validate_agent_work_unit.py"
    spec=importlib.util.spec_from_file_location("awu_validator",path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _fixture()->dict[str,Any]:
    value=json.loads((ROOT/"engineering/fixtures/agent_work_unit_v1.example.json").read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError("AWU fixture must be an object")
    return value


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"AWU negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    base=_fixture()
    mod.validate_awu(base,source="fixture")

    unknown=copy.deepcopy(base)
    unknown["surprise"]=True
    _expect(mod.AgentWorkUnitError,lambda:mod.validate_awu(unknown),"unknown field")

    bad_parent=copy.deepcopy(base)
    bad_parent["parent"]["task_id"]="ENG-01.1"
    _expect(mod.AgentWorkUnitError,lambda:mod.validate_awu(bad_parent),"foreign parent task")

    self_dep=copy.deepcopy(base)
    self_dep["depends_on"]=[self_dep["id"]]
    _expect(mod.AgentWorkUnitError,lambda:mod.validate_awu(self_dep),"self dependency")

    duplicate=copy.deepcopy(base)
    duplicate["scope"]["allowed_paths"].append(duplicate["scope"]["allowed_paths"][0])
    _expect(mod.AgentWorkUnitError,lambda:mod.validate_awu(duplicate),"duplicate allowed path")

    done_unclassified=copy.deepcopy(base)
    done_unclassified["status"]="DONE"
    _expect(mod.AgentWorkUnitError,lambda:mod.validate_awu(done_unclassified),"DONE unclassified")

    bad_sha=copy.deepcopy(base)
    bad_sha["scope"]["scope_base_sha"]="not-a-sha"
    _expect(mod.AgentWorkUnitError,lambda:mod.validate_awu(bad_sha),"invalid scope base")

    print("AGENT_WORK_UNIT_SELFTEST_PASS probes=6")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
