#!/usr/bin/env python3
"""Validate a complete Agent Work Unit dependency DAG."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


class AgentWorkUnitGraphError(ValueError):
    pass


def _awu_module()->ModuleType:
    path=ROOT/"scripts/governance/validate_agent_work_unit.py"
    spec=importlib.util.spec_from_file_location("awu_contract_validator_for_graph",path)
    if spec is None or spec.loader is None:
        raise AgentWorkUnitGraphError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _load(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise AgentWorkUnitGraphError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict):
        raise AgentWorkUnitGraphError(f"{path} must contain an object")
    return value


def _parent_task_index(awu:dict[str,Any], cache:dict[str,dict[str,int]])->int:
    parent=awu["parent"]
    manifest_path=parent["manifest"]
    task_id=parent["task_id"]
    if manifest_path not in cache:
        manifest=_load(ROOT/manifest_path)
        tasks=manifest.get("tasks")
        if not isinstance(tasks,list):
            raise AgentWorkUnitGraphError(f"{manifest_path}: tasks must be a list")
        mapping={
            task.get("id"):index
            for index,task in enumerate(tasks)
            if isinstance(task,dict) and isinstance(task.get("id"),str)
        }
        cache[manifest_path]=mapping
    mapping=cache[manifest_path]
    if task_id not in mapping:
        raise AgentWorkUnitGraphError(f"parent task {task_id} not found in {manifest_path}")
    return mapping[task_id]


def validate_graph(nodes:dict[str,dict[str,Any]])->list[str]:
    if not nodes:
        raise AgentWorkUnitGraphError("AWU graph is empty")

    contract=_awu_module()
    for awu_id,node in nodes.items():
        try:
            contract.validate_awu(node,source=awu_id)
        except contract.AgentWorkUnitError as exc:
            raise AgentWorkUnitGraphError(str(exc)) from exc
        if node.get("id")!=awu_id:
            raise AgentWorkUnitGraphError(f"graph key {awu_id} disagrees with embedded id")

    for awu_id,node in nodes.items():
        for dep in node["depends_on"]:
            if dep not in nodes:
                raise AgentWorkUnitGraphError(f"{awu_id}: missing dependency {dep}")

    visiting:set[str]=set()
    visited:set[str]=set()
    topo:list[str]=[]

    def visit(awu_id:str)->None:
        if awu_id in visited:
            return
        if awu_id in visiting:
            raise AgentWorkUnitGraphError(f"dependency cycle detected at {awu_id}")
        visiting.add(awu_id)
        for dep in nodes[awu_id]["depends_on"]:
            visit(dep)
        visiting.remove(awu_id)
        visited.add(awu_id)
        topo.append(awu_id)

    for awu_id in sorted(nodes):
        visit(awu_id)

    task_cache:dict[str,dict[str,int]]={}
    for awu_id,node in nodes.items():
        node_parent=node["parent"]
        node_index=_parent_task_index(node,task_cache)
        for dep_id in node["depends_on"]:
            dep=nodes[dep_id]
            dep_parent=dep["parent"]
            if dep_parent["work_item_id"]==node_parent["work_item_id"]:
                dep_index=_parent_task_index(dep,task_cache)
                if dep_index>node_index:
                    raise AgentWorkUnitGraphError(
                        f"{awu_id}: dependency {dep_id} belongs to a future parent task"
                    )

        if node["status"] in {"READY","IN_PROGRESS","DONE"}:
            incomplete=[
                dep_id
                for dep_id in node["depends_on"]
                if nodes[dep_id]["status"]!="DONE"
            ]
            if incomplete:
                raise AgentWorkUnitGraphError(
                    f"{awu_id}: executable/completed node has incomplete dependencies {incomplete}"
                )

    active_by_parent:dict[tuple[str,str],list[str]]={}
    for awu_id,node in nodes.items():
        if node["status"]=="IN_PROGRESS":
            parent=node["parent"]
            key=(parent["work_item_id"],parent["task_id"])
            active_by_parent.setdefault(key,[]).append(awu_id)
    ambiguous={key:ids for key,ids in active_by_parent.items() if len(ids)>1}
    if ambiguous:
        raise AgentWorkUnitGraphError(f"multiple IN_PROGRESS AWUs for one parent task: {ambiguous}")

    return topo


def load_paths(paths:list[Path])->dict[str,dict[str,Any]]:
    nodes:dict[str,dict[str,Any]]={}
    for path in paths:
        node=_load(path)
        awu_id=node.get("id")
        if not isinstance(awu_id,str) or not awu_id:
            raise AgentWorkUnitGraphError(f"{path}: AWU id is missing")
        if awu_id in nodes:
            raise AgentWorkUnitGraphError(f"duplicate AWU id across files: {awu_id}")
        nodes[awu_id]=node
    return nodes


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Complete AWU graph paths. Defaults to engineering/fixtures/awu_graph_valid/*.json.",
    )
    args=parser.parse_args()
    paths=args.paths or sorted((ROOT/"engineering/fixtures/awu_graph_valid").glob("*.json"))
    try:
        nodes=load_paths(paths)
        topo=validate_graph(nodes)
    except AgentWorkUnitGraphError as exc:
        print(f"AGENT_WORK_UNIT_GRAPH_INVALID: {exc}",file=sys.stderr)
        return 1
    print(f"AGENT_WORK_UNIT_GRAPH_VALID count={len(nodes)} order={','.join(topo)}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
