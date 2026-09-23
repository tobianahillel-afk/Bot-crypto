#!/usr/bin/env python3
"""Render and validate the bounded active-agent context map."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "context_map_policy_v1.json"


class ContextMapError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextMapError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContextMapError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ContextMapError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _safe_existing(path: str, root: Path = ROOT) -> None:
    if not isinstance(path, str) or not path:
        raise ContextMapError("context path must be a non-empty string")
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ContextMapError(f"context path escapes repository: {path}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ContextMapError(f"context path escapes repository: {path}") from exc
    if not resolved.is_file():
        raise ContextMapError(f"context path does not exist: {path}")


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ContextMapError(f"{label} contains duplicate paths")


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise ContextMapError("unsupported context-map policy version")
    if policy.get("policy_kind") != "context_map_policy_v1":
        raise ContextMapError("invalid context-map policy kind")
    if policy.get("semantics") != "GENERATED_PROGRESSIVE_DISCLOSURE_FROM_ACTIVE_AWU":
        raise ContextMapError("context-map semantics drift")
    if policy.get("state_source") != "config/governance/project_state.json":
        raise ContextMapError("canonical state source drift")
    if policy.get("active_awu_resolver") != "scripts/governance/resolve_active_awu.py":
        raise ContextMapError("active AWU resolver drift")
    if policy.get("handoff_source") != "engineering/handoff/CURRENT.json":
        raise ContextMapError("handoff source drift")
    if policy.get("machine_output") != "engineering/CONTEXT_MAP.json":
        raise ContextMapError("machine output drift")
    if policy.get("human_output") != "engineering/CONTEXT_MAP.md":
        raise ContextMapError("human output drift")
    expected = [
        "AGENTS.md",
        "config/governance/project_state.json",
        "engineering/CONTEXT_MAP.json",
    ]
    if policy.get("bootstrap_read_order") != expected:
        raise ContextMapError("bootstrap read order drift")
    if policy.get("non_authoritative_sources") != [
        "engineering/STATE.json", "chat_history", "model_memory"
    ]:
        raise ContextMapError("non-authoritative source declaration drift")
    if policy.get("implicit_expansion") != "FORBIDDEN":
        raise ContextMapError("implicit context expansion must remain forbidden")
    if policy.get("max_bootstrap_files") != 3:
        raise ContextMapError("bootstrap file budget drift")


def _validate_handoff(handoff: dict[str, Any], engineering: dict[str, Any]) -> None:
    expected = {
        "active_lot": engineering.get("active_lot"),
        "active_task": engineering.get("active_task"),
        "active_manifest": engineering.get("active_manifest"),
    }
    if handoff.get("next_engineering") != expected:
        raise ContextMapError("handoff next_engineering disagrees with canonical state")
    for field in ("current_objective", "next_action"):
        if not isinstance(handoff.get(field), str) or not handoff[field]:
            raise ContextMapError(f"handoff {field} missing")


def build_map(
    state: dict[str, Any],
    handoff: dict[str, Any],
    awu_path: str,
    awu: dict[str, Any],
    route: dict[str, Any],
    policy: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any]:
    validate_policy(policy)
    if state.get("project", {}).get("canonical_name") != "Crypto Quant Bot V3.1-Ops":
        raise ContextMapError("canonical identity drift")
    engineering = state.get("engineering_track")
    if not isinstance(engineering, dict) or engineering.get("phase") != "BUILDING":
        raise ContextMapError("ENGINEERING track must be BUILDING")
    _validate_handoff(handoff, engineering)

    expected_parent = {
        "work_item_id": engineering.get("active_lot"),
        "task_id": engineering.get("active_task"),
        "manifest": engineering.get("active_manifest"),
    }
    if awu.get("parent") != expected_parent:
        raise ContextMapError("active AWU parent disagrees with canonical state")
    if awu.get("status") != "IN_PROGRESS":
        raise ContextMapError("context map requires one IN_PROGRESS AWU")

    primary = route.get("primary_files")
    reference = route.get("reference_files")
    if not isinstance(primary, list) or not isinstance(reference, list):
        raise ContextMapError("active context route missing")
    _unique(primary, "primary route")
    _unique(reference, "reference route")
    if set(primary) & set(reference):
        raise ContextMapError("primary/reference route overlap")
    if primary[:2] != ["AGENTS.md", "config/governance/project_state.json"]:
        raise ContextMapError("primary route authority prefix drift")
    if engineering["active_manifest"] not in primary or awu_path not in primary:
        raise ContextMapError("active manifest/AWU missing from primary route")
    if "engineering/STATE.json" in primary + reference:
        raise ContextMapError("migration bridge entered executable context")
    for path in primary + reference:
        _safe_existing(path, root)

    budget = awu.get("planning", {}).get("context_budget")
    if not isinstance(budget, dict):
        raise ContextMapError("active context budget missing")
    if route.get("primary_count") != len(primary):
        raise ContextMapError("primary route count drift")
    if route.get("reference_count") != len(reference):
        raise ContextMapError("reference route count drift")
    if len(primary) > budget["max_primary_files"]:
        raise ContextMapError("primary context budget exceeded")
    if len(reference) > budget["max_reference_files"]:
        raise ContextMapError("reference context budget exceeded")
    if route.get("total_kib_ceil", 0) > budget["max_total_kib"]:
        raise ContextMapError("context byte budget exceeded")

    business = state["business_track"]
    safety = state["safety"]
    return {
        "schema_version": 1,
        "map_kind": "active_agent_context_map_v1",
        "project": state["project"]["canonical_name"],
        "authority": {
            "current_state": policy["state_source"],
            "resume_hint": policy["handoff_source"],
            "resume_hint_is_authoritative": False,
        },
        "bootstrap_read_order": list(policy["bootstrap_read_order"]),
        "active_work": {
            "track": "ENGINEERING",
            "lot": engineering["active_lot"],
            "task": engineering["active_task"],
            "manifest": engineering["active_manifest"],
            "awu_id": awu["id"],
            "awu_path": awu_path,
            "risk_class": awu["planning"]["risk_class"],
            "complexity_score": awu["planning"]["complexity_score"],
        },
        "execution_context": {
            "primary_files": primary,
            "reference_files": reference,
            "primary_count": route["primary_count"],
            "reference_count": route["reference_count"],
            "total_kib_ceil": route["total_kib_ceil"],
            "budget": budget,
            "implicit_expansion": "FORBIDDEN",
        },
        "resume": {
            "handoff": policy["handoff_source"],
            "current_objective": handoff["current_objective"],
            "next_action": handoff["next_action"],
        },
        "business_hold": {
            "development_status": business["development_status"],
            "candidate_lot": business["candidate"]["lot"],
            "candidate_status": business["candidate"]["status"],
            "next_lot": business["next_lot"],
        },
        "safety": {
            "runtime_max": safety["runtime_max"],
            "trade_allowed": safety["trade_allowed"],
            "execution_allowed": safety["execution_allowed"],
            "live_execution": safety["live_execution"],
        },
        "stop_conditions": state.get("stop_conditions", []),
        "non_authoritative_sources": list(policy["non_authoritative_sources"]),
        "instructions": [
            "verify external Git reality before writing",
            "continue only the active AWU",
            "do not recursively load the repository at startup",
            "load additional files only when the active AWU or validated dependency requires them",
        ],
    }


def validate_map(value: dict[str, Any], root: Path = ROOT) -> None:
    if value.get("schema_version") != 1 or value.get("map_kind") != "active_agent_context_map_v1":
        raise ContextMapError("invalid generated context-map identity")
    if value.get("bootstrap_read_order") != [
        "AGENTS.md", "config/governance/project_state.json", "engineering/CONTEXT_MAP.json"
    ]:
        raise ContextMapError("generated bootstrap order drift")
    active = value.get("active_work")
    if not isinstance(active, dict) or active.get("track") != "ENGINEERING":
        raise ContextMapError("generated active work invalid")
    execution = value.get("execution_context")
    if not isinstance(execution, dict):
        raise ContextMapError("generated execution context missing")
    primary = execution.get("primary_files")
    reference = execution.get("reference_files")
    if not isinstance(primary, list) or not isinstance(reference, list):
        raise ContextMapError("generated route invalid")
    _unique(primary, "generated primary route")
    _unique(reference, "generated reference route")
    if set(primary) & set(reference):
        raise ContextMapError("generated primary/reference overlap")
    if "engineering/STATE.json" in primary + reference:
        raise ContextMapError("migration bridge entered generated route")
    for path in primary + reference:
        _safe_existing(path, root)
    if value.get("non_authoritative_sources") != [
        "engineering/STATE.json", "chat_history", "model_memory"
    ]:
        raise ContextMapError("generated authority declarations drift")
    resume = value.get("resume")
    if not isinstance(resume, dict) or resume.get("handoff") != "engineering/handoff/CURRENT.json":
        raise ContextMapError("generated resume context drift")


def render_markdown(value: dict[str, Any]) -> str:
    active = value["active_work"]
    execution = value["execution_context"]
    lines = [
        "# Active Agent Context Map",
        "",
        "> Generated from canonical project state and the validated active AWU route. Do not edit manually.",
        "",
        "## Bootstrap read order",
        "",
    ]
    lines.extend(
        f"{index}. {path}" for index, path in enumerate(value["bootstrap_read_order"], 1)
    )
    lines += [
        "",
        "## Active work",
        "",
        f"- Track: {active['track']}",
        f"- Work item: {active['lot']}",
        f"- Task: {active['task']}",
        f"- AWU: {active['awu_id']}",
        f"- Risk: {active['risk_class']}",
        f"- Manifest: {active['manifest']}",
        f"- AWU file: {active['awu_path']}",
        "",
        "## Execution context — primary",
        "",
    ]
    lines.extend(f"- {path}" for path in execution["primary_files"])
    lines += ["", "## Execution context — reference", ""]
    lines.extend(f"- {path}" for path in execution["reference_files"])
    lines += [
        "",
        "## Budget",
        "",
        f"- Primary: {execution['primary_count']} / {execution['budget']['max_primary_files']} files",
        f"- Reference: {execution['reference_count']} / {execution['budget']['max_reference_files']} files",
        f"- Routed size: {execution['total_kib_ceil']} / {execution['budget']['max_total_kib']} KiB",
        "- Implicit repository expansion: FORBIDDEN",
        "",
        "## Resume hint",
        "",
        f"- Handoff: {value['resume']['handoff']}",
        f"- Objective: {value['resume']['current_objective']}",
        f"- Next action: {value['resume']['next_action']}",
        "",
        "## Non-authoritative sources",
        "",
    ]
    lines.extend(f"- {item}" for item in value["non_authoritative_sources"])
    lines += [
        "",
        "Chat history and model memory may explain prior work but never authorize it.",
        "",
        "## Stop conditions",
        "",
    ]
    lines.extend(f"- {item}" for item in value["stop_conditions"])
    return "\n".join(lines) + "\n"


def desired(root: Path = ROOT) -> tuple[dict[str, Any], str]:
    policy = _json(root / "config/governance/context_map_policy_v1.json")
    validate_policy(policy)
    state = _json(root / policy["state_source"])
    handoff = _json(root / policy["handoff_source"])
    resolver = _module("context_map_active_awu", root / policy["active_awu_resolver"])
    try:
        path, awu, evidence = resolver.resolve_active_awu()
    except resolver.ActiveAwuError as exc:
        raise ContextMapError(str(exc)) from exc
    value = build_map(
        state,
        handoff,
        path.relative_to(root).as_posix(),
        awu,
        evidence["context_route"],
        policy,
        root,
    )
    validate_map(value, root)
    return value, render_markdown(value)


def run(mode: str, root: Path = ROOT) -> None:
    policy = _json(root / "config/governance/context_map_policy_v1.json")
    validate_policy(policy)
    value, markdown = desired(root)
    expected = {
        root / policy["machine_output"]: json.dumps(value, indent=2, sort_keys=True) + "\n",
        root / policy["human_output"]: markdown,
    }
    stale = []
    for path, content in expected.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != content:
            if mode == "check":
                stale.append(path.relative_to(root).as_posix())
            else:
                path.write_text(content, encoding="utf-8")
    if stale:
        raise ContextMapError(f"generated context map is stale: {sorted(stale)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--update", action="store_true")
    args = parser.parse_args()
    try:
        run("check" if args.check else "update")
    except (ContextMapError, OSError, KeyError) as exc:
        print(f"CONTEXT_MAP_INVALID: {exc}", file=sys.stderr)
        return 1
    print("CONTEXT_MAP_VALID" if args.check else "CONTEXT_MAP_UPDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
