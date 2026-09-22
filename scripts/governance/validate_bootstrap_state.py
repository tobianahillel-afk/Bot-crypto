#!/usr/bin/env python3
"""Cheap fail-closed validator for the Bootstrap Engineering Engine state.

This script intentionally uses only the Python 3.11 standard library.
It validates bootstrap-level invariants only; work-item manifest validation
is completed by the BOOT-03/BOOT-06 layers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class BootstrapStateError(ValueError):
    """Raised when bootstrap state violates a mandatory invariant."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapStateError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BootstrapStateError(f"{path} must contain a JSON object")
    return data


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise BootstrapStateError(f"missing {where}.{key}")
    return mapping[key]


def _require_false(mapping: dict[str, Any], key: str, where: str) -> None:
    if _require(mapping, key, where) is not False:
        raise BootstrapStateError(f"{where}.{key} must be false")


def validate_state(state: dict[str, Any], policy: dict[str, Any]) -> None:
    if state.get("schema_version") != 1:
        raise BootstrapStateError("unsupported state schema_version")
    if state.get("state_kind") != "bootstrap_engine_state":
        raise BootstrapStateError("invalid state_kind")

    project = _require(state, "project", "state")
    if project.get("canonical_name") != "Crypto Quant Bot V3.1-Ops":
        raise BootstrapStateError("canonical project identity drift")
    if project.get("repository") != "tobianahillel-afk/Bot-crypto":
        raise BootstrapStateError("repository identity drift")

    baseline = _require(state, "observed_git_baseline", "state")
    if baseline.get("default_branch") != "main":
        raise BootstrapStateError("default branch must remain main during bootstrap")
    if not SHA40_RE.fullmatch(str(baseline.get("main_sha", ""))):
        raise BootstrapStateError("observed main_sha must be a 40-character lowercase SHA")

    engine = _require(state, "bootstrap_engine", "state")
    phase = engine.get("phase")
    phase_transitions = policy.get("phase_transitions", {})
    if phase not in phase_transitions:
        raise BootstrapStateError(f"unknown bootstrap phase: {phase!r}")

    order = policy.get("bootstrap_order")
    if not isinstance(order, list) or not order:
        raise BootstrapStateError("transition policy bootstrap_order is invalid")

    completed = engine.get("completed")
    if not isinstance(completed, list) or len(completed) != len(set(completed)):
        raise BootstrapStateError("completed must be a unique list")

    active = engine.get("active_lot")
    if phase == "BUILDING":
        if active not in order:
            raise BootstrapStateError("BUILDING requires one valid active_lot")
        active_index = order.index(active)
        expected_completed = order[:active_index]
        if completed != expected_completed:
            raise BootstrapStateError(
                f"completed lots must be the strict prefix before {active}: "
                f"expected {expected_completed}, got {completed}"
            )
        expected_next = order[active_index + 1] if active_index + 1 < len(order) else None
        if engine.get("next_lot") != expected_next:
            raise BootstrapStateError(
                f"next_lot mismatch: expected {expected_next!r}, got {engine.get('next_lot')!r}"
            )
        active_task = engine.get("active_task")
        if not isinstance(active_task, str) or not active_task.startswith(f"{active}."):
            raise BootstrapStateError("active_task must belong to active_lot")

    business = _require(state, "business_track", "state")
    if phase == "BUILDING":
        if business.get("business_development") != "PAUSED":
            raise BootstrapStateError("business development must remain PAUSED while BUILDING")
        next_lot = business.get("next_lot")
        if not isinstance(next_lot, dict) or next_lot.get("lot") != 46:
            raise BootstrapStateError("business next_lot must remain Lot46 during bootstrap")
        if next_lot.get("status") != "LOCKED":
            raise BootstrapStateError("Lot46 must remain LOCKED while BUILDING")

    safety = _require(state, "safety", "state")
    _require_false(safety, "trade_allowed", "safety")
    _require_false(safety, "execution_allowed", "safety")
    if safety.get("live_execution") != "DISABLED":
        raise BootstrapStateError("live_execution must remain DISABLED")
    if safety.get("leverage") != "FORBIDDEN":
        raise BootstrapStateError("leverage must remain FORBIDDEN")
    if safety.get("withdrawals") != "FORBIDDEN":
        raise BootstrapStateError("withdrawals must remain FORBIDDEN")

    cost = _require(state, "mandatory_cost_policy", "state")
    for key in (
        "paid_external_api_required",
        "paid_llm_required",
        "paid_saas_required",
        "paid_runner_required",
    ):
        _require_false(cost, key, "mandatory_cost_policy")

    required_stops = {
        "STATE_DRIFT",
        "BUSINESS_SCOPE_TOUCHED_WITHOUT_UNLOCK",
        "FROZEN_EVIDENCE_MUTATION",
        "LOT46_UNLOCK_ATTEMPT",
        "MANDATORY_PAID_DEPENDENCY_INTRODUCED",
    }
    stops = set(state.get("stop_conditions", []))
    missing = sorted(required_stops - stops)
    if missing:
        raise BootstrapStateError(f"missing mandatory stop conditions: {missing}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--state",
        type=Path,
        default=root / "engineering" / "STATE.json",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=root / "engineering" / "STATE_TRANSITIONS.json",
    )
    args = parser.parse_args()

    try:
        state = _load_json(args.state)
        policy = _load_json(args.policy)
        validate_state(state, policy)
    except BootstrapStateError as exc:
        print(f"BOOTSTRAP_STATE_INVALID: {exc}", file=sys.stderr)
        return 1

    print("BOOTSTRAP_STATE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
