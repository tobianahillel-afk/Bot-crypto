#!/usr/bin/env python3
"""Adversarial qualification for Agent Work Unit dependency DAG semantics."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


def _module()->ModuleType:
    path=ROOT/"scripts/governance/validate_agent_work_unit_graph.py"
    spec=importlib.util.spec_from_file_location("awu_graph_validator_selftest",path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"AWU graph negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    paths=sorted((ROOT/"engineering/fixtures/awu_graph_valid").glob("*.json"))
    nodes=mod.load_paths(paths)
    topo=mod.validate_graph(nodes)
    assert set(topo)==set(nodes)

    missing=copy.deepcopy(nodes)
    missing["ENG-02-DAG-WU03"]["depends_on"]=["ENG-02-DAG-WU99"]
    _expect(mod.AgentWorkUnitGraphError,lambda:mod.validate_graph(missing),"missing dependency")

    cycle=copy.deepcopy(nodes)
    cycle["ENG-02-DAG-WU01"]["depends_on"]=["ENG-02-DAG-WU03"]
    _expect(mod.AgentWorkUnitGraphError,lambda:mod.validate_graph(cycle),"dependency cycle")

    incomplete=copy.deepcopy(nodes)
    incomplete["ENG-02-DAG-WU01"]["status"]="PLANNED"
    incomplete["ENG-02-DAG-WU02"]["status"]="READY"
    _expect(mod.AgentWorkUnitGraphError,lambda:mod.validate_graph(incomplete),"READY with incomplete predecessor")

    ambiguous=copy.deepcopy(nodes)
    ambiguous["ENG-02-DAG-WU01"]["status"]="IN_PROGRESS"
    ambiguous["ENG-02-DAG-WU02"]["status"]="IN_PROGRESS"
    ambiguous["ENG-02-DAG-WU02"]["depends_on"]=[]
    _expect(mod.AgentWorkUnitGraphError,lambda:mod.validate_graph(ambiguous),"multiple active AWUs")

    future=copy.deepcopy(nodes)
    future["ENG-02-DAG-WU01"]["parent"]["task_id"]="ENG-02.3"
    future["ENG-02-DAG-WU02"]["parent"]["task_id"]="ENG-02.2"
    future["ENG-02-DAG-WU02"]["depends_on"]=["ENG-02-DAG-WU01"]
    future["ENG-02-DAG-WU01"]["status"]="DONE"
    _expect(mod.AgentWorkUnitGraphError,lambda:mod.validate_graph(future),"future parent task dependency")

    print("AGENT_WORK_UNIT_GRAPH_SELFTEST_PASS probes=5")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
