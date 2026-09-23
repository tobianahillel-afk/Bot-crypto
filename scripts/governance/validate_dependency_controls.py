#!/usr/bin/env python3
"""Validate ENG-04.2 dependency-security controls without network access."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "dependency_control_policy_v1.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "security-dependencies.yml"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PIN_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;@]+)$")


class DependencyControlError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DependencyControlError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DependencyControlError(f"{path} must contain an object")
    return value


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_pin(line: str, source: str) -> tuple[str, str]:
    match = PIN_RE.fullmatch(line.strip())
    if match is None:
        raise DependencyControlError(f"{source} contains non-exact requirement: {line!r}")
    name, version = match.groups()
    if NAME_RE.fullmatch(name) is None or not version:
        raise DependencyControlError(f"{source} contains invalid package pin: {line!r}")
    return _normalize(name), version


def _non_comment_lines(path: Path) -> list[str]:
    try:
        raw = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DependencyControlError(f"cannot read {path}: {exc}") from exc
    return [line.strip() for line in raw if line.strip() and not line.lstrip().startswith("#")]


def _parse_pin_list(lines: list[str], source: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines:
        name, version = _parse_pin(line, source)
        if name in result:
            raise DependencyControlError(f"{source} contains duplicate package: {name}")
        result[name] = version
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise DependencyControlError("unsupported dependency policy schema_version")
    if policy.get("policy_kind") != "dependency_control_policy_v1":
        raise DependencyControlError("invalid dependency policy kind")
    if policy.get("semantics") != "PINNED_LOCK_PLUS_PR_DIFF_FAIL_CLOSED":
        raise DependencyControlError("dependency policy semantics drift")
    audit = policy.get("pip_audit")
    if not isinstance(audit, dict) or audit.get("version") != "2.9.0":
        raise DependencyControlError("pip-audit pin drift")
    if audit.get("direct_requirement") != "pip-audit==2.9.0":
        raise DependencyControlError("pip-audit direct requirement drift")
    if audit.get("arguments") != [
        "-r","requirements-dev.lock","--no-deps","--disable-pip","--strict","--progress-spinner","off"
    ]:
        raise DependencyControlError("pip-audit arguments drift")
    review = policy.get("dependency_review")
    if not isinstance(review, dict):
        raise DependencyControlError("dependency review policy missing")
    if review.get("version") != "v5.0.0":
        raise DependencyControlError("Dependency Review version drift")
    if review.get("commit") != "a1d282b36b6f3519aa1f3fc636f609c47dddb294":
        raise DependencyControlError("Dependency Review SHA drift")
    expected = {
        "fail_on_severity":"low",
        "fail_on_scopes":"runtime,development,unknown",
        "vulnerability_check":True,
        "license_check":False,
        "comment_summary_in_pr":"never",
        "warn_only":False,
        "show_openssf_scorecard":False,
    }
    for key, value in expected.items():
        if review.get(key) != value:
            raise DependencyControlError(f"Dependency Review policy drift: {key}")
    toolchain = policy.get("toolchain")
    if not isinstance(toolchain, dict):
        raise DependencyControlError("dependency toolchain policy missing")
    for key in ("checkout_action_sha","setup_python_action_sha"):
        if re.fullmatch(r"[0-9a-f]{40}", str(toolchain.get(key,""))) is None:
            raise DependencyControlError(f"{key} must be exact SHA")
    if toolchain.get("python_version") != "3.11.9":
        raise DependencyControlError("dependency audit Python drift")
    if policy.get("schedule") != {"cadence":"WEEKLY","cron":"23 4 * * 1"}:
        raise DependencyControlError("dependency audit schedule drift")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise DependencyControlError("dependency controls must remain zero-cost")


def validate_manifests(policy: dict[str, Any]) -> None:
    try:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise DependencyControlError(f"cannot parse pyproject.toml: {exc}") from exc

    project = pyproject.get("project")
    if not isinstance(project, dict):
        raise DependencyControlError("pyproject project table missing")
    runtime = project.get("dependencies")
    if policy.get("runtime_dependencies_expected_empty") is True and runtime != []:
        raise DependencyControlError("runtime dependencies changed without dependency-policy update")

    optional = project.get("optional-dependencies")
    if not isinstance(optional, dict) or not isinstance(optional.get("dev"), list):
        raise DependencyControlError("pyproject dev dependencies missing")
    py_dev = _parse_pin_list(list(optional["dev"]), "pyproject dev")
    in_dev = _parse_pin_list(_non_comment_lines(ROOT / "requirements-dev.in"), "requirements-dev.in")
    if py_dev != in_dev:
        raise DependencyControlError("pyproject dev dependencies and requirements-dev.in drift")

    dev_txt = _non_comment_lines(ROOT / "requirements-dev.txt")
    if dev_txt != ["-r requirements-dev.lock"]:
        raise DependencyControlError("requirements-dev.txt must only reference requirements-dev.lock")

    lock = _parse_pin_list(_non_comment_lines(ROOT / "requirements-dev.lock"), "requirements-dev.lock")
    missing = {
        name:version for name,version in py_dev.items()
        if lock.get(name) != version
    }
    if missing:
        raise DependencyControlError(f"direct dev pins missing or changed in lock: {sorted(missing)}")
    if lock.get("pip-audit") != "2.9.0":
        raise DependencyControlError("locked pip-audit must remain 2.9.0 in ENG-04.2")

    runtime_txt = _non_comment_lines(ROOT / "requirements.txt")
    if runtime_txt:
        raise DependencyControlError("requirements.txt acquired runtime dependencies without policy update")


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise DependencyControlError(f"dependency workflow missing {label}: {needle}")


def validate_workflow(policy: dict[str, Any], text: str) -> None:
    if "permissions:\n  contents: read\n" not in text:
        raise DependencyControlError("dependency workflow permissions must be contents: read only")
    for forbidden in (
        "contents: write","pull-requests: write","security-events: write","permissions: write-all"
    ):
        if forbidden in text:
            raise DependencyControlError(f"forbidden dependency workflow permission: {forbidden}")

    tc = policy["toolchain"]
    _require(text, "actions/checkout@" + tc["checkout_action_sha"], "checkout SHA pin")
    _require(text, "actions/setup-python@" + tc["setup_python_action_sha"], "setup-python SHA pin")
    if text.count("actions/checkout@" + tc["checkout_action_sha"]) != 2:
        raise DependencyControlError("both dependency jobs must use exact checkout pin")
    _require(text, 'python-version: "' + tc["python_version"] + '"', "exact Python version")
    _require(text, "persist-credentials: false", "disabled credential persistence")

    review = policy["dependency_review"]
    _require(text, review["action"] + "@" + review["commit"], "Dependency Review exact SHA")
    _require(text, "if: github.event_name == 'pull_request'", "PR-only dependency review")
    _require(text, "fail-on-severity: low", "low severity floor")
    _require(text, "fail-on-scopes: runtime,development,unknown", "all dependency scopes")
    _require(text, "vulnerability-check: true", "vulnerability check")
    _require(text, "license-check: false", "license check separation")
    _require(text, "comment-summary-in-pr: never", "no PR comments")
    _require(text, "warn-only: false", "fail-closed vulnerability gate")
    _require(text, "show-openssf-scorecard: false", "scorecard separation")

    _require(text, "python -m pip install --disable-pip-version-check -r requirements-dev.lock", "lock install")
    _require(
        text,
        "pip-audit -r requirements-dev.lock --no-deps --disable-pip --strict --progress-spinner off",
        "exact lock audit",
    )
    _require(text, 'cron: "23 4 * * 1"', "weekly audit")
    _require(text, "workflow_dispatch:", "manual audit")

    required_paths = [
        '"pyproject.toml"',
        '"requirements*.in"',
        '"requirements*.txt"',
        '"requirements*.lock"',
        '".github/workflows/security-dependencies.yml"',
        '"config/governance/dependency_control_policy_v1.json"',
    ]
    for item in required_paths:
        if text.count(item) < 2:
            raise DependencyControlError(f"dependency path filter missing from PR/push: {item}")


def main() -> int:
    try:
        policy = _json(POLICY_PATH)
        validate_policy(policy)
        validate_manifests(policy)
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        validate_workflow(policy, workflow)
    except (DependencyControlError, OSError, KeyError) as exc:
        print(f"DEPENDENCY_CONTROLS_INVALID: {exc}", file=sys.stderr)
        return 1
    print("DEPENDENCY_CONTROLS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
