#!/usr/bin/env python3
"""Render deterministic current-status documentation from canonical project state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "generated_status_policy_v1.json"


class CurrentStatusError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CurrentStatusError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CurrentStatusError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise CurrentStatusError("unsupported generated-status policy version")
    if policy.get("policy_kind") != "generated_status_policy_v1":
        raise CurrentStatusError("invalid generated-status policy kind")
    if policy.get("semantics") != "CANONICAL_STATE_TO_BOUNDED_DOC_BLOCKS":
        raise CurrentStatusError("generated-status semantics drift")
    if policy.get("source") != "config/governance/project_state.json":
        raise CurrentStatusError("canonical status source drift")
    docs = policy.get("managed_documents")
    if not isinstance(docs, list) or [x.get("path") for x in docs] != ["README.md", "AGENTS.md"]:
        raise CurrentStatusError("managed document set/order drift")
    for item in docs:
        if set(item) != {"path", "start_marker", "end_marker"}:
            raise CurrentStatusError("invalid managed-document policy shape")
        if item["start_marker"] == item["end_marker"]:
            raise CurrentStatusError("generated block markers must differ")
    if policy.get("generated_page") != "engineering/CURRENT_STATUS.md":
        raise CurrentStatusError("generated status page path drift")


def validate_state(state: dict[str, Any]) -> None:
    try:
        project = state["project"]
        business = state["business_track"]
        engineering = state["engineering_track"]
        safety = state["safety"]
        baseline = business["merged_certified_baseline"]
        candidate = business["candidate"]
        next_lot = business["next_lot"]
    except KeyError as exc:
        raise CurrentStatusError(f"canonical state missing required field: {exc}") from exc
    if project.get("canonical_name") != "Crypto Quant Bot V3.1-Ops":
        raise CurrentStatusError("canonical project identity drift")
    if business.get("development_status") != "PAUSED":
        raise CurrentStatusError("ENG-05.1 expects business development to remain PAUSED")
    if candidate.get("status") != "SUSPENDED_CANDIDATE":
        raise CurrentStatusError("Lot45 candidate must remain suspended")
    if next_lot.get("status") != "LOCKED":
        raise CurrentStatusError("next business lot must remain locked")
    if safety.get("trade_allowed") is not False or safety.get("execution_allowed") is not False:
        raise CurrentStatusError("trading/execution safety must remain disabled")
    if not isinstance(baseline.get("lot"), int) or not isinstance(engineering.get("active_lot"), str):
        raise CurrentStatusError("canonical status state shape invalid")


def render_block(state: dict[str, Any]) -> str:
    validate_state(state)
    business = state["business_track"]
    engineering = state["engineering_track"]
    safety = state["safety"]
    baseline = business["merged_certified_baseline"]
    candidate = business["candidate"]
    findings = [x for x in state.get("findings", []) if isinstance(x, dict) and x.get("observed")]
    finding_text = (
        ", ".join(
            f"`{x['id']}` ({x['code']}; before {x['must_be_resolved_before']})"
            for x in findings
        )
        if findings else "**none**"
    )
    rows = [
        "<!-- BEGIN GENERATED CURRENT STATUS -->",
        "## Current project status (generated)",
        "",
        "> Generated from `config/governance/project_state.json`. Do not edit this block manually.",
        "",
        f"- Project: **{state['project']['canonical_name']}**",
        f"- Business development: **{business['development_status']}**",
        f"- Certified business baseline: **Lot {baseline['lot']} / {baseline['version']} / {baseline['verdict']}**",
        f"- Suspended business candidate: **Lot {candidate['lot']} / PR #{candidate['pr']} / {candidate['status']}**",
        f"- Next business lot: **Lot {business['next_lot']['lot']} / {business['next_lot']['status']}**",
        f"- Engineering: **{engineering['active_lot']} / {engineering['active_task']} / {engineering['phase']}**",
        f"- Next engineering lot: **{engineering['next_lot']}**",
        f"- Runtime maximum: `{safety['runtime_max']}`",
        f"- Trading allowed: `{str(safety['trade_allowed']).lower()}`",
        f"- Execution allowed: `{str(safety['execution_allowed']).lower()}`",
        f"- Live execution: `{safety['live_execution']}`",
        f"- Leverage: `{safety['leverage']}`",
        f"- Withdrawals: `{safety['withdrawals']}`",
        f"- Open blocking findings: {finding_text}",
        "<!-- END GENERATED CURRENT STATUS -->",
    ]
    return "\n".join(rows)


def render_page(block: str) -> str:
    return (
        "# Current Project Status\n\n"
        "> Fully generated from `config/governance/project_state.json`. "
        "Do not edit this file manually.\n\n"
        + block + "\n"
    )


def replace_block(text: str, start: str, end: str, expected: str) -> str:
    starts = text.count(start)
    ends = text.count(end)
    if starts != 1 or ends != 1:
        raise CurrentStatusError(
            f"managed document requires exactly one generated block; starts={starts} ends={ends}"
        )
    begin = text.index(start)
    finish = text.index(end, begin) + len(end)
    if finish <= begin:
        raise CurrentStatusError("generated block marker ordering invalid")
    return text[:begin] + expected + text[finish:]


def desired_files(root: Path = ROOT) -> dict[Path, str]:
    policy = _json(root / "config/governance/generated_status_policy_v1.json")
    validate_policy(policy)
    state = _json(root / policy["source"])
    block = render_block(state)
    desired: dict[Path, str] = {}
    for item in policy["managed_documents"]:
        path = root / item["path"]
        try:
            current = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CurrentStatusError(f"cannot read managed document {path}: {exc}") from exc
        desired[path] = replace_block(
            current, item["start_marker"], item["end_marker"], block
        )
    desired[root / policy["generated_page"]] = render_page(block)
    return desired


def run(mode: str, root: Path = ROOT) -> None:
    desired = desired_files(root)
    stale: list[str] = []
    for path, expected in desired.items():
        try:
            current = path.read_text(encoding="utf-8")
        except OSError:
            current = ""
        if current != expected:
            if mode == "check":
                stale.append(path.relative_to(root).as_posix())
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8")
    if stale:
        raise CurrentStatusError(f"generated current status is stale: {sorted(stale)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--update", action="store_true")
    args = parser.parse_args()
    try:
        run("check" if args.check else "update")
    except CurrentStatusError as exc:
        print(f"CURRENT_STATUS_INVALID: {exc}", file=sys.stderr)
        return 1
    print("CURRENT_STATUS_VALID" if args.check else "CURRENT_STATUS_UPDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
