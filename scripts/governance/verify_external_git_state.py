#!/usr/bin/env python3
"""Verify permanent external Git observations against live GitHub state."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "config" / "governance" / "project_state.json"
API_VERSION = "2022-11-28"


class StateDriftError(ValueError):
    """Raised when live GitHub reality differs from canonical project state."""


def _load_state(path: Path = STATE) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateDriftError(f"cannot load project state: {exc}") from exc
    if not isinstance(value, dict):
        raise StateDriftError("project state must be an object")
    return value


def _request_json(url: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "crypto-quant-bot-governance",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise StateDriftError(f"GitHub observation failed for {url}: {exc}") from exc


def collect_live_observations(
    state: dict[str, Any],
    *,
    token: str | None,
    api_root: str = "https://api.github.com",
) -> dict[str, Any]:
    project = state.get("project", {})
    repository = project.get("repository")
    if not isinstance(repository, str) or "/" not in repository:
        raise StateDriftError("project.repository is invalid")

    expected = state.get("external_observations")
    if not isinstance(expected, dict):
        raise StateDriftError("external_observations are missing")
    candidate = expected.get("business_candidate")
    if not isinstance(candidate, dict):
        raise StateDriftError("business candidate observation is required during ENG-01")
    pr_number = candidate.get("pr")
    if not isinstance(pr_number, int) or pr_number <= 0:
        raise StateDriftError("business candidate PR number is invalid")

    base = f"{api_root.rstrip('/')}/repos/{repository}"
    branch = _request_json(f"{base}/branches/main", token)
    pull = _request_json(f"{base}/pulls/{pr_number}", token)
    rulesets = _request_json(f"{base}/rulesets", token)

    if not isinstance(branch, dict) or not isinstance(pull, dict) or not isinstance(rulesets, list):
        raise StateDriftError("GitHub returned an unexpected observation shape")

    try:
        main_sha = branch["commit"]["sha"]
        protected = bool(branch["protected"])
        pr_head = pull["head"]["sha"]
        pr_base = pull["base"]["sha"]
        pr_state = pull["state"]
        pr_merged = bool(pull["merged"])
    except (KeyError, TypeError) as exc:
        raise StateDriftError(f"GitHub observation is incomplete: {exc}") from exc

    return {
        "main": {
            "sha": main_sha,
            "branch_protected": protected,
        },
        "rulesets_count": len(rulesets),
        "business_candidate": {
            "pr": pr_number,
            "state": pr_state,
            "merged": pr_merged,
            "head": pr_head,
            "base": pr_base,
        },
    }


def compare_observations(state: dict[str, Any], observed: dict[str, Any]) -> None:
    expected = state.get("external_observations")
    if not isinstance(expected, dict):
        raise StateDriftError("canonical external_observations are missing")

    if observed != expected:
        keys = ("main", "rulesets_count", "business_candidate")
        differences = [
            key
            for key in keys
            if observed.get(key) != expected.get(key)
        ]
        raise StateDriftError(f"STATE_DRIFT external observations changed: {differences}")

    business = state.get("business_track", {})
    candidate = business.get("candidate")
    observed_candidate = observed.get("business_candidate")
    if not isinstance(candidate, dict) or not isinstance(observed_candidate, dict):
        raise StateDriftError("business candidate state is missing")

    bindings = {
        "pr": (candidate.get("pr"), observed_candidate.get("pr")),
        "head": (candidate.get("observed_head"), observed_candidate.get("head")),
        "merged": (candidate.get("merged"), observed_candidate.get("merged")),
        "state": (str(candidate.get("state", "")).lower(), observed_candidate.get("state")),
    }
    drifted = [name for name, values in bindings.items() if values[0] != values[1]]
    if drifted:
        raise StateDriftError(f"STATE_DRIFT business candidate binding changed: {drifted}")

    next_lot = business.get("next_lot")
    if next_lot != {"lot": 46, "status": "LOCKED"}:
        raise StateDriftError("STATE_DRIFT Lot46 is no longer locked")

    freshness = state.get("freshness_policy", {})
    if freshness.get("verify_external_git_on_every_agent_resume") is not True:
        raise StateDriftError("fresh external Git verification is not mandatory")
    if freshness.get("auto_heal_state_from_external_git") is not False:
        raise StateDriftError("external Git drift must not auto-heal")
    if freshness.get("mismatch_consequence") != "STATE_DRIFT":
        raise StateDriftError("external mismatch consequence must be STATE_DRIFT")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["snapshot", "github"],
        default="snapshot",
        help="snapshot validates recorded bindings; github also queries live GitHub.",
    )
    args = parser.parse_args()

    try:
        state = _load_state()
        expected = state.get("external_observations")
        if not isinstance(expected, dict):
            raise StateDriftError("external_observations are missing")
        if args.mode == "github":
            observed = collect_live_observations(
                state,
                token=os.environ.get("GITHUB_TOKEN"),
            )
        else:
            observed = expected
        compare_observations(state, observed)
    except StateDriftError as exc:
        print(f"STATE_DRIFT_DETECTED: {exc}", file=sys.stderr)
        return 1

    main_sha = observed["main"]["sha"]
    candidate = observed["business_candidate"]
    print(
        "EXTERNAL_GIT_STATE_VALID "
        f"main={main_sha} pr={candidate['pr']} head={candidate['head']} "
        f"rulesets={observed['rulesets_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
