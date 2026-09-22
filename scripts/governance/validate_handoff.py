#!/usr/bin/env python3
"""Validate the canonical bootstrap handoff against canonical state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class HandoffError(ValueError):
    """Raised when the handoff is malformed or stale against canonical state."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HandoffError(f"{path} must contain an object")
    return value


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise HandoffError(f"missing {where}.{key}")
    return mapping[key]


def validate_handoff(state: dict[str, Any], handoff: dict[str, Any]) -> None:
    if handoff.get("schema_version") != 1 or handoff.get("kind") != "bootstrap_handoff":
        raise HandoffError("unsupported handoff schema/kind")
    if handoff.get("workstream") != "BOOTSTRAP_ENGINE":
        raise HandoffError("unexpected handoff workstream")

    bootstrap = _require(state, "bootstrap_engine", "state")
    business = _require(state, "business_track", "state")
    snapshot = _require(handoff, "state_snapshot", "handoff")
    observed = _require(handoff, "external_git_observation", "handoff")

    expected = {
        "phase": bootstrap.get("phase"),
        "active_lot": bootstrap.get("active_lot"),
        "active_task": bootstrap.get("active_task"),
        "active_manifest": bootstrap.get("active_manifest"),
        "business_development": business.get("business_development"),
        "lot46_status": business.get("next_lot", {}).get("status"),
    }
    if snapshot != expected:
        raise HandoffError("handoff state snapshot is stale")

    baseline = _require(state, "observed_git_baseline", "state")
    if observed.get("default_branch") != baseline.get("default_branch"):
        raise HandoffError("handoff default branch disagrees with canonical state")
    if observed.get("main_sha") != baseline.get("main_sha"):
        raise HandoffError("handoff main SHA disagrees with canonical state")
    if SHA40_RE.fullmatch(str(observed.get("main_sha", ""))) is None:
        raise HandoffError("handoff main SHA is malformed")

    candidate = business.get("active_candidate", {})
    if observed.get("lot45_pr") != candidate.get("pull_request"):
        raise HandoffError("handoff Lot45 PR disagrees with canonical state")
    if observed.get("lot45_head_sha") != candidate.get("observed_head_sha"):
        raise HandoffError("handoff Lot45 head disagrees with canonical state")

    if handoff.get("engineering_branch") != bootstrap.get("branch"):
        raise HandoffError("handoff engineering branch disagrees with canonical state")

    if handoff.get("status") == "COMPLETE":
        engineering = _require(state, "engineering_engine", "state")
        expected_next = {
            "active_lot": engineering.get("active_lot"),
            "active_task": engineering.get("active_task"),
            "active_manifest": engineering.get("active_manifest"),
        }
        if handoff.get("next_engineering") != expected_next:
            raise HandoffError("completed bootstrap handoff disagrees with engineering entry state")

    if not isinstance(handoff.get("next_action"), str) or not handoff["next_action"].strip():
        raise HandoffError("handoff next_action must be non-empty")
    if not isinstance(handoff.get("stale_when"), list) or not handoff["stale_when"]:
        raise HandoffError("handoff must declare stale_when conditions")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--state", type=Path, default=root / "engineering" / "STATE.json")
    parser.add_argument("--handoff", type=Path, default=root / "engineering" / "handoff" / "CURRENT.json")
    args = parser.parse_args()

    try:
        validate_handoff(_load(args.state), _load(args.handoff))
    except HandoffError as exc:
        print(f"HANDOFF_INVALID: {exc}", file=sys.stderr)
        return 1
    print("HANDOFF_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
