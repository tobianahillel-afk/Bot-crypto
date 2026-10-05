#!/usr/bin/env python3
"""Fail closed when the Git diff escapes the active Agent Work Unit scope."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class DiffScopeError(ValueError):
    pass


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise DiffScopeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=False, capture_output=True, text=True
    )


def _matches(path: str, patterns: list[str]) -> bool:
    return any(path == pattern or fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def resolve_scope_base(sha: str) -> str:
    if not isinstance(sha, str) or SHA40_RE.fullmatch(sha) is None:
        raise DiffScopeError("AWU scope_base_sha must be lowercase SHA-40")
    if _git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        raise DiffScopeError(f"AWU scope base does not resolve to a commit: {sha}")
    if _git("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
        raise DiffScopeError(f"AWU scope base is not an ancestor of HEAD: {sha}")
    return sha


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiffScopeError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DiffScopeError(f"{path} must contain an object")
    return value


def changed_files_between(base: str, head: str) -> list[str]:
    result = _git("diff", "--name-only", f"{base}...{head}")
    if result.returncode != 0:
        raise DiffScopeError(f"git diff failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(base: str) -> list[str]:
    return changed_files_between(base, "HEAD")


def first_commit_after(base: str) -> str:
    result = _git("rev-list", "--ancestry-path", "--reverse", f"{base}..HEAD")
    if result.returncode != 0:
        raise DiffScopeError(f"cannot resolve activation ancestry: {result.stderr.strip()}")
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not commits:
        raise DiffScopeError("BUSINESS route has no commit after activation predecessor")
    first = commits[0]
    parents = _git("rev-list", "--parents", "-n", "1", first)
    if parents.returncode != 0:
        raise DiffScopeError("cannot resolve activation commit parent")
    fields = parents.stdout.split()
    if len(fields) != 2 or fields[1] != base:
        raise DiffScopeError("activation transition must be one direct non-merge commit after predecessor")
    return first


ACTIVATION_REQUIRED_FILES = {
    "AGENTS.md",
    "README.md",
    "config/governance/project_state.json",
    "engineering/STATE.json",
    "engineering/lots/ENG-09.json",
    "engineering/handoff/CURRENT.json",
    "engineering/CONTEXT_MAP.json",
    "engineering/CONTEXT_MAP.md",
    "engineering/CURRENT_STATUS.md",
    "engineering/BUSINESS_DEVELOPMENT_UNLOCK_ACTIVATION.json",
    "engineering/work_units/ENG-09.6-WU05.json",
    "business/lots/LOT-45.json",
    "business/work_units/LOT-45.1-WU01.json",
}


def validate_activation_evidence(value: dict, base: str) -> None:
    if value.get("schema_version") != 1:
        raise DiffScopeError("activation evidence schema drift")
    if value.get("evidence_kind") != "business_development_unlock_activation_v1":
        raise DiffScopeError("activation evidence kind drift")
    if value.get("explicit_human_action") != "BUSINESS_DEVELOPMENT_UNLOCK":
        raise DiffScopeError("activation evidence lacks exact human authorization")
    if value.get("activation_predecessor_head") != base:
        raise DiffScopeError("activation evidence predecessor does not match BUSINESS scope base")
    if value.get("candidate_mutated") is not False or value.get("candidate_merged") is not False:
        raise DiffScopeError("activation evidence cannot claim candidate mutation or merge")
    if value.get("lot46_status") != "LOCKED":
        raise DiffScopeError("activation evidence must preserve Lot46 lock")


def validate_activation_transition_files(files: list[str]) -> None:
    missing = sorted(ACTIVATION_REQUIRED_FILES - set(files))
    if missing:
        raise DiffScopeError(f"activation transition missing required files: {missing}")


def resolve_business_effective_base(
    scope_base: str,
    activation_predecessor: str,
    activation_commit: str,
) -> str:
    if scope_base == activation_predecessor:
        return activation_commit
    if _git(
        "merge-base", "--is-ancestor", activation_commit, scope_base
    ).returncode != 0:
        raise DiffScopeError(
            "BUSINESS maintenance scope base must descend from the activation commit"
        )
    return scope_base


def validate_business_activation_bridge(
    base: str,
    scope: dict,
    parent_allowed: list[str],
) -> tuple[str, str, list[str]]:
    activation_path = ROOT / "engineering/BUSINESS_DEVELOPMENT_UNLOCK_ACTIVATION.json"
    if not activation_path.is_file():
        raise DiffScopeError("ACTIVE BUSINESS route requires activation evidence")
    activation = _load_json(activation_path)
    activation_predecessor = activation.get("activation_predecessor_head")
    if (
        not isinstance(activation_predecessor, str)
        or SHA40_RE.fullmatch(activation_predecessor) is None
    ):
        raise DiffScopeError("activation evidence predecessor is not a SHA-40")
    activation_predecessor = resolve_scope_base(activation_predecessor)
    validate_activation_evidence(activation, activation_predecessor)

    activation_commit = first_commit_after(activation_predecessor)
    transition_files = changed_files_between(activation_predecessor, activation_commit)
    validate_activation_transition_files(transition_files)

    wu05 = _load_json(ROOT / "engineering/work_units/ENG-09.6-WU05.json")
    eng09 = _load_json(ROOT / "engineering/lots/ENG-09.json")
    if wu05.get("status") != "DONE":
        raise DiffScopeError("activation transition requires ENG-09.6-WU05 DONE")
    validate_scope(
        transition_files,
        wu05["scope"]["allowed_paths"],
        wu05["scope"]["forbidden_paths"],
        eng09["allowed_paths"],
    )

    effective_base = resolve_business_effective_base(
        base, activation_predecessor, activation_commit
    )
    business_files = changed_files_between(effective_base, "HEAD")
    validate_scope(
        business_files,
        scope["allowed_paths"],
        scope["forbidden_paths"],
        parent_allowed,
    )
    return activation_commit, effective_base, business_files


def validate_scope(
    files: list[str],
    awu_allowed: list[str],
    awu_forbidden: list[str],
    parent_allowed: list[str],
) -> None:
    escaped_awu = sorted(path for path in files if not _matches(path, awu_allowed))
    if escaped_awu:
        raise DiffScopeError(f"changed files outside active AWU allowlist: {escaped_awu}")

    forbidden = sorted(path for path in files if _matches(path, awu_forbidden))
    if forbidden:
        raise DiffScopeError(f"changed files match active AWU forbidden paths: {forbidden}")

    escaped_parent = sorted(path for path in files if not _matches(path, parent_allowed))
    if escaped_parent:
        raise DiffScopeError(f"changed files outside parent work-item allowlist: {escaped_parent}")


def main() -> int:
    try:
        resolver = _module(
            "active_awu_resolver_for_diff",
            ROOT / "scripts/governance/resolve_active_awu.py",
        )
        try:
            awu_path, awu, evidence = resolver.resolve_active_awu()
        except resolver.ActiveAwuError as exc:
            raise DiffScopeError(str(exc)) from exc

        scope = awu["scope"]
        base = resolve_scope_base(scope["scope_base_sha"])
        parent_allowed = evidence["parent_manifest"]["allowed_paths"]
        if evidence.get("track") == "BUSINESS":
            activation_commit, effective_base, files = validate_business_activation_bridge(
                base, scope, parent_allowed
            )
        else:
            activation_commit = None
            effective_base = base
            files = changed_files(base)
            validate_scope(
                files,
                scope["allowed_paths"],
                scope["forbidden_paths"],
                parent_allowed,
            )
    except DiffScopeError as exc:
        print(f"ACTIVE_AWU_SCOPE_INVALID: {exc}", file=sys.stderr)
        return 1

    print(
        "ACTIVE_AWU_SCOPE_VALID "
        f"awu={awu['id']} path={awu_path.relative_to(ROOT)} "
        f"base={base} effective_base={effective_base} changed_files={len(files)}"
        + (f" activation_commit={activation_commit}" if activation_commit else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
