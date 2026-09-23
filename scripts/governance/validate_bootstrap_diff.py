#!/usr/bin/env python3
"""Fail closed when the Git diff escapes the active Agent Work Unit scope."""

from __future__ import annotations

import fnmatch
import importlib.util
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


def changed_files(base: str) -> list[str]:
    result = _git("diff", "--name-only", f"{base}...HEAD")
    if result.returncode != 0:
        raise DiffScopeError(f"git diff failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


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
        files = changed_files(base)
        parent_allowed = evidence["parent_manifest"]["allowed_paths"]
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
        f"base={base} changed_files={len(files)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
