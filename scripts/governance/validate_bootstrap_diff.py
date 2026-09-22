#!/usr/bin/env python3
"""Fail closed if the engineering branch changes files outside the active work-item scope."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class DiffScopeError(ValueError):
    """Raised when the engineering diff escapes the active work-item allowlist."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiffScopeError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DiffScopeError(f"{path} must contain an object")
    return value


def _matches(path: str, patterns: list[str]) -> bool:
    return any(path == pattern or fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def changed_files(root: Path, base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DiffScopeError(f"git diff failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def validate_scope(files: list[str], allowed_paths: list[str]) -> None:
    escaped = sorted(path for path in files if not _matches(path, allowed_paths))
    if escaped:
        raise DiffScopeError(f"changed files outside active allowlist: {escaped}")


def _active_engine(state: dict[str, Any]) -> dict[str, Any]:
    bootstrap = state.get("bootstrap_engine", {})
    if bootstrap.get("phase") == "BUILDING":
        return bootstrap
    engineering = state.get("engineering_engine")
    if not isinstance(engineering, dict):
        raise DiffScopeError("STABLE bootstrap requires engineering_engine")
    return engineering


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    try:
        state = _load(root / "engineering" / "STATE.json")
        manifest_path = args.manifest
        if manifest_path is None:
            declared = _active_engine(state).get("active_manifest")
            if not isinstance(declared, str):
                raise DiffScopeError("active engine does not declare active_manifest")
            manifest_path = root / declared
        manifest = _load(manifest_path)
        allowed = manifest.get("allowed_paths")
        if not isinstance(allowed, list) or not allowed:
            raise DiffScopeError("active manifest allowed_paths is invalid")
        files = changed_files(root, args.base)
        validate_scope(files, allowed)
    except DiffScopeError as exc:
        print(f"BOOTSTRAP_DIFF_INVALID: {exc}", file=sys.stderr)
        return 1

    print(f"BOOTSTRAP_DIFF_VALID changed_files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
