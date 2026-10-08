#!/usr/bin/env python3
"""Validate the explicit fail-closed business-development unlock decision."""

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
DECISION_PATH = ROOT / "engineering" / "BUSINESS_DEVELOPMENT_UNLOCK_DECISION.json"
STATE_PATH = ROOT / "config" / "governance" / "project_state.json"
PROTECTION_POLICY_PATH = ROOT / "config" / "governance" / "repository_protection_policy_v1.json"
PROTECTION_STATUS_PATH = ROOT / "engineering" / "REPOSITORY_PROTECTION_STATUS.json"
SECURITY_EVIDENCE_PATH = ROOT / "engineering" / "SECURITY_ENGINE_VERIFICATION.json"
CERT_EVIDENCE_PATH = ROOT / "engineering" / "DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json"
API_VERSION = "2022-11-28"


class BusinessUnlockDecisionError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BusinessUnlockDecisionError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BusinessUnlockDecisionError(f"{path} must contain an object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BusinessUnlockDecisionError(message)


def validate(
    decision: dict[str, Any],
    state: dict[str, Any],
    protection_policy: dict[str, Any],
    protection_status: dict[str, Any],
    security_evidence: dict[str, Any],
    certification_evidence: dict[str, Any],
) -> None:
    _require(decision.get("schema_version") == 1, "unsupported unlock-decision schema version")
    _require(
        decision.get("decision_kind") == "business_development_unlock_decision_v1",
        "invalid unlock-decision kind",
    )
    _require(
        decision.get("semantics") == "EXPLICIT_FAIL_CLOSED_NO_AUTO_UNLOCK",
        "unlock decision semantics drift",
    )
    _require(decision.get("project") == "Crypto Quant Bot V3.1-Ops", "project identity drift")

    _require(
        certification_evidence.get("verdict") == "PASS_DEVELOPMENT_ENGINE_V1_EXACT_HEAD_CERTIFIED",
        "Development Engine V1 certification missing",
    )
    _require(
        security_evidence.get("verdict") == "PASS_ENGINEERING_SECURITY",
        "security engine verification missing",
    )
    _require(
        protection_policy.get("semantics") == "BUSINESS_UNLOCK_REQUIRES_VERIFIED_MAIN_PROTECTION",
        "repository protection policy drift",
    )

    finding = next(
        (item for item in state.get("findings", []) if item.get("id") == "BOOT-FINDING-001"),
        None,
    )
    _require(isinstance(finding, dict) and finding.get("observed") is True, "blocking finding is not open")
    _require(
        finding.get("must_be_resolved_before") == "BUSINESS_DEVELOPMENT_UNLOCK",
        "blocking finding target drift",
    )

    # Canonical external observations are the immutable ENG-00 baseline.
    # Fresh GitHub reality is recorded separately in decision.live_reverification.
    external = state.get("external_observations", {})
    main = external.get("main", {})
    decision_protection = decision.get("repository_protection", {})
    _require(
        decision_protection.get("observed_main_sha") == main.get("sha"),
        "decision baseline main SHA drift",
    )
    _require(
        decision_protection.get("branch_protected") == main.get("branch_protected"),
        "decision baseline branch-protection drift",
    )
    _require(
        decision_protection.get("rulesets_count") == external.get("rulesets_count"),
        "decision baseline ruleset-count drift",
    )
    _require(
        decision_protection.get("overall_status") == protection_status.get("overall_status"),
        "decision protection status drift",
    )
    _require(
        decision_protection.get("manual_admin_action_required")
        == protection_status.get("manual_admin_action_required"),
        "decision manual-remediation flag drift",
    )

    live = decision.get("live_reverification", {})
    _require(live.get("source") == "GITHUB_CONNECTOR", "live re-verification source drift")
    _require(live.get("main_sha") == main.get("sha"), "live re-verification main SHA drift")
    _require(
        live.get("baseline_rulesets_count") == external.get("rulesets_count"),
        "live re-verification baseline ruleset binding drift",
    )
    live_rulesets_count = live.get("live_rulesets_count")
    active_rulesets_count = live.get("active_rulesets_count")
    _require(
        isinstance(live_rulesets_count, int) and live_rulesets_count >= 0,
        "live ruleset count invalid",
    )
    _require(
        isinstance(active_rulesets_count, int)
        and 0 <= active_rulesets_count <= live_rulesets_count,
        "live active-ruleset count invalid",
    )
    observed_ruleset = live.get("observed_ruleset")
    if live_rulesets_count == 1:
        _require(isinstance(observed_ruleset, dict), "single live ruleset detail missing")
        enforcement = observed_ruleset.get("enforcement")
        _require(
            enforcement in {"disabled", "active", "evaluate"},
            "live ruleset enforcement invalid",
        )
        expected_active = 1 if enforcement == "active" else 0
        _require(
            active_rulesets_count == expected_active,
            "live active-ruleset count disagrees with observed enforcement",
        )
    _require(
        live.get("main_branch_protected") in {True, False},
        "live branch-protection observation invalid",
    )

    accepted_mechanism_observed = (
        live.get("main_branch_protected") is True or active_rulesets_count > 0
    )
    unprotected = (
        not accepted_mechanism_observed
        or protection_status.get("overall_status") != "PROTECTED"
        or protection_status.get("business_unlock_allowed") is not True
    )
    _require(unprotected, "blocked decision is stale because repository protection changed")
    _require(
        protection_status.get("manual_admin_action_required") is True,
        "manual repository-protection remediation must remain explicit",
    )

    _require(decision.get("verdict") == "BLOCKED_NO_UNLOCK", "unsafe unlock verdict")
    _require(decision.get("blocking_findings") == ["BOOT-FINDING-001"], "blocking finding binding drift")

    business = state.get("business_track", {})
    _require(business.get("development_status") == "PAUSED", "business development must remain PAUSED")
    candidate = business.get("candidate", {})
    _require(candidate.get("status") == "SUSPENDED_CANDIDATE", "Lot45 must remain suspended")
    _require(business.get("next_lot") == {"lot": 46, "status": "LOCKED"}, "Lot46 must remain LOCKED")

    expected_authority = {
        "business_development_unlock_allowed": False,
        "development_status": "PAUSED",
        "lot45_status": "SUSPENDED_CANDIDATE",
        "lot45_merge_allowed": False,
        "lot46_status": "LOCKED",
        "lot46_unlock_allowed": False,
    }
    _require(decision.get("business_authority") == expected_authority, "business authority must remain fail-closed")

    expected_safety = {
        "trade_allowed": False,
        "execution_allowed": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "withdrawals": "FORBIDDEN",
    }
    safety = state.get("safety", {})
    for key, expected in expected_safety.items():
        _require(safety.get(key) == expected, f"canonical safety floor weakened: {key}")
    _require(decision.get("safety_authority") == expected_safety, "decision safety authority drift")

    engineering = state.get("engineering_track", {})
    _require(engineering.get("phase") == "BUILDING", "ENG-09.6 blocked decision must remain resumable")
    _require(engineering.get("active_lot") == "ENG-09", "ENG-09 must remain active")
    _require(engineering.get("active_task") == "ENG-09.6", "ENG-09.6 must be active")
    _require(engineering.get("blockers") == ["BOOT-FINDING-001"], "unlock blocker not active")


def _request_json(url: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "crypto-quant-bot-unlock-decision",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise BusinessUnlockDecisionError(
            f"live GitHub observation failed for {url}: {exc}"
        ) from exc


def _normalize_ruleset(detail: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(detail, dict), "live ruleset detail must be an object")
    ref_name = detail.get("conditions", {}).get("ref_name", {})
    _require(isinstance(ref_name, dict), "live ruleset ref_name condition missing")
    include = ref_name.get("include", [])
    exclude = ref_name.get("exclude", [])
    _require(isinstance(include, list) and isinstance(exclude, list), "live ruleset ref conditions invalid")

    rules = detail.get("rules", [])
    _require(isinstance(rules, list), "live ruleset rules must be a list")
    normalized_rules: list[dict[str, Any]] = []
    for rule in rules:
        _require(isinstance(rule, dict) and isinstance(rule.get("type"), str), "live ruleset rule invalid")
        item: dict[str, Any] = {"type": rule["type"]}
        if "parameters" in rule:
            item["parameters"] = rule["parameters"]
        normalized_rules.append(item)

    bypass_actors = detail.get("bypass_actors", [])
    _require(isinstance(bypass_actors, list), "live ruleset bypass actors invalid")
    return {
        "id": detail.get("id"),
        "name": detail.get("name"),
        "target": detail.get("target"),
        "enforcement": detail.get("enforcement"),
        "conditions": {
            "ref_name": {
                "exclude": exclude,
                "include": include,
            }
        },
        "rules": normalized_rules,
        "bypass_actors": bypass_actors,
        "current_user_can_bypass": detail.get("current_user_can_bypass"),
    }


def collect_live_reverification(
    state: dict[str, Any],
    *,
    token: str | None,
    api_root: str = "https://api.github.com",
    request_json: Any = _request_json,
) -> dict[str, Any]:
    repository = state.get("project", {}).get("repository")
    _require(isinstance(repository, str) and "/" in repository, "project repository invalid")
    candidate = state.get("external_observations", {}).get("business_candidate", {})
    pr_number = candidate.get("pr")
    _require(isinstance(pr_number, int) and pr_number > 0, "candidate PR number invalid")

    base = f"{api_root.rstrip('/')}/repos/{repository}"
    branch = request_json(f"{base}/branches/main", token)
    pull = request_json(f"{base}/pulls/{pr_number}", token)
    rulesets = request_json(f"{base}/rulesets", token)
    _require(isinstance(branch, dict), "live main branch observation invalid")
    _require(isinstance(pull, dict), "live candidate PR observation invalid")
    _require(isinstance(rulesets, list), "live rulesets observation invalid")

    normalized_ruleset = None
    if len(rulesets) == 1:
        summary = rulesets[0]
        _require(isinstance(summary, dict) and isinstance(summary.get("id"), int), "live ruleset summary invalid")
        detail = request_json(f"{base}/rulesets/{summary['id']}", token)
        normalized_ruleset = _normalize_ruleset(detail)

    active_count = sum(
        1
        for item in rulesets
        if isinstance(item, dict) and item.get("enforcement") == "active"
    )
    try:
        return {
            "main_sha": branch["commit"]["sha"],
            "main_branch_protected": bool(branch["protected"]),
            "lot45_pr": pr_number,
            "lot45_head_sha": pull["head"]["sha"],
            "lot45_base_sha": pull["base"]["sha"],
            "lot45_state": pull["state"],
            "lot45_merged": bool(pull["merged"]),
            "live_rulesets_count": len(rulesets),
            "active_rulesets_count": active_count,
            "observed_ruleset": normalized_ruleset,
        }
    except (KeyError, TypeError) as exc:
        raise BusinessUnlockDecisionError(f"live GitHub observation incomplete: {exc}") from exc


def validate_live_reverification(
    decision: dict[str, Any],
    state: dict[str, Any],
    observed: dict[str, Any],
) -> None:
    live = decision.get("live_reverification", {})
    _require(isinstance(live, dict), "persisted live re-verification missing")
    baseline = state.get("external_observations", {})
    main = baseline.get("main", {})
    candidate = baseline.get("business_candidate", {})

    expected_candidate = {
        "lot45_pr": candidate.get("pr"),
        "lot45_head_sha": candidate.get("head"),
        "lot45_base_sha": candidate.get("base"),
        "lot45_state": candidate.get("state"),
        "lot45_merged": candidate.get("merged"),
    }
    for key, expected in expected_candidate.items():
        _require(observed.get(key) == expected, f"live candidate drift: {key}")

    _require(observed.get("main_sha") == main.get("sha"), "live main SHA changed")
    _require(
        observed.get("main_sha") == live.get("main_sha"),
        "persisted live main SHA no longer matches GitHub",
    )
    _require(
        observed.get("main_branch_protected") == live.get("main_branch_protected"),
        "live branch-protection state changed; explicit re-evaluation required",
    )
    _require(
        observed.get("live_rulesets_count") == live.get("live_rulesets_count"),
        "live ruleset count changed; explicit re-evaluation required",
    )
    _require(
        observed.get("active_rulesets_count") == live.get("active_rulesets_count"),
        "live active-ruleset count changed; explicit re-evaluation required",
    )
    _require(
        observed.get("observed_ruleset") == live.get("observed_ruleset"),
        "live ruleset details changed; explicit re-evaluation required",
    )
    _require(
        decision.get("verdict") == "BLOCKED_NO_UNLOCK",
        "live verifier only accepts the explicit blocked decision",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["snapshot", "github"],
        default="snapshot",
        help="snapshot validates persisted evidence; github also binds it to live GitHub reality.",
    )
    args = parser.parse_args()

    try:
        decision = _json(DECISION_PATH)
        state = _json(STATE_PATH)
        protection_policy = _json(PROTECTION_POLICY_PATH)
        protection_status = _json(PROTECTION_STATUS_PATH)
        security_evidence = _json(SECURITY_EVIDENCE_PATH)
        certification_evidence = _json(CERT_EVIDENCE_PATH)
        validate(
            decision,
            state,
            protection_policy,
            protection_status,
            security_evidence,
            certification_evidence,
        )
        if args.mode == "github":
            observed = collect_live_reverification(
                state,
                token=os.environ.get("GITHUB_TOKEN"),
            )
            validate_live_reverification(decision, state, observed)
    except (BusinessUnlockDecisionError, KeyError, TypeError) as exc:
        print(f"BUSINESS_UNLOCK_DECISION_INVALID: {exc}", file=sys.stderr)
        return 1

    suffix = " live=EXACT_MATCH" if args.mode == "github" else ""
    print(
        "BUSINESS_UNLOCK_DECISION_VALID "
        f"verdict=BLOCKED_NO_UNLOCK blocker=BOOT-FINDING-001{suffix}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
